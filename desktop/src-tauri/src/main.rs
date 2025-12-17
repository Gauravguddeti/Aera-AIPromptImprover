// Prevents additional console window on Windows in release, DO NOT REMOVE!!
#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

use tauri::{command, State, Manager};
use serde::{Deserialize, Serialize};
use std::sync::Mutex;

#[derive(Debug, Serialize, Deserialize)]
struct AppState {
    backend_url: String,
    backend_running: bool,
}

impl Default for AppState {
    fn default() -> Self {
        Self {
            backend_url: "http://localhost:8000".to_string(),
            backend_running: false,
        }
    }
}

#[command]
async fn start_backend() -> Result<String, String> {
    // In a real implementation, this would start the Python backend
    // For now, we'll assume it's running separately
    Ok("Backend connection established".to_string())
}

#[command]
async fn stop_backend() -> Result<String, String> {
    // In a real implementation, this would stop the Python backend
    Ok("Backend stopped".to_string())
}

#[command]
async fn check_backend_status(state: State<'_, Mutex<AppState>>) -> Result<bool, String> {
    let app_state = state.lock().unwrap();
    // In a real implementation, this would ping the backend
    Ok(app_state.backend_running)
}

#[command]
async fn get_backend_url(state: State<'_, Mutex<AppState>>) -> Result<String, String> {
    let app_state = state.lock().unwrap();
    Ok(app_state.backend_url.clone())
}

#[command]
async fn set_backend_url(
    url: String,
    state: State<'_, Mutex<AppState>>
) -> Result<String, String> {
    let mut app_state = state.lock().unwrap();
    app_state.backend_url = url.clone();
    Ok(format!("Backend URL set to: {}", url))
}

fn main() {
    tauri::Builder::default()
        .manage(Mutex::new(AppState::default()))
        .invoke_handler(tauri::generate_handler![
            start_backend,
            stop_backend,
            check_backend_status,
            get_backend_url,
            set_backend_url
        ])
        .setup(|app| {
            // Optional: Auto-start backend here
            Ok(())
        })
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}