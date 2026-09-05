import json
import io
import os
import re
import subprocess
import uuid
import threading
import edge_tts
import asyncio
import soundfile as sf
import time
import requests
import numpy as np
import scipy.io.wavfile as wav
import sounddevice as sd
from docx import Document
from pypdf import PdfReader
from tools.win_schema import ALL_SCHEMAS
from tools.win_gateway import windows_control_gateway
import webview
from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request
from config import SYSTEM_PROMPT, client as groq_client, openrouter_client

load_dotenv_status = load_dotenv()

ALL_TOOLS = {
    "windows_control_gateway": windows_control_gateway
}

SETTINGS_FILE = 'settings.json'

TEMP_DIR = "tmp"
os.makedirs(TEMP_DIR, exist_ok=True)

IS_KURO_SPEAKING = False  
HISTORY_FILE = "chat_history.json"
MEMORY_FILE = "user_memory.json"


# "id-ID-GadisNeural"  -> Indonesia
# "ja-JP-NanamiNeural" -> Jepang 
VOICE_NAME = "id-ID-GadisNeural"
VOICE_RATE = "+14%"  # Kecepatan bicara (contoh: +5%, +10%, -5%)
VOICE_PITCH = "+25Hz" # Nada suara/imut (contoh: +10Hz, +15Hz, -5Hz)


app_state = {
    "active_model": "Kuroyami 1.0",
    "voice_enabled": True,
    "dark_mode": False,
    "text": "Halo! Kuroyami udah siap nih...",
    "expression": "normal",
    "is_speaking": False
}


def load_chat_history():
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []
    else:
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump([], f, indent=4)
        return []
conversation_history = load_chat_history()

