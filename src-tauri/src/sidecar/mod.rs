use serde::{Deserialize, Serialize};
use std::io::{BufRead, BufReader, Read, Write};
use std::process::{Command, Stdio};

/// JSON-RPC request structure
#[derive(Debug, Serialize)]
struct JsonRpcRequest {
    jsonrpc: String,
    method: String,
    params: serde_json::Value,
    id: u64,
}

/// JSON-RPC response structure
#[derive(Debug, Deserialize)]
struct JsonRpcResponse {
    #[serde(default)]
    result: Option<serde_json::Value>,
    #[serde(default)]
    error: Option<JsonRpcError>,
    #[serde(default)]
    id: Option<u64>,
}

/// JSON-RPC error structure
#[derive(Debug, Deserialize)]
pub struct JsonRpcError {
    pub code: i32,
    pub message: String,
}

/// Get the sidecar executable path
fn get_sidecar_path() -> Result<std::path::PathBuf, String> {
    // In production, use the bundled sidecar
    #[cfg(not(debug_assertions))]
    {
        // Get the exe directory
        let exe_dir = std::env::current_exe()
            .map_err(|e| format!("Failed to get exe path: {}", e))?;
        let exe_dir = exe_dir.parent().ok_or("Failed to get exe directory")?;
        
        // Look for sidecar in the same directory
        let sidecar_name = if cfg!(windows) {
            "pdf-sidecar-x86_64-pc-windows-msvc.exe"
        } else {
            "pdf-sidecar-x86_64-unknown-linux-gnu"
        };
        
        let sidecar_path = exe_dir.join(sidecar_name);
        
        if sidecar_path.exists() {
            return Ok(sidecar_path);
        }
        
        // Fallback: look in binaries subdirectory
        let sidecar_path = exe_dir.join("binaries").join(sidecar_name);
        if sidecar_path.exists() {
            return Ok(sidecar_path);
        }
    }
    
    // In development, return None to use Python directly
    Err("Sidecar not found, using Python".to_string())
}

/// Call the Python sidecar
pub fn call_sidecar(
    method: &str,
    params: serde_json::Value,
) -> Result<serde_json::Value, String> {
    // Create JSON-RPC request
    let request = JsonRpcRequest {
        jsonrpc: "2.0".to_string(),
        method: method.to_string(),
        params,
        id: 1,
    };
    
    let request_json = serde_json::to_string(&request)
        .map_err(|e| format!("Failed to serialize request: {}", e))?;
    
    // Try to use bundled sidecar first (production)
    let mut child = if let Ok(sidecar_path) = get_sidecar_path() {
        Command::new(&sidecar_path)
            .stdin(Stdio::piped())
            .stdout(Stdio::piped())
            .stderr(Stdio::piped())
            .spawn()
            .map_err(|e| format!("Failed to spawn sidecar '{}': {}", sidecar_path.display(), e))?
    } else {
        // Development mode: use Python directly
        let current_dir = std::env::current_dir()
            .map_err(|e| format!("Failed to get current directory: {}", e))?;
        
        let project_root = if current_dir.file_name().map(|n| n == "src-tauri").unwrap_or(false) {
            current_dir.parent().unwrap_or(&current_dir).to_path_buf()
        } else {
            current_dir.clone()
        };
        
        let script_path = project_root
            .join("pdf-sidecar")
            .join("src")
            .join("__main__.py")
            .to_string_lossy()
            .to_string();
        
        Command::new("python")
            .arg("-u")
            .arg(&script_path)
            .env("PYTHONIOENCODING", "utf-8")
            .stdin(Stdio::piped())
            .stdout(Stdio::piped())
            .stderr(Stdio::piped())
            .spawn()
            .map_err(|e| format!("Failed to spawn Python: {}. Make sure Python is installed.", e))?
    };
    
    // Send request via stdin
    if let Some(mut stdin) = child.stdin.take() {
        writeln!(stdin, "{}", request_json)
            .map_err(|e| format!("Failed to write to stdin: {}", e))?;
        stdin.flush()
            .map_err(|e| format!("Failed to flush stdin: {}", e))?;
    } else {
        return Err("Failed to get stdin".to_string());
    }
    
    // Read response from stdout
    let response = if let Some(stdout) = child.stdout.take() {
        let mut reader = BufReader::new(stdout);
        let mut line = String::new();
        reader.read_line(&mut line)
            .map_err(|e| format!("Failed to read from stdout: {}", e))?;
        line
    } else {
        return Err("Failed to get stdout".to_string());
    };
    
    // Read stderr for debugging
    let stderr_output = if let Some(mut stderr) = child.stderr.take() {
        let mut error_output = String::new();
        Read::read_to_string(&mut stderr, &mut error_output).ok();
        error_output
    } else {
        String::new()
    };
    
    // Wait for process
    let status = child.wait()
        .map_err(|e| format!("Failed to wait for process: {}", e))?;
    
    if !status.success() {
        return Err(format!("Sidecar failed ({}): {}", status, stderr_output));
    }
    
    // Parse response
    let rpc_response: JsonRpcResponse = serde_json::from_str(&response)
        .map_err(|e| format!("Failed to parse response '{}': {}", response.trim(), e))?;
    
    if let Some(error) = rpc_response.error {
        return Err(format!("JSON-RPC error {}: {}", error.code, error.message));
    }
    
    rpc_response.result.ok_or_else(|| "No result in response".to_string())
}
