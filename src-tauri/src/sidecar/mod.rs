use serde::{Deserialize, Serialize};
use std::io::{BufRead, BufReader, Write};
use std::process::{Child, ChildStdin, ChildStdout, Command, Stdio};
use std::sync::{Arc, Mutex};

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
    #[serde(default, skip_serializing)]
    id: Option<u64>,
}

/// JSON-RPC error structure
#[derive(Debug, Deserialize)]
pub struct JsonRpcError {
    pub code: i32,
    pub message: String,
}

/// Persistent sidecar process manager
pub struct SidecarManager {
    child: Option<Child>,
    stdin: Option<ChildStdin>,
    stdout: Option<BufReader<ChildStdout>>,
    request_id: u64,
}

impl SidecarManager {
    /// Create a new sidecar manager
    pub fn new() -> Self {
        Self {
            child: None,
            stdin: None,
            stdout: None,
            request_id: 0,
        }
    }
    
    /// Start or restart the sidecar process
    pub fn start(&mut self) -> Result<(), String> {
        // Kill existing process if any
        self.stop()?;
        
        let sidecar_path = get_sidecar_path()?;
        
        #[cfg(windows)]
        let mut child = {
            use std::os::windows::process::CommandExt;
            const CREATE_NO_WINDOW: u32 = 0x08000000;
            Command::new(&sidecar_path)
                .creation_flags(CREATE_NO_WINDOW)
                .stdin(Stdio::piped())
                .stdout(Stdio::piped())
                .stderr(Stdio::piped())
                .spawn()
                .map_err(|e| format!("Failed to spawn sidecar '{}': {}", sidecar_path.display(), e))?
        };
        
        #[cfg(not(windows))]
        let mut child = Command::new(&sidecar_path)
            .stdin(Stdio::piped())
            .stdout(Stdio::piped())
            .stderr(Stdio::piped())
            .spawn()
            .map_err(|e| format!("Failed to spawn sidecar '{}': {}", sidecar_path.display(), e))?;
        
        let stdin = child.stdin.take().ok_or("Failed to get stdin")?;
        let stdout = child.stdout.take().ok_or("Failed to get stdout")?;
        let stdout = BufReader::new(stdout);
        
        self.child = Some(child);
        self.stdin = Some(stdin);
        self.stdout = Some(stdout);
        
        Ok(())
    }
    
    /// Stop the sidecar process
    pub fn stop(&mut self) -> Result<(), String> {
        if let Some(mut child) = self.child.take() {
            child.kill().ok();
            child.wait().ok();
        }
        self.stdin = None;
        self.stdout = None;
        Ok(())
    }
    
    /// Check if sidecar is running
    pub fn is_running(&mut self) -> bool {
        if let Some(ref mut child) = self.child {
            match child.try_wait() {
                Ok(Some(_)) => false, // Process has exited
                Ok(None) => true,      // Still running
                Err(_) => false,
            }
        } else {
            false
        }
    }
    
    /// Ensure sidecar is running
    fn ensure_running(&mut self) -> Result<(), String> {
        if !self.is_running() {
            self.start()?;
        }
        Ok(())
    }
    
    /// Call a method on the sidecar
    pub fn call(&mut self, method: &str, params: serde_json::Value) -> Result<serde_json::Value, String> {
        self.ensure_running()?;
        
        self.request_id += 1;
        let request = JsonRpcRequest {
            jsonrpc: "2.0".to_string(),
            method: method.to_string(),
            params,
            id: self.request_id,
        };
        
        let request_json = serde_json::to_string(&request)
            .map_err(|e| format!("Failed to serialize request: {}", e))?;
        
        // Send request
        if let Some(ref mut stdin) = self.stdin {
            writeln!(stdin, "{}", request_json)
                .map_err(|e| format!("Failed to write to stdin: {}", e))?;
            stdin.flush()
                .map_err(|e| format!("Failed to flush stdin: {}", e))?;
        } else {
            return Err("No stdin available".to_string());
        }
        
        // Read response
        let response = if let Some(ref mut stdout) = self.stdout {
            let mut line = String::new();
            stdout.read_line(&mut line)
                .map_err(|e| format!("Failed to read from stdout: {}", e))?;
            line
        } else {
            return Err("No stdout available".to_string());
        };
        
        // Parse response
        let rpc_response: JsonRpcResponse = serde_json::from_str(&response)
            .map_err(|e| format!("Failed to parse response '{}': {}", response.trim(), e))?;
        
        if let Some(error) = rpc_response.error {
            return Err(format!("JSON-RPC error {}: {}", error.code, error.message));
        }
        
        rpc_response.result.ok_or_else(|| "No result in response".to_string())
    }
}

impl Drop for SidecarManager {
    fn drop(&mut self) {
        self.stop().ok();
    }
}

/// Get the sidecar executable path
fn get_sidecar_path() -> Result<std::path::PathBuf, String> {
    let exe_dir = std::env::current_exe()
        .map_err(|e| format!("Failed to get exe path: {}", e))?;
    let exe_dir = exe_dir.parent().ok_or("Failed to get exe directory")?;
    
    let sidecar_name = if cfg!(windows) {
        "pdf-sidecar-x86_64-pc-windows-msvc.exe"
    } else {
        "pdf-sidecar-x86_64-unknown-linux-gnu"
    };
    
    // Try in the same directory
    let sidecar_path = exe_dir.join(sidecar_name);
    if sidecar_path.exists() {
        return Ok(sidecar_path);
    }
    
    // Try in binaries subdirectory
    let sidecar_path = exe_dir.join("binaries").join(sidecar_name);
    if sidecar_path.exists() {
        return Ok(sidecar_path);
    }
    
    // Try with .exe extension only (PyInstaller default name)
    #[cfg(windows)]
    {
        let sidecar_path = exe_dir.join("pdf-sidecar.exe");
        if sidecar_path.exists() {
            return Ok(sidecar_path);
        }
    }
    
    Err("Sidecar executable not found".to_string())
}

// Global sidecar manager singleton
lazy_static::lazy_static! {
    static ref SIDECAR_MANAGER: Arc<Mutex<SidecarManager>> = Arc::new(Mutex::new(SidecarManager::new()));
}

/// Call the Python sidecar (using persistent process)
pub fn call_sidecar(method: &str, params: serde_json::Value) -> Result<serde_json::Value, String> {
    let mut manager = SIDECAR_MANAGER.lock()
        .map_err(|_| "Failed to lock sidecar manager")?;
    
    manager.call(method, params)
}

/// Initialize sidecar on app startup
pub fn init_sidecar() -> Result<(), String> {
    let mut manager = SIDECAR_MANAGER.lock()
        .map_err(|_| "Failed to lock sidecar manager")?;
    manager.start()
}

/// Shutdown sidecar on app exit
pub fn shutdown_sidecar() -> Result<(), String> {
    let mut manager = SIDECAR_MANAGER.lock()
        .map_err(|_| "Failed to lock sidecar manager")?;
    manager.stop()
}