def save_chat_history(history):
    MAX_HISTORY_LEN = 12  
    if len(history) > MAX_HISTORY_LEN:
        history = [history[0]] + history[-(MAX_HISTORY_LEN - 1):]
    with open("chat_history.json", "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=4)


def load_user_memory():
    if os.path.exists(MEMORY_FILE):
        try:
            with open(MEMORY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    else:
        default_memory = {
            "nama": "Yus",
            "fakta_penting": [
                "Kuliah di jurusan Sistem Informasi",
                "Suka anime dan hal berbau Jepang",
                "Suka ngoding bot WhatsApp dan custom script pakai JavaScript/Python"
            ]
        }
        with open(MEMORY_FILE, "w", encoding="utf-8") as f:
            json.dump(default_memory, f, indent=4, ensure_ascii=False)
        return default_memory
user_profile = load_user_memory()


def load_settings_data():
    if os.path.exists(SETTINGS_FILE):
        with open(SETTINGS_FILE, 'r') as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                pass
    return {"tema_gelap": False}


def clean_text_for_tts_and_ui(text):
    if not text:
        return ""
    text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)
    text = re.sub(r'\*(.*?)\*', r'\1', text)
    text = re.sub(r'^\s*[-*]\s+', '', text, flags=re.MULTILINE)
    emoji_pattern = re.compile(r'[\U00010000-\U0010ffff\u2600-\u27bf\U0001f300-\U0001f6ff]', flags=re.UNICODE)
    text = emoji_pattern.sub(r'', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def get_edge_tts_audio(text: str) -> bytes | None:
    """Generate audio gratis dengan penyesuaian Pitch & Rate"""
    try:
        async def _generate():
            communicate = edge_tts.Communicate(
                text=text,
                voice=VOICE_NAME,
                rate=VOICE_RATE,
                pitch=VOICE_PITCH
            )
            audio_data = b""
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    audio_data += chunk["data"]
            return audio_data

        return asyncio.run(_generate())
    except Exception as e:
        print(f"⚠️ [Edge-TTS] Error: {e}")
        return None


def kuro_speak_natural(text: str, max_chars: int = 300):
    global IS_KURO_SPEAKING

    if not app_state.get("voice_enabled", True) or not text.strip():
        return

    try:
        clean_text = re.sub(r"```[\s\S]*?```", " [Kode program terlampir] ", text)
        clean_text = re.sub(r"[^\w\s.,?!zZà-ÿĀ-žА-я0-9\-\(\)]", "", clean_text)
        clean_text = re.sub(r"\s+", " ", clean_text).strip()

        if len(clean_text) > max_chars:
            truncated_text = clean_text[:max_chars]
            last_punct = max(truncated_text.rfind('.'), truncated_text.rfind('?'), truncated_text.rfind('!'))
            
            if last_punct > 50: 
                clean_text = truncated_text[:last_punct + 1] + " Penjelasan lengkapnya sudah Kuro tampilkan di layar ya, Yus."
            else:
                clean_text = truncated_text + "... Penjelasan lengkapnya sudah Kuro tampilkan di layar ya, Yus."

        if not clean_text:
            clean_text = "Baik, saya mengerti."

        IS_KURO_SPEAKING = True

        print(f"🎙️ [Edge-TTS] Generating audio ({VOICE_NAME} | Length: {len(clean_text)} chars)...")
        audio_bytes = get_edge_tts_audio(clean_text)

        if audio_bytes:
            print("🔊 [Kuro] Memutar suara...")
            data, fs = sf.read(io.BytesIO(audio_bytes))
            sd.play(data, fs)
            sd.wait()
        else:
            print("⚠️ [Kuro TTS] Gagal memutar suara.")

    except Exception as e:
        print(f"⚠️ Gagal memutar suara: {e}")
    finally:
        IS_KURO_SPEAKING = False


def kuro_speak_anime(text: str):
    print("🔊 [Kuro sedang ngomong...]")
    try:
        kuro_speak_natural(text)
    except Exception as e:
        print(f"⚠️ Gagal memutar suara anime: {e}")

def trim_history(history, max_messages=4):
    if len(history) <= max_messages:
        return history
    return [history[0]] + history[-max_messages:]


def sanitize_tool_name(name: str) -> str:
    return re.sub(r'<\|.*?\|>.*', '', name).strip()


def clean_messages_for_api(messages):
    valid_roles = {"system", "user", "assistant", "tool"}
    cleaned = []
    for msg in messages:
        if not isinstance(msg, dict):
            continue
        m = dict(msg)
        if m.get("role") not in valid_roles:
            m["role"] = "assistant"
        cleaned.append(m)
    return cleaned

DYNAMIC_SYSTEM_PROMPT = f"""
Kamu adalah Kuro, asisten AI pribadi milik {user_profile.get('nama', 'Yus')}.
Fakta pengguna:
- {user_profile.get('fakta_penting', [])}
"""

LEARNING_SYSTEM_PROMPT = f"""
{DYNAMIC_SYSTEM_PROMPT}
[MODE KURO LEARNING 1.5]: Kamu adalah tutor akademik pribadi Yus yang sabar, asik, dan gaul ala wibu cerdas. Fokusmu adalah membimbing Yus memahami materi kuliah Sistem Informasi, menjelaskan konsep rumit dengan analogi sederhana, serta membantu merangkum teori. Kamu juga memiliki akses penuh untuk mengeksekusi perintah/tools sistem komputer Yus jika diminta.
"""

PRO_SYSTEM_PROMPT = f"""
{DYNAMIC_SYSTEM_PROMPT}
[MODE KURO PRO 2.0]: Kamu adalah Kuro Pro 2.0, asisten AI elite yang sangat ahli dalam arsitektur perangkat lunak, pemrograman tingkat lanjut (JavaScript, Node.js, Python), dan eksekusi project kompleks. Berikan solusi teknis yang akurat dan bersih dengan gaya wibu asik. Kamu memiliki akses penuh untuk mengeksekusi perintah/tools sistem komputer Yus jika diminta.
"""

def chat_agent(user_input: str, file=None):
    global conversation_history
    if file:
        import base64
        file_bytes = file.read()
        encoded_image = base64.b64encode(file_bytes).decode('utf-8')
        mime_type = file.mimetype or 'image/png'
        
        user_content = [
            {"type": "text", "text": user_input if user_input else "Tolong perhatikan file ini."},
            {
                "type": "image_url",
                "image_url": {
                    "url": f"data:{mime_type};base64,{encoded_image}"
                }
            }
        ]
        conversation_history.append({"role": "user", "content": user_content})
    else:
        conversation_history.append({"role": "user", "content": user_input})
    
    current_model_mode = app_state.get("active_model", "Kuroyami 1.0")

    if current_model_mode == "Kuro Pro 2.0":
        client_to_use = openrouter_client
        active_models = ["poolside/laguna-s-2.1:free", "nvidia/nemotron-3.5-lightning:free"]
        active_system_prompt = PRO_SYSTEM_PROMPT
        active_tools = ALL_SCHEMAS if ALL_SCHEMAS else None
        tool_choice_setting = "auto"
    elif current_model_mode == "Kuro Learning 1.5":
        client_to_use = groq_client
        active_models = ["openai/gpt-oss-120b", "openai/gpt-oss-20b", "llama-3.3-70b-versatile"]
        active_system_prompt = LEARNING_SYSTEM_PROMPT + "\n[INSTRUKSI KULIAH]: Bantu Yus menganalisis file, materi kuliah, dan cari informasi realtime jika diperlukan."
        active_tools = ALL_SCHEMAS if ALL_SCHEMAS else None  
        tool_choice_setting = "auto"                    
    else:
        # --- KUROYAMI 1.0 ---
        client_to_use = groq_client
        active_models = ["qwen/qwen3.6-27b", "openai/gpt-oss-20b"]
        active_system_prompt = DYNAMIC_SYSTEM_PROMPT
        active_tools = ALL_SCHEMAS if ALL_SCHEMAS else None
        tool_choice_setting = "auto"

    response = None
    system_msg = {
        "role": "system", 
        "content": active_system_prompt + "\n[INSTRUKSI WAJIB]: Jika Yus memberikan perintah terkait kendali sistem Windows (buka aplikasi, ngetik, hotkey/shortcut, screenshot, tutup aplikasi), gunakan tool `windows_control_gateway`."
    }
    raw_history = trim_history(conversation_history, max_messages=6)
    clean_history = clean_messages_for_api(raw_history)
    current_messages = [system_msg] + clean_history

    for model_name in active_models:
        try:
            print(f"🔄 [{current_model_mode}] Mencoba model: {model_name}...")
            api_kwargs = {
                "model": model_name,
                "messages": current_messages,
            }
            if active_tools: 
                api_kwargs["tools"] = active_tools
                api_kwargs["tool_choice"] = tool_choice_setting

            response = client_to_use.chat.completions.create(**api_kwargs)
            break  
        except Exception as e:
            print(f"⚠️ Model {model_name} beralih/error: {e}")
            continue

    if not response:
        final_reply = "Duh, server lagi sibuk atau gagal baca file. Coba ketik ulang ya!"
        conversation_history.append({"role": "assistant", "content": final_reply})
        save_chat_history(conversation_history)
        return final_reply

    response_message = response.choices[0].message
    tool_calls = getattr(response_message, 'tool_calls', None)

    if tool_calls and active_tools:
        msg_dict = {
            "role": "assistant",
            "content": response_message.content or "",
            "tool_calls": [
                {
                    "id": tc.id,
                    "type": tc.type,
                    "function": {
                        "name": tc.function.name,
                        "arguments": tc.function.arguments
                    }
                } for tc in tool_calls
            ]
        }
        conversation_history.append(msg_dict)
        
        tool_outputs_summary = []
        for tool_call in tool_calls:
            function_name = sanitize_tool_name(tool_call.function.name)
            try:
                function_args = json.loads(tool_call.function.arguments) if tool_call.function.arguments else {}
            except Exception:
                function_args = {}

            print(f"\n[AGENT ACTION] Eksekusi fungsi 1 pintu: {function_name}({function_args})")
            if function_name in ALL_TOOLS:
                tool_output = ALL_TOOLS[function_name](**function_args)
            else:
                tool_output = f"Fungsi '{function_name}' ga ditemukan di sistem."

            tool_outputs_summary.append(str(tool_output))
            conversation_history.append({
                "tool_call_id": tool_call.id,
                "role": "tool",
                "name": function_name,
                "content": str(tool_output)
            })
        
        save_chat_history(conversation_history)
        raw_reply = f"{tool_outputs_summary[0]}"
    else:
        raw_reply = response_message.content or "Ada yang bisa dibantu lagi?"

    if "<think>" in raw_reply and "</think>" in raw_reply:
        raw_reply = raw_reply.split("</think>")[-1].strip()

    final_reply = clean_text_for_tts_and_ui(raw_reply)
    conversation_history.append({"role": "assistant", "content": final_reply})
    save_chat_history(conversation_history)
    return final_reply


def rekam_dan_transkripsi_suara(sample_rate: int = 16000):
    print("\n🎙️ [Standby] Mendengarkan... Silakan berbicara...")
    threshold = 900            
    silence_limit = 1.5  
    chunk_duration = 0.1  
    chunk_samples = int(sample_rate * chunk_duration)
    audio_chunks = []
    is_speaking = False
    silent_chunks_count = 0
    max_silent_chunks = int(silence_limit / chunk_duration)

    try:
        with sd.InputStream(samplerate=sample_rate, channels=1, dtype='int16') as stream:
            while True:
                if IS_KURO_SPEAKING:
                    time.sleep(0.2)
                    continue
                audio_chunk, _ = stream.read(chunk_samples)
                volume = np.abs(audio_chunk).mean()
                if volume > threshold:
                    if not is_speaking:
                        print("🔴 [Merekam suara...]")
                        is_speaking = True
                    audio_chunks.append(audio_chunk)
                    silent_chunks_count = 0
                else:
                    if is_speaking:
                        audio_chunks.append(audio_chunk)
                        silent_chunks_count += 1
                        if silent_chunks_count > max_silent_chunks:
                            break                      
                            if not audio_chunks:
                                return ""
                                print("⏹️ [Selesai merekam, memproses suara ke teks...]")
                                audio_data = np.concatenate(audio_chunks, axis=0)
                                wav_buffer = io.BytesIO()
                                wav.write(wav_buffer, sample_rate, audio_data)
                                wav_buffer.name = "audio_user.wav"
                                wav_buffer.seek(0)
                                transcript = groq_client.audio.transcriptions.create(
                                    model="whisper-large-v3",
                                    file=wav_buffer,
                                    language="id",
                                    response_format="text"
                                    )
                                    result_text = transcript.strip()
                                    print(f"🗣️ Kamu(Suara): {result_text}")
                                    return result_text
                                    except Exception as e:
                                        print(f"❌ Gagal transkripsi suara: {e}")
                                        return "" 


def deteksi_ekspresi(text: str) -> str:
    t = text.lower()
    if any(k in t for k in ["!", "serius", "ha?", "wah", "kaget", "masa", "anjir", "beneran", "😲", "😱", "eh"]):
        return "surprised"
    elif any(k in t for k in ["hmm", "tunggu", "mikir", "lagi", "sebentar", "🤔"]):
        return "thinking"
    elif any(k in t for k in ["hehe", "wkwk", "haha", "senang", "siap", "bantu", "😊", "✨", "halo"]):
        return "happy"
    else:
        return "normal"




# --- FLASK WEB SERVER & UI STATE CONFIGURATION ---
app = Flask(__name__, static_folder='media', template_folder='templates')


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/settings')
def settings():
    return render_template('settings.html')


@app.route('/save-settings', methods=['POST'])
def save_settings_backend():
    req_data = request.get_json()
    if req_data:
        with open(SETTINGS_FILE, 'w') as f:
            json.dump(req_data, f, indent=4)
        return jsonify({"status": "success", "message": "Pengaturan tersimpan!"}), 200
    return jsonify({"status": "error", "message": "Data tidak valid"}), 400

@app.route('/get-settings', methods=['GET'])
def kuro_get_settings():
    data = load_settings_data()
    return jsonify(data)

@app.route('/save-settings', methods=['POST'])
def kuro_save_settings():
    req_data = request.get_json()
    if req_data:
        with open(SETTINGS_FILE, 'w') as f:
            json.dump(req_data, f, indent=4)
        return jsonify({"status": "success", "message": "Pengaturan tersimpan!"}), 200
    return jsonify({"status": "error", "message": "Data tidak valid"}), 400

@app.route('/get-api-limit', methods=['GET'])
def get_api_limit():
    active_mode = app_state.get("active_model", "Kuroyami 1.0")
    models_by_mode = {
        "Kuro Pro 2.0": {
            "provider": "openrouter",
            "models": ["poolside/laguna-s-2.1:free", "nvidia/nemotron-3.5-lightning:free"]
        },
        "Kuro Learning 1.5": {
            "provider": "groq",
            "models": ["openai/gpt-oss-120b", "openai/gpt-oss-20b", "llama-3.3-70b-versatile"]
        },
        "Kuroyami 1.0": {
            "provider": "groq",
            "models": ["qwen/qwen3.6-27b", "openai/gpt-oss-20b"]
        }
    }

    current_config = models_by_mode.get(active_mode, models_by_mode["Kuroyami 1.0"])
    provider = current_config["provider"]
    model_list = current_config["models"]

    models_status = []

    for model_id in model_list:
        model_info = {
            "model_id": model_id,
            "requests_limit": "1440",
            "requests_remaining": "1430",
            "reset_time": "Besok, 00:00 WIB",
            "status": "Ready"
        }

        try:
            if provider == "groq":
                groq_key = os.getenv("GROQ_API_KEY")
                headers = {
                    "Authorization": f"Bearer {groq_key}",
                    "Content-Type": "application/json"
                }
                payload = {
                    "model": model_id,
                    "messages": [{"role": "user", "content": "ping"}],
                    "max_tokens": 1
                }
                res = requests.post("https://api.groq.com/openai/v1/chat/completions", json=payload, headers=headers, timeout=4)
                
                if res.status_code in [200, 429]:
                    h = res.headers
                    model_info["requests_limit"] = h.get("x-ratelimit-limit-requests", h.get("x-ratelimit-limit-tokens", "1440"))
                    model_info["requests_remaining"] = h.get("x-ratelimit-remaining-requests", h.get("x-ratelimit-remaining-tokens", "1430"))
                    model_info["reset_time"] = h.get("x-ratelimit-reset-requests", h.get("x-ratelimit-reset-tokens", "Beberapa menit"))
                    if res.status_code == 429:
                        model_info["status"] = "Limit Reached"
                else:
                    model_info["status"] = f"HTTP {res.status_code}"

            elif provider == "openrouter":
                openrouter_key = os.getenv("OPENROUTER_API_KEY")
                headers = {"Authorization": f"Bearer {openrouter_key}"}

                res = requests.get("https://openrouter.ai/api/v1/auth/key", headers=headers, timeout=4)
                if res.status_code == 200:
                    data = res.json().get("data", {})
                    limit_val = data.get("limit")
                    usage_val = data.get("usage")
                    
                    if limit_val is not None:
                        model_info["requests_limit"] = str(limit_val)
                        model_info["requests_remaining"] = str(round(limit_val - (usage_val or 0), 4))
                    else:
                        model_info["requests_limit"] = "Free / Unlimited"
                        model_info["requests_remaining"] = "Aktif"
                    
                    model_info["reset_time"] = "Reset Harian"
                    model_info["status"] = "Ready"
                else:
                    model_info["status"] = "Error Key"

        except Exception as e:
            print(f"⚠️ Gagal cek status model {model_id}: {e}")
            model_info["status"] = "Offline/Error"

        models_status.append(model_info)

    return jsonify({
        "active_mode": active_mode,
        "provider": provider.upper(),
        "models": models_status
    })

@app.route('/send', methods=['POST'])
def send_message():
    data = request.get_json(force=True) or {}
    user_message = data.get("message", "").strip()
    
    if user_message:
        print(f"⌨️ Kamu(Teks): {user_message}")
        update_ui("Hmm, lagi mikir...", expression="thinking")
        
        def process_typed_msg():
            try:
                balasan = chat_agent(user_message)
                print(f"Kuro: {balasan}\n")
                ekspresi_kuro = deteksi_ekspresi(balasan)
                update_ui(balasan, expression=ekspresi_kuro)
                kuro_speak_anime(balasan)
            except Exception as e:
                print(f"⚠️ Error saat memproses pesan ketik: {e}")
                update_ui("Duh, ada error...", expression="normal")
            
        threading.Thread(target=process_typed_msg, daemon=True).start()
        return jsonify({"status": "success"})
    
    return jsonify({"status": "error", "message": "Pesan kosong!"}), 400

@app.route("/send-with-file", methods=["POST"])
def send_with_file():
    user_message = request.form.get("message", "").strip()
    active_model = request.form.get(
        "model", app_state.get("active_model", "Kuro Learning 1.5")
    )

    uploaded_files = request.files.getlist("files")
    if not uploaded_files or (len(uploaded_files) == 1 and uploaded_files[0].filename == ""):
        uploaded_files = request.files.getlist("file")

    valid_files = [f for f in uploaded_files if f and f.filename != ""]

    if not user_message and not valid_files:
        return jsonify({"status": "error", "message": "Pesan atau file kosong!"}), 400

    file_context_list = []

    for uploaded_file in valid_files:
        file_name = uploaded_file.filename
        file_extension = file_name.split(".")[-1].lower() if "." in file_name else ""
        print(f"📁 Menerima file: {file_name} (Ekstensi: {file_extension})")

        unique_prefix = str(uuid.uuid4())[:8]
        temp_path = f"temp_{unique_prefix}_{file_name}"

        try:
            if file_extension in [
                "txt", "py", "md", "json", "html", "css",
                "js", "csv", "c", "cpp", "java"
            ]:
                file_content = uploaded_file.read().decode("utf-8", errors="ignore")
                file_context_list.append(
                    f"\n\n[Isi File Teks '{file_name}':\n{file_content}\n]"
                )

            # Dokumen Word (.docx)
            elif file_extension == "docx":
                uploaded_file.save(temp_path)
                doc = Document(temp_path)
                doc_text = "\n".join(
                    [para.text for para in doc.paragraphs if para.text.strip()]
                )
                file_context_list.append(
                    f"\n\n[Isi Dokumen Word '{file_name}':\n{doc_text}\n]"
                )
                if os.path.exists(temp_path):
                    os.remove(temp_path)

            # Dokumen PDF (.pdf)
            elif file_extension == "pdf":
                uploaded_file.save(temp_path)
                reader = PdfReader(temp_path)
                pdf_text = ""
                for page in reader.pages:
                    text = page.extract_text()
                    if text:
                        pdf_text += text + "\n"
                file_context_list.append(
                    f"\n\n[Isi Dokumen PDF '{file_name}':\n{pdf_text}\n]"
                )
                if os.path.exists(temp_path):
                    os.remove(temp_path)

            # File Gambar (.jpg, .png, dll)
            elif file_extension in ["jpg", "jpeg", "png", "webp"]:
                file_context_list.append(
                    f"\n\n[Pengguna melampirkan gambar: {file_name}]"
                )

            else:
                file_context_list.append(f"\n\n[File dilampirkan: {file_name}]")

        except Exception as e:
            file_context_list.append(
                f"\n\n[Gagal membaca isi file {file_name}: {str(e)}]"
            )
            print(f"⚠️ Error parsing file {file_name}: {e}")
            if os.path.exists(temp_path):
                os.remove(temp_path)

    file_context = "".join(file_context_list)
    combined_input = user_message + file_context

    print(
        f"⌨️ User (Ketik + {len(valid_files)} File): {user_message} [File diproses backend]"
    )
    update_ui(
        f"Hmm, Kuro lagi bedah {len(valid_files)} file kamu...",
        expression="thinking",
    )

    def process_file_msg():
        try:
            balasan = chat_agent(combined_input)
            print(f"Kuro: {balasan}\n")
            ekspresi_kuro = deteksi_ekspresi(balasan)
            update_ui(balasan, expression=ekspresi_kuro)
            kuro_speak_anime(balasan)
        except Exception as e:
            print(f"⚠️ Error saat memproses agen dengan file: {e}")
            update_ui(
                "Duh, ada kendala pas baca file-nya nih...", expression="normal"
            )

    threading.Thread(target=process_file_msg, daemon=True).start()
    return jsonify({"status": "success"})

@app.route('/status')
def status():
    app_state["is_speaking"] = IS_KURO_SPEAKING
    return jsonify(app_state)


@app.route('/switch-model', methods=['POST'])
def switch_model():
    data = request.json or {}
    selected_model = data.get('model', 'Kuroyami 1.0')
    app_state["active_model"] = selected_model
    
    if selected_model == "Kuro Pro 2.0":
        notif_text = "Kuro Pro 2.0 sedang dalam pengembangan! Model ini khusus untuk eksekusi coding project tingkat lanjut dengan akses penuh agen."
    elif selected_model == "Kuro Learning 1.5":
        notif_text = "Kuro Learning 1.5 aktif! Siap nemenin kamu belajar materi sambil ngedaliin ekosistem google"
    else:
        notif_text = "Kembali ke Kuroyami 1.0."
        
    app_state["text"] = notif_text
    app_state["expression"] = "happy"
    print(f"Model diganti ke: {selected_model}")
    
    threading.Thread(target=lambda: kuro_speak_anime(notif_text), daemon=True).start()
    return jsonify({"status": "success", "active_model": selected_model})


def start_flask():
    import logging
    log = logging.getLogger('werkzeug')
    log.setLevel(logging.ERROR)
    app.run(host='127.0.0.1', port=5000, debug=False, use_reloader=False)


def update_ui(text, expression="normal", is_speaking=False):
    app_state["text"] = text
    app_state["expression"] = expression
    app_state["is_speaking"] = is_speaking


def ai_agent_background_loop():
    salam_awal = "Halo! Ada yang bisa dibantu hari ini?"
    print(f"Kuro: {salam_awal}\n")
    update_ui(salam_awal, expression="happy")
    kuro_speak_anime(salam_awal)  

    while True:
        try:
            pesan = rekam_dan_transkripsi_suara()
            if not pesan:
                continue
                
            if pesan.lower() in ['exit', 'quit', 'keluar']:
                pesan_keluar = "Dadah! Sampai jumpa lagi!"
                print(f"Kuro: {pesan_keluar} 👋✨")
                update_ui(pesan_keluar, expression="happy")
                kuro_speak_anime(pesan_keluar)
                break

            update_ui("Hmm, lagi mikir...", expression="thinking")
            balasan = chat_agent(pesan)
            ekspresi_kuro = deteksi_ekspresi(balasan)
            update_ui(balasan, expression=ekspresi_kuro)
            kuro_speak_anime(balasan)
            
        except KeyboardInterrupt:
            print("\n👋 Keluar dari program.")
            break



