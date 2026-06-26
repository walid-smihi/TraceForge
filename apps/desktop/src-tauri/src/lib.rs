use std::sync::Mutex;

use tauri::Manager;
use tauri_plugin_shell::process::CommandChild;
use tauri_plugin_shell::ShellExt;

// The static-exported frontend has the API URL baked in at build time, so
// the backend must listen on a fixed, known port rather than a dynamically
// chosen one.
const BACKEND_PORT: u16 = 47821;

struct SidecarState(Mutex<Option<CommandChild>>);

fn kill_sidecar(app: &tauri::AppHandle) {
    let state = app.state::<SidecarState>();
    let mut guard = state.0.lock().unwrap();
    if let Some(child) = guard.take() {
        let _ = child.kill();
    }
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .plugin(tauri_plugin_shell::init())
        .manage(SidecarState(Mutex::new(None)))
        .setup(|app| {
            if cfg!(debug_assertions) {
                app.handle().plugin(
                    tauri_plugin_log::Builder::default()
                        .level(log::LevelFilter::Info)
                        .build(),
                )?;
            }

            let app_data_dir = app.path().app_data_dir()?;
            std::fs::create_dir_all(&app_data_dir)?;
            let db_path = app_data_dir.join("traceforge.db");

            let (mut rx, child) = app
                .shell()
                .sidecar("traceforge-backend")?
                .env("PORT", BACKEND_PORT.to_string())
                .env("STORAGE_PATH", app_data_dir.to_string_lossy().to_string())
                .env(
                    "DATABASE_URL",
                    format!("sqlite+aiosqlite:///{}", db_path.to_string_lossy()),
                )
                .env(
                    "CORS_ORIGINS",
                    "tauri://localhost,https://tauri.localhost",
                )
                .spawn()?;

            tauri::async_runtime::spawn(async move {
                while let Some(event) = rx.recv().await {
                    match event {
                        tauri_plugin_shell::process::CommandEvent::Stdout(line) => {
                            log::info!("[backend] {}", String::from_utf8_lossy(&line));
                        }
                        tauri_plugin_shell::process::CommandEvent::Stderr(line) => {
                            log::info!("[backend] {}", String::from_utf8_lossy(&line));
                        }
                        _ => {}
                    }
                }
            });

            app.state::<SidecarState>().0.lock().unwrap().replace(child);

            let app_handle = app.handle().clone();
            if let Some(window) = app.get_webview_window("main") {
                window.on_window_event(move |event| {
                    if let tauri::WindowEvent::CloseRequested { .. } = event {
                        kill_sidecar(&app_handle);
                    }
                });
            }

            Ok(())
        })
        .build(tauri::generate_context!())
        .expect("error while building tauri application")
        .run(|app_handle, event| {
            // Belt-and-suspenders alongside the window CloseRequested handler
            // above — catches Cmd+Q / app.exit() paths that don't go through
            // a window close event.
            if let tauri::RunEvent::ExitRequested { .. } | tauri::RunEvent::Exit = event {
                kill_sidecar(app_handle);
            }
        });
}
