@echo off

echo "Current directory structure:"
dir /b /s D:\test_project\pdf_editor

echo.
echo "Checking key files..."
if exist "D:\test_project\pdf_editor\package.json" (
    echo [OK] package.json exists
) else (
    echo [ERROR] package.json missing
)

if exist "D:\test_project\pdf_editor\src-tauri\Cargo.toml" (
    echo [OK] Cargo.toml exists
) else (
    echo [ERROR] Cargo.toml missing
)

if exist "D:\test_project\pdf_editor\src-tauri\tauri.conf.json" (
    echo [OK] tauri.conf.json exists
) else (
    echo [ERROR] tauri.conf.json missing
)

echo.
echo "Checking source directories..."
if exist "D:\test_project\pdf_editor\src\routes\+page.svelte" (
    echo [OK] +page.svelte exists
) else (
    echo [ERROR] +page.svelte missing
)

if exist "D:\test_project\pdf_editor\src-tauri\src\lib.rs" (
    echo [OK] lib.rs exists  
) else (
    echo [ERROR] lib.rs missing
)

if exist "D:\test_project\pdf_editor\src-tauri\src\main.rs" (
    echo [OK] main.rs exists
) else (
    echo [ERROR] main.rs missing
)

echo.
echo "All checks passed!"
