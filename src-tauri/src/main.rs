// Multimedia Downloader V4.0 — Tauri desktop shell.
//
// Design: one Python engine sidecar process PER operation. Write one JSON
// request line, stream its event lines back to the webview as "engine-event",
// finish on the terminal response. `stop_engine` kills the current child —
// cooperative cancellation for free. The engine emits i18n KEYS; the frontend
// translates them.
//
// Sidecar resolution (see `sidecar_program`):
//   * dev (debug):   `python ../engine_sidecar.py` (cwd is src-tauri/)
//   * packaged:      the bundled PyInstaller `engine_sidecar(.exe)` from the
//                    Tauri resource dir (no Python needed on the user's machine).

#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

use std::io::{BufRead, BufReader, Write};
use std::process::{Child, Command, Stdio};
use std::sync::Mutex;

use serde_json::{json, Value};
use tauri::path::BaseDirectory;
use tauri::{Emitter, Manager, State};

/// Tracks the sidecar child of the current streaming op so `stop_engine` can kill it.
#[derive(Default)]
struct Engine {
    child: Mutex<Option<Child>>,
}

/// Resolve how to launch the engine sidecar: (program, leading args).
fn sidecar_program(app: &tauri::AppHandle) -> Result<(std::path::PathBuf, Vec<String>), String> {
    if cfg!(debug_assertions) {
        // Dev: run the source script via PATH python. cwd is src-tauri/.
        Ok((std::path::PathBuf::from("python"), vec!["../engine_sidecar.py".to_string()]))
    } else {
        // Packaged: the PyInstaller onedir is bundled under resources/engine_sidecar/.
        let exe = if cfg!(windows) { "engine_sidecar/engine_sidecar.exe" } else { "engine_sidecar/engine_sidecar" };
        let path = app
            .path()
            .resolve(exe, BaseDirectory::Resource)
            .map_err(|e| format!("cannot resolve bundled sidecar: {e}"))?;
        Ok((path, vec![]))
    }
}

fn spawn_sidecar(app: &tauri::AppHandle, req: &Value) -> Result<Child, String> {
    let (program, args) = sidecar_program(app)?;
    let mut cmd = Command::new(program);
    cmd.args(args)
        .stdin(Stdio::piped())
        .stdout(Stdio::piped())
        .stderr(Stdio::null());
    // Windows: don't flash a console window on every per-operation spawn.
    #[cfg(windows)]
    {
        use std::os::windows::process::CommandExt;
        const CREATE_NO_WINDOW: u32 = 0x0800_0000;
        cmd.creation_flags(CREATE_NO_WINDOW);
    }
    let mut child = cmd
        .spawn()
        .map_err(|e| format!("failed to start sidecar: {e}"))?;
    let line = format!("{}\n", req);
    child
        .stdin
        .as_mut()
        .ok_or("no stdin")?
        .write_all(line.as_bytes())
        .map_err(|e| e.to_string())?;
    Ok(child)
}

/// One-shot request/response (no event stream): formats, locales, strings.
fn one_shot(app: &tauri::AppHandle, cmd: &str, args: Value) -> Result<Value, String> {
    let req = json!({ "id": cmd, "cmd": cmd, "args": args });
    let mut child = spawn_sidecar(app, &req)?;
    let stdout = child.stdout.take().ok_or("no stdout")?;
    for line in BufReader::new(stdout).lines() {
        let line = line.map_err(|e| e.to_string())?;
        let msg: Value = match serde_json::from_str(&line) {
            Ok(v) => v,
            Err(_) => continue,
        };
        if msg.get("type").is_some() {
            continue; // ignore stray events for one-shot calls
        }
        let _ = child.wait();
        if msg.get("ok").and_then(Value::as_bool).unwrap_or(false) {
            return Ok(msg.get("result").cloned().unwrap_or(Value::Null));
        }
        return Err(msg.get("error").and_then(Value::as_str).unwrap_or("error").into());
    }
    Err("sidecar closed without a response".into())
}

