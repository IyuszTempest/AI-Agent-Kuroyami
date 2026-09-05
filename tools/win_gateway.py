import os
import subprocess
import pyautogui
import psutil
import socket
import glob
import zipfile
import cv2
import pyperclip
from tools.google_manager import handle_google_ecosystem

pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.4

def windows_control_gateway(action: str, target: str = "") -> str:
    action = action.lower().strip()
    target = target.strip()
    
    try:
        # --- ROUTER EKOSISTEM GOOGLE ---
        elif_actions = [
            "gmail_read", "gdrive_search", "gdrive_upload", 
            "g_tasks_add", "g_tasks_list", "gdocs_create", 
            "gslides_create", "youtube_search"
        ]
        if action in elif_actions:
            return handle_google_ecosystem(action, target)

        # --- APLIKASI & SISTEM DASAR ---
        elif action == "buka_app":
            os.system(f"start {target}")
            return f"Berhasil membuka aplikasi: {target}"
            
        elif action == "ketik":
            pyautogui.write(target, interval=0.03)
            return f"Berhasil mengetik: '{target}'"
            
        elif action == "hotkey":
            keys = [k.strip() for k in target.split('+')]
            pyautogui.hotkey(*keys)
            return f"Berhasil hotkey: {target}"
            
        elif action == "screenshot":
            os.makedirs("tmp", exist_ok=True)
            path = "tmp/windows_screen.png"
            pyautogui.screenshot().save(path)
            return f"Screenshot disimpan di {path}"
            
        elif action == "tutup_app":
            os.system(f"taskkill /f /im {target}.exe")
            return f"Berhasil menutup proses: {target}"

        elif action == "open_url":
            os.system(f"start {target}")
            return f"Berhasil membuka URL di browser: {target}"
            
        elif action == "media":
            if target == "mute":
                pyautogui.press('volumemute')
            elif target in ["vol_up", "up"]:
                pyautogui.press('volumeup')
            elif target in ["vol_down", "down"]:
                pyautogui.press('volumedown')
            elif target in ["play", "pause"]:
                pyautogui.press('playpause')
            return f"Berhasil menjalankan perintah media: {target}"
            
        elif action == "power":
            if target == "shutdown":
                os.system("shutdown /s /t 15")
                return "PC akan dimatikan dalam 15 detik!"
            elif target == "restart":
                os.system("shutdown /r /t 15")
                return "PC akan direstart dalam 15 detik!"
            elif target == "sleep":
                os.system("rundll32.exe powrprof.dll,SetSuspendState 0,1,0")
                return "Memasukkan PC ke mode sleep..."
                
        elif action == "sys_info":
            cpu_usage = psutil.cpu_percent(interval=1)
            ram_usage = psutil.virtual_memory().percent
            return f"Status Sistem Saat Ini -> CPU: {cpu_usage}%, RAM Terpakai: {ram_usage}%"

        elif action == "file_search":
            import glob
            found = glob.glob(f"C:/**/*{target}*", recursive=True)[:5]
            return f"File ditemukan: {found}" if found else "File tidak ditemukan."

        elif action == "window_manage":
            if target == "minimize":
                pyautogui.hotkey('win', 'down')
            elif target == "maximize":
                pyautogui.hotkey('win', 'up')
            elif target == "close":
                pyautogui.hotkey('alt', 'f4')
            return f"Window management executed: {target}"

        elif action == "get_ip":
            import socket
            hostname = socket.gethostname()
            local_ip = socket.gethostbyname(hostname)
            return f"Hostname: {hostname}, Local IP: {local_ip}"

        elif action == "volume_set":
            try:
                level = int(target)
                return f"Volume diatur ke {level}%"
            except:
                return "Format volume harus angka (0-100)"

        elif action == "empty_recycle_bin":
            os.system("PowerShell.cmd -Command \"Clear-RecycleBin -Force -ErrorAction SilentlyContinue\"")
            return "Recycle Bin berhasil dikosongkan."

        elif action == "lock_screen":
            import ctypes
            ctypes.windll.user32.LockWorkStation()
            return "Layar berhasil dikunci, Yus!"
        

        elif action == "copy_clipboard":
            # Mengambil teks yang sedang disalin di clipboard
            import pyperclip
            content = pyperclip.paste()
            return f"Isi Clipboard: {content}" if content else "Clipboard kosong."

        elif action == "write_clipboard":
            # Memasukkan teks langsung ke clipboard untuk siap dipaste
            import pyperclip
            pyperclip.copy(target)
            return f"Berhasil menyalin teks ke clipboard: '{target}'"

        elif action == "list_running_apps":
            # Mendapatkan daftar aplikasi/proses yang sedang berjalan di sistem
            import subprocess
            result = subprocess.run(["powershell", "-Command", "Get-Process | Where-Object {$_.MainWindowTitle -ne ''} | Select-Object -ExpandProperty Name"], capture_output=True, text=True)
            apps = [line.strip() for line in result.stdout.splitlines() if line.strip()]
            return f"Aplikasi aktif: {', '.join(apps[:10])}"

        elif action == "take_webcam":
            # Mengambil foto kilat dari webcam PC
            import cv2
            cam = cv2.VideoCapture(0)
            ret, frame = cam.read()
            if ret:
                path = "tmp/webcam_snapshot.jpg"
                cv2.imwrite(path, frame)
                cam.release()
                return f"Foto webcam berhasil diambil dan disimpan di {path}"
            cam.release()
            return "Gagal mengakses webcam."

        elif action == "open_path":
            # Membuka folder spesifik di Windows Explorer (contoh target: 'C:\Users\Downloads')
            os.system(f"explorer \"{target}\"")
            return f"Berhasil membuka folder: {target}"

        elif action == "speech_say":
            # Membuat PC bersuara / Text-to-Speech lokal menggunakan PowerShell SAPI
            import subprocess
            cmd = f"Add-Type -AssemblyName System.Speech; (New-Object System.Speech.Synthesis.SpeechSynthesizer).Speak('{target}');"
            subprocess.run(["powershell", "-Command", cmd])
            return f"PC berhasil membacakan teks: '{target}'"

        elif action == "vscode_read":
            # Membaca isi file project di VS Code (target: path file, misal 'main.py')
            try:
                with open(target, 'r', encoding='utf-8') as f:
                    content = f.read()
                return f"Isi file {target}:\n{content}"
            except Exception as e:
                return f"Gagal membaca file: {str(e)}"

        elif action == "vscode_write":
            # Menulis atau mengedit isi file project (target: path|isi_teks atau pisah dengan delimiter)
            try:
                parts = target.split('|', 1)
                file_path = parts[0].strip()
                new_content = parts[1] if len(parts) > 1 else ""
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                return f"Berhasil menyimpan perubahan pada file: {file_path}"
            except Exception as e:
                return f"Gagal menulis file: {str(e)}"

        elif action == "vscode_list_dir":
            # Melihat daftar file/folder di direktori workspace
            import os
            path = target if target else "."
            items = os.listdir(path)
            return f"Daftar file di {path}: {', '.join(items)}"

        elif action == "run_python_script":
            # Menjalankan script Python kecil secara langsung dan mengembalikan output-nya
            import subprocess
            result = subprocess.run(["python", "-c", target], capture_output=True, text=True, timeout=10)
            output = result.stdout if result.stdout else result.stderr
            return f"Output eksekusi Python:\n{output}"

        elif action == "extract_archive":
            # Mengekstrak file arsip (ZIP) untuk kebutuhan tugas/materi
            import zipfile
            parts = target.split('|', 1)
            zip_path = parts[0].strip()
            dest_path = parts[1].strip() if len(parts) > 1 else "."
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(dest_path)
            return f"Berhasil mengekstrak {zip_path} ke {dest_path}"

        else:
            return f"Aksi '{action}' tidak dikenali sistem."
            
    except Exception as e:
        return f"Gagal mengeksekusi aksi: {str(e)}"