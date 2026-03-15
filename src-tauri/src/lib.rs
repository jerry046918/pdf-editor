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

/// Batch split result for a single file
#[derive(serde::Deserialize, serde::Serialize)]
struct BatchSplitResult {
    file: String,
    success: bool,
    #[serde(skip_serializing_if = "Option::is_none")]
    output_files: Option<Vec<String>>,
    #[serde(skip_serializing_if = "Option::is_none")]
    error: Option<String>,
}

/// Batch split response
#[derive(serde::Deserialize, serde::Serialize)]
struct BatchSplitResponse {
    success: bool,
    #[serde(skip_serializing_if = "Option::is_none")]
    error: Option<String>,
    results: Vec<BatchSplitResult>,
    total_files: usize,
    success_count: usize,
    failed_count: usize,
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

/// Batch split multiple PDF files with the same settings
#[tauri::command]
fn pdf_batch_split(files: Vec<String>, output_dir: String, mode: String, options: serde_json::Value) -> Result<BatchSplitResponse, String> {
    let params = serde_json::json!({
        "files": files,
        "output_dir": output_dir,
        "mode": mode,
        "options": options,
    });
    
    let result = call_sidecar("pdf.batch_split", params)?;
    let response: BatchSplitResponse = serde_json::from_value(result)
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

/// Page preview response for specific page
#[derive(serde::Deserialize, serde::Serialize)]
struct PagePreviewResponse {
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
    page_width: Option<f32>,
    #[serde(skip_serializing_if = "Option::is_none")]
    page_height: Option<f32>,
}

/// Font settings for text
#[derive(serde::Deserialize, serde::Serialize, Clone)]
struct FontSettings {
    family: String,
    size: f32,
    color: String,
}

/// Text block for text editing
#[derive(serde::Deserialize, serde::Serialize)]
struct TextBlock {
    id: String,
    text: String,
    bbox: Vec<f32>,
    page: usize,
    #[serde(skip_serializing_if = "Option::is_none")]
    font: Option<FontSettings>,
}

/// Response for text blocks extraction
#[derive(serde::Deserialize, serde::Serialize)]
struct TextBlocksResponse {
    success: bool,
    #[serde(skip_serializing_if = "Option::is_none")]
    error: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    blocks: Option<Vec<TextBlock>>,
    #[serde(skip_serializing_if = "Option::is_none")]
    page_width: Option<f32>,
    #[serde(skip_serializing_if = "Option::is_none")]
    page_height: Option<f32>,
}

/// Text match for search
#[derive(serde::Deserialize, serde::Serialize)]
struct TextMatch {
    page: usize,
    text: String,
    bbox: (f32, f32, f32, f32),
    context: String,
}

/// Response for text search
#[derive(serde::Deserialize, serde::Serialize)]
struct TextSearchResponse {
    success: bool,
    #[serde(skip_serializing_if = "Option::is_none")]
    error: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    matches: Option<Vec<TextMatch>>,
    total_matches: Option<usize>,
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

/// Get preview for a specific page in a PDF file
#[tauri::command]
fn pdf_get_page_preview(file: String, page: usize, zoom: Option<f32>) -> Result<PagePreviewResponse, String> {
    let params = serde_json::json!({
        "file": file,
        "page": page,
        "zoom": zoom.unwrap_or(1.0),
    });

    let result = call_sidecar("pdf.get_page_preview", params)?;
    let response: PagePreviewResponse = serde_json::from_value(result)
        .map_err(|e| format!("Failed to parse response: {}", e))?;
    Ok(response)
}

/// Get text blocks from a specific page
#[tauri::command]
fn pdf_get_text_blocks(file: String, page: usize) -> Result<TextBlocksResponse, String> {
    let params = serde_json::json!({
        "file": file,
        "page": page,
    });

    let result = call_sidecar("pdf.get_text_blocks", params)?;
    let response: TextBlocksResponse = serde_json::from_value(result)
        .map_err(|e| format!("Failed to parse response: {}", e))?;
    Ok(response)
}

/// Search for text in a PDF
#[tauri::command]
fn pdf_search_text(file: String, search: String, case_sensitive: Option<bool>, pages: Option<Vec<usize>>) -> Result<TextSearchResponse, String> {
    let params = serde_json::json!({
        "file": file,
        "search": search,
        "case_sensitive": case_sensitive.unwrap_or(false),
        "pages": pages,
    });

    let result = call_sidecar("pdf.search_text", params)?;
    let response: TextSearchResponse = serde_json::from_value(result)
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
            pdf_batch_split,
            pdf_convert_images,
            pdf_edit_text,
            test_sidecar,
            pdf_get_thumbnails,
            pdf_get_file_preview,
            pdf_get_page_preview,
            pdf_get_text_blocks,
            pdf_search_text
        ])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
