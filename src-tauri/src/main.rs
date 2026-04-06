#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

use std::{
    path::PathBuf,
    sync::Mutex,
    time::Duration,
};

use portpicker::pick_unused_port;
use serde::Serialize;
use tauri::{path::BaseDirectory, AppHandle, Manager, State};
use tauri_plugin_shell::{process::CommandChild, ShellExt};
use tokio::time::sleep;

struct BackendState {
    child: Mutex<Option<CommandChild>>,
    api_base_url: Mutex<Option<String>>,
}

#[derive(Serialize)]
#[serde(rename_all = "camelCase")]
struct RuntimeConfig {
    api_base_url: String,
}

#[tauri::command]
fn get_runtime_config(state: State<'_, BackendState>) -> Result<RuntimeConfig, String> {
    let api_base_url = state
        .api_base_url
        .lock()
        .map_err(|_| "Failed to read desktop runtime config".to_string())?
        .clone()
        .ok_or_else(|| "Backend is not ready".to_string())?;

    Ok(RuntimeConfig { api_base_url })
}

fn app_dir(app: &AppHandle) -> Result<PathBuf, String> {
    app.path()
        .resolve("data", BaseDirectory::AppData)
        .map_err(|err| err.to_string())
}

fn log_dir(app: &AppHandle) -> Result<PathBuf, String> {
    app.path()
        .resolve("logs", BaseDirectory::AppData)
        .map_err(|err| err.to_string())
}

async fn wait_for_backend(base_url: &str) -> Result<(), String> {
    let health_url = format!("{base_url}/health");
    let client = reqwest::Client::builder()
        .timeout(Duration::from_secs(2))
        .build()
        .map_err(|err| err.to_string())?;

    for _ in 0..40 {
        if let Ok(response) = client.get(&health_url).send().await {
            if response.status().is_success() {
                return Ok(());
            }
        }
        sleep(Duration::from_millis(250)).await;
    }

    Err(format!("Backend did not become ready at {health_url}"))
}

async fn spawn_backend(app: &AppHandle, state: &BackendState) -> Result<(), String> {
    let port = pick_unused_port().ok_or_else(|| "Unable to find a free localhost port".to_string())?;
    let api_base_url = format!("http://127.0.0.1:{port}/api");
    let data_dir = app_dir(app)?;
    let logs_dir = log_dir(app)?;

    std::fs::create_dir_all(&data_dir).map_err(|err| err.to_string())?;
    std::fs::create_dir_all(&logs_dir).map_err(|err| err.to_string())?;

    let sidecar_command = app
        .shell()
        .sidecar("backend-sidecar")
        .map_err(|err| err.to_string())?
        .env("TIMETABLING_APP_ENV", "desktop")
        .env("TIMETABLING_CORS_DEBUG_LOGGING", "true")
        .env("TIMETABLING_HOST", "127.0.0.1")
        .env("TIMETABLING_PORT", port.to_string())
        .env("TIMETABLING_CONFIG_DIR", data_dir.to_string_lossy().to_string())
        .env("TIMETABLING_LOG_DIR", logs_dir.to_string_lossy().to_string());

    let (mut rx, child) = sidecar_command.spawn().map_err(|err| err.to_string())?;

    tauri::async_runtime::spawn(async move {
        while let Some(event) = rx.recv().await {
            if let tauri_plugin_shell::process::CommandEvent::Stderr(line) = event {
                eprintln!("backend stderr: {}", String::from_utf8_lossy(&line));
            }
        }
    });

    {
        let mut child_slot = state.child.lock().map_err(|_| "Failed to store backend process".to_string())?;
        *child_slot = Some(child);
    }
    {
        let mut api_slot = state.api_base_url.lock().map_err(|_| "Failed to store backend url".to_string())?;
        *api_slot = Some(api_base_url.clone());
    }

    if let Err(err) = wait_for_backend(&api_base_url).await {
        shutdown_backend(state);
        if let Ok(mut api_slot) = state.api_base_url.lock() {
            *api_slot = None;
        }
        return Err(err);
    }

    Ok(())
}

fn shutdown_backend(state: &BackendState) {
    if let Ok(mut slot) = state.child.lock() {
        if let Some(child) = slot.take() {
            let _ = child.kill();
        }
    }

    if let Ok(mut api_slot) = state.api_base_url.lock() {
        *api_slot = None;
    }
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .plugin(tauri_plugin_shell::init())
        .manage(BackendState {
            child: Mutex::new(None),
            api_base_url: Mutex::new(None),
        })
        .invoke_handler(tauri::generate_handler![get_runtime_config])
        .setup(|app| {
            let handle = app.handle().clone();
            let state = app.state::<BackendState>();
            tauri::async_runtime::block_on(async move { spawn_backend(&handle, &state).await })?;
            Ok(())
        })
        .on_window_event(|window, event| {
            if let tauri::WindowEvent::CloseRequested { .. } = event {
                let state = window.state::<BackendState>();
                shutdown_backend(&state);
            }
        })
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}

fn main() {
    run();
}
