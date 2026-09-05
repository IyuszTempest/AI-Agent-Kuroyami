WINDOWS_GATEWAY_SCHEMA = {
    "type": "function",
    "function": {
        "name": "windows_control_gateway",
        "description": "Kendalikan sistem operasi Windows (buka aplikasi, ngetik, hotkey/shortcut keyboard, screenshot, tutup aplikasi, open url, media control, power, system info, file search, window manage, get ip) hanya lewat 1 pintu.",
        "parameters": {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": [
                        "buka_app", 
                        "ketik", 
                        "hotkey", 
                        "screenshot", 
                        "tutup_app", 
                        "open_url", 
                        "media", 
                        "power", 
                        "sys_info", 
                        "file_search", 
                        "window_manage", 
                        "get_ip",
                        "volume_set", 
                        "empty_recycle_bin", 
                        "lock_screen",
                        "copy_clipboard", 
                        "write_clipboard", 
                        "list_running_apps",
                        "take_webcam", 
                        "open_path", 
                        "speech_say",
                        "vscode_read", 
                        "vscode_write", 
                        "vscode_list_dir",
                        "run_python_script", 
                        "extract_archive",
                        "gmail_read", 
                        "gdrive_search", 
                        "gdrive_upload", 
                        "g_tasks_add", 
                        "g_tasks_list",
                        "gdocs_create", 
                        "gslides_create", 
                        "youtube_search"
                    ],
                    "description": "Aksi yang ingin dilakukan pada Windows."
                },
                "target": {
                    "type": "string",
                    "description": "Nama aplikasi, teks untuk diketik, kombinasi shortcut, URL, atau parameter aksi."
                }
            },
            "required": ["action"]
        }
    }
}

ALL_SCHEMAS = [WINDOWS_GATEWAY_SCHEMA]