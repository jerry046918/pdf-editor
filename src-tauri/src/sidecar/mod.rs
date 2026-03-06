use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use std::io::{BufRead, BufWriter, Write};
use std::process::{ChildStderr, ChildStdin, ChildStdout, Command, Stdio};
use std::sync::{Arc, Mutex};
use tauri::Runtime;
use tauri_plugin_shell::ShellExt;

/// JSON-RPC request structure
#[derive(Debug, Serialize)]
pub struct JsonRpcRequest {
    jsonrpc: String,
    method: String,
    params: serde_json::Value,
    id: u64,
}

/// JSON-RPC response structure
#[derive(Debug, Deserialize)]
pub struct JsonRpcResponse<T> {
    pub jsonrpc: String,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub result: Option<T>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub error: Option<JsonRpcError>,
    pub id: u64,
}

/// JSON-RPC error structure
#[derive(Debug, Deserialize)]
pub struct JsonRpcError {
    pub code: i32,
    pub message: String,
}

/// PDF Sidecar client
pub struct PdfSidecar {
    stdin: Arc<Mutex<ChildStdin>>,
    request_id: Arc<Mutex<u64>>,
}

impl PdfSidecar {
    pub fn new<R: Runtime>(app: &tauri::AppHandle<R>) -> Result<Self, String> {
        let shell = app.shell();
        
        // Start the sidecar process
        let sidecar_command = Command::new_sidecar("pdf-sidecar")
            .map_err(|e| format!("Failed to create sidecar command: {}", e))?;
        
        let (mut rx, tx) = std::sync::mpsc::channel();
        
        let (mut reader, writer) = pipe()
            .map_err(|e| format!("Failed to create pipe: {}", e))?;
        
        // Spawn the sidecar process
        let output = shell
            .command(sidecar_command)
            .current_dir(std::env::current_dir().unwrap_or_default())
            .output()
            .map_err(|e| format!("Failed to spawn sidecar: {}", e))?;
        
        Ok(Self {
            stdin: Arc::new(Mutex::new(output.stdin)),
            request_id: Arc::new(Mutex::new(0)),
        })
    }
    
    /// Send a request to the sidecar and get response
    pub async fn call<T: for<'a> Deserialize<'a>>(
        &self,
        method: &str,
        params: serde_json::Value,
    ) -> Result<T, String> {
        let id = {
            let mut req_id = self.request_id.lock().unwrap();
            *req_id += 1;
            *req_id
        };
        
        let request = JsonRpcRequest {
            jsonrpc: "2.0".to_string(),
            method: method.to_string(),
            params,
            id,
        };
        
        // Send request
        let request_json = serde_json::to_string(&request)
            .map_err(|e| format!("Failed to serialize request: {}", e))?;
        
        {
            let mut stdin = self.stdin.lock().unwrap();
            writeln!(stdin, "{}", request_json)
                .map_err(|e| format!("Failed to write to sidecar: {}", e))?;
            stdin.flush()
                .map_err(|e| format!("Failed to flush sidecar stdin: {}", e))?;
        }
        
        // For now, return a placeholder
        // TODO: Implement response reading
        Err("Response reading not yet implemented".to_string())
    }
}