/// Streaming op: emit each event as "engine-event"; block until the response.
fn streaming(app: &tauri::AppHandle, engine: &Engine, cmd: &str, args: Value)
    -> Result<Value, String>
{
    let req = json!({ "id": cmd, "cmd": cmd, "args": args });
    let mut child = spawn_sidecar(app, &req)?;
    let stdout = child.stdout.take().ok_or("no stdout")?;
    // stash the child (minus stdout) so stop_engine can kill it
    *engine.child.lock().unwrap() = Some(child);

    let mut result = Value::Null;
    let mut err: Option<String> = None;
    for line in BufReader::new(stdout).lines() {
        let Ok(line) = line else { break };
        let Ok(msg) = serde_json::from_str::<Value>(&line) else { continue };
        if msg.get("type").is_some() {
            let _ = app.emit("engine-event", msg);
        } else if msg.get("id").is_some() {
            if msg.get("ok").and_then(Value::as_bool).unwrap_or(false) {
                result = msg.get("result").cloned().unwrap_or(Value::Null);
            } else {
                err = Some(msg.get("error").and_then(Value::as_str).unwrap_or("error").into());
            }
            break;
        }
    }
    if let Some(mut c) = engine.child.lock().unwrap().take() {
        let _ = c.wait();
    }
    match err {
        Some(e) => Err(e),
        None => Ok(result),
    }
}

#[tauri::command]
fn get_formats(app: tauri::AppHandle) -> Result<Value, String> {
    one_shot(&app, "formats", json!({}))
}

#[tauri::command]
fn get_locales(app: tauri::AppHandle) -> Result<Value, String> {
    // Frontend expects the {code: name} map directly.
    Ok(one_shot(&app, "locales", json!({}))?
        .get("available")
        .cloned()
        .unwrap_or(Value::Null))
}

#[tauri::command]
fn start_download(app: tauri::AppHandle, engine: State<Engine>, args: Value) -> Result<Value, String> {
    // Map the frontend DownloadArgs into the sidecar's {urls, options} shape.
    let options = json!({
        "save_path": args.get("save_path"),
        "mode": args.get("mode"),
        "video_fmt": args.get("video_fmt"),
        "audio_fmt": args.get("audio_fmt"),
        "quality": args.get("quality"),
        "browser": args.get("browser"),
    });
    streaming(&app, &engine, "download",
        json!({ "urls": args.get("urls"), "options": options }))
}

#[tauri::command]
fn start_convert(app: tauri::AppHandle, engine: State<Engine>, args: Value) -> Result<Value, String> {
    streaming(&app, &engine, "convert", json!({
        "files": args.get("files"),
        "dst_fmt": args.get("dst_fmt"),
        "save_path": args.get("save_path"),
    }))
}

#[tauri::command]
fn run_queue(app: tauri::AppHandle, engine: State<Engine>, args: Value) -> Result<Value, String> {
    streaming(&app, &engine, "run_queue", args)
}

#[tauri::command]
fn ai_plan(app: tauri::AppHandle, engine: State<Engine>, args: Value) -> Result<Value, String> {
    // args is already {api_key, prompt, context} — passes straight through to
    // the sidecar's ai_plan command. NEVER executes anything (see D4); the
    // frontend calls run_queue separately, only after the user confirms.
    streaming(&app, &engine, "ai_plan", args)
}

#[tauri::command]
fn stop_engine(engine: State<Engine>) -> Result<(), String> {
    if let Some(child) = engine.child.lock().unwrap().as_mut() {
        let _ = child.kill();
    }
    Ok(())
}

fn main() {
    tauri::Builder::default()
        .manage(Engine::default())
        .invoke_handler(tauri::generate_handler![
            get_formats,
            get_locales,
            start_download,
            start_convert,
            run_queue,
            ai_plan,
            stop_engine
        ])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
