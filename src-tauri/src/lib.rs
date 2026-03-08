mod sidecar;

use sidecar::call_sidecar;

// Learn more about Tauri commands at https://tauri.app/develop/calling-rust/

/// Generic PDF operation response
#[derive(serde::Deserialize, serde::Serialize)]
struct PdfResponse {
    success: bool,
    #[serde(skip_serializing_if = "Option::is_none")]
    error: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    output_path: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    page_count: Option<usize>,
    #[serde(skip_serializing_if = "Option::is_none")]
    files: Option<Vec<String>>,
    #[serde(skip_serializing_if = "Option::is_none")]
    total_files: Option<usize>,
}

/// Merge multiple PDF files into one
#[tauri::command]
fn pdf_merge(files: Vec<String>, output: String) -> Result<PdfResponse, String> {
    let params = serde_json::json!({
        "files": files,
        "output": output,
    });
    
    let result = call_sidecar("pdf.merge", params)?;
    let response: PdfResponse = serde_json::from_value(result)
        .map_err(|e| format!("Failed to parse response: {}", e))?;
    Ok(response)
}

/// Split a PDF file into multiple files
#[tauri::command]
fn pdf_split(file: String, output_dir: String, mode: String, options: serde_json::Value) -> Result<PdfResponse, String> {
    let params = serde_json::json!({
        "file": file,
        "output_dir": output_dir,
        "mode": mode,
        "options": options,
    });
    
    let result = call_sidecar("pdf.split", params)?;
    let response: PdfResponse = serde_json::from_value(result)
        .map_err(|e| format!("Failed to parse response: {}", e))?;
    Ok(response)
}

/// Convert images to PDF
#[tauri::command]
fn pdf_convert_images(images: Vec<String>, output: String, options: Option<serde_json::Value>) -> Result<PdfResponse, String> {
    let params = serde_json::json!({
        "images": images,
        "output": output,
        "options": options.unwrap_or(serde_json::json!({})),
    });
    
    let result = call_sidecar("pdf.convert_images", params)?;
    let response: PdfResponse = serde_json::from_value(result)
        .map_err(|e| format!("Failed to parse response: {}", e))?;
    Ok(response)
}

/// Edit text in a PDF
#[tauri::command]
fn pdf_edit_text(file: String, output: String, operations: Vec<serde_json::Value>) -> Result<PdfResponse, String> {
    let params = serde_json::json!({
        "file": file,
        "output": output,
        "operations": operations,
    });
    
    let result = call_sidecar("pdf.edit_text", params)?;
    let response: PdfResponse = serde_json::from_value(result)
        .map_err(|e| format!("Failed to parse response: {}", e))?;
    Ok(response)
}

/// Test connection to Python sidecar
#[tauri::command]
fn test_sidecar() -> Result<String, String> {
    #[derive(serde::Deserialize)]
    struct PingResponse {
        status: String,
        message: String,
    }
    
    let result = call_sidecar("system.ping", serde_json::json!({}))?;
    let ping: PingResponse = serde_json::from_value(result)
        .map_err(|e| format!("Failed to parse ping response: {}", e))?;
    Ok(format!("{}: {}", ping.status, ping.message))
}

/// Thumbnail response for a single page
#[derive(serde::Deserialize, serde::Serialize)]
struct Thumbnail {
    page: usize,
    image: String,
    width: usize,
    height: usize,
}

/// Thumbnails response
#[derive(serde::Deserialize, serde::Serialize)]
struct ThumbnailsResponse {
    success: bool,
    #[serde(skip_serializing_if = "Option::is_none")]
    error: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    thumbnails: Option<Vec<Thumbnail>>,
    #[serde(skip_serializing_if = "Option::is_none")]
    page_count: Option<usize>,
}

/// File preview response
#[derive(serde::Deserialize, serde::Serialize)]
struct FilePreviewResponse {
    success: bool,
    #[serde(skip_serializing_if = "Option::is_none")]
    error: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    image: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    width: Option<usize>,
    #[serde(skip_serializing_if = "Option::is_none")]
    height: Option<usize>,
    #[serde(skip_serializing_if = "Option::is_none")]
    page_count: Option<usize>,
    #[serde(skip_serializing_if = "Option::is_none")]
    title: Option<String>,
}

/// Get thumbnails for all pages in a PDF file
#[tauri::command]
fn pdf_get_thumbnails(file: String, max_pages: Option<usize>, zoom: Option<f32>) -> Result<ThumbnailsResponse, String> {
    let params = serde_json::json!({
        "file": file,
        "max_pages": max_pages.unwrap_or(50),
        "zoom": zoom.unwrap_or(0.3),
    });
    
    let result = call_sidecar("pdf.get_thumbnails", params)?;
    let response: ThumbnailsResponse = serde_json::from_value(result)
        .map_err(|e| format!("Failed to parse response: {}", e))?;
    Ok(response)
}

/// Get preview for a PDF file (first page)
#[tauri::command]
fn pdf_get_file_preview(file: String, zoom: Option<f32>) -> Result<FilePreviewResponse, String> {
    let params = serde_json::json!({
        "file": file,
        "zoom": zoom.unwrap_or(0.5),
    });
    
    let result = call_sidecar("pdf.get_file_preview", params)?;
    let response: FilePreviewResponse = serde_json::from_value(result)
        .map_err(|e| format!("Failed to parse response: {}", e))?;
    Ok(response)
}

#[tauri::command]
fn greet(name: &str) -> String {
    format!("Hello, {}! Welcome to PDF Editor!", name)
}

pub fn run() {
    tauri::Builder::default()
        .plugin(tauri_plugin_dialog::init())
        .plugin(tauri_plugin_fs::init())
        .plugin(tauri_plugin_shell::init())
        .invoke_handler(tauri::generate_handler![
            greet,
            pdf_merge,
            pdf_split,
            pdf_convert_images,
            pdf_edit_text,
            test_sidecar,
            pdf_get_thumbnails,
            pdf_get_file_preview
        ])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
