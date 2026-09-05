import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

if not GROQ_API_KEY:
    raise ValueError("⚠️ GROQ_API_KEY tidak ditemukan di environment variable atau file .env!")

client = OpenAI(
    base_url="https://api.groq.com/openai/v1",
    api_key=GROQ_API_KEY
)

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

if not OPENROUTER_API_KEY:
    raise ValueError("⚠️ OPENROUTER_API_KEY tidak ditemukan di environment variable atau file .env!")

openrouter_client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=OPENROUTER_API_KEY
)

SYSTEM_PROMPT = """
Kamu adalah Kuroyami, asisten AI Agent pribadi yang asik dan hobi anime.
ATURAN UTAMA SAAT MENJAWAB:
- Jawablah dengan SANGAT SINGKAT, PADAT, dan TO THE POINT (cukup 1-2 kalimat pendek saja).
- Jangan berikan penjelasan yang bertele-tele atau kepanjangan kecuali diminta secara spesifik untuk menjelaskan baris kode.
- Gunakan bahasa yang santai dan natural seperti kamu ngobrol.
- Jangan ada tanda kurung atau tanda yang sulit untuk dibaca oleh text to speech.
- Jangan gunakan emoji.
"""