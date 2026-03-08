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

/// Call the Python sidecar
pub fn call_sidecar(
    method: &str,
    params: serde_json::Value,
) -> Result<serde_json::Value, String> {
    // Get the project root
    let current_dir = std::env::current_dir()
        .map_err(|e| format!("Failed to get current directory: {}", e))?;
    
    // If we're in src-tauri, go to parent directory
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
    
    // Create JSON-RPC request
    let request = JsonRpcRequest {
        jsonrpc: "2.0".to_string(),
        method: method.to_string(),
        params,
        id: 1,
    };
    
    let request_json = serde_json::to_string(&request)
        .map_err(|e| format!("Failed to serialize request: {}", e))?;
    
    // Spawn Python process with UTF-8 encoding
    let mut child = Command::new("python")
        .arg("-u")  // Unbuffered output
        .arg(&script_path)
        .env("PYTHONIOENCODING", "utf-8")  // Force UTF-8 encoding
        .stdin(Stdio::piped())
        .stdout(Stdio::piped())
        .stderr(Stdio::piped())
        .spawn()
        .map_err(|e| format!("Failed to spawn Python: {}. Make sure Python is installed.", e))?;
    
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
        return Err(format!("Python failed ({}): {}", status, stderr_output));
    }
    
    // Parse response
    let rpc_response: JsonRpcResponse = serde_json::from_str(&response)
        .map_err(|e| format!("Failed to parse response '{}': {}", response.trim(), e))?;
    
    if let Some(error) = rpc_response.error {
        return Err(format!("JSON-RPC error {}: {}", error.code, error.message));
    }
    
    rpc_response.result.ok_or_else(|| "No result in response".to_string())
}
