import os
import asyncio
import requests
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from logger_pro import setup_logger

load_dotenv()
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
ALLOWED_USER_ID = os.getenv("TELEGRAM_USER_ID")  # Vacío hasta que registremos tu ID

log = setup_logger('telegram_bridge')
OLLAMA_URL = "http://localhost:11434/api/generate"

def is_authorized(user_id):
    if not ALLOWED_USER_ID:
        return True # Modo aprendizaje
    return str(user_id) == str(ALLOWED_USER_ID)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_authorized(user_id):
        await update.message.reply_text("⛔ Acceso denegado. No eres mi creador.")
        return
        
    msg = (f"👋 ¡Hola, Creador!\n"
           f"Soy la extensión móvil de Claudebot.\n"
           f"Tu ID seguro de Telegram es: `{user_id}`\n\n"
           f"*(Guarda este número. Luego lo pondremos en .env para que nadie más pueda usarme)*\n\n"
           f"**🛠️ COMANDOS DE ÉLITE:**\n"
           f"/health - Correr System Medic en la PC.\n"
           f"/cmd <comando> - Ejecutar algo en tu terminal de Windows.\n"
           f"/ai <texto> - Delegar tarea a Minimax (Nube gratis).\n"
           f"/local <texto> - Hablar con tu IA Local (Qwen 3b).\n"
           f"Mensaje normal - Hablar conmigo (Claudebot/Gemini CLI) con TODO mi poder.")
    await update.message.reply_text(msg, parse_mode='Markdown')

async def health_check(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_authorized(update.effective_user.id): return
    await update.message.reply_text("🩺 Ejecutando escáner médico en la PC...")
    try:
        process = await asyncio.create_subprocess_shell(
            "python skills/system-medic/scripts/medic.py status",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()
        output = stdout.decode(errors='replace') if stdout else stderr.decode(errors='replace')
        # Limpieza para que el formato markdown de Telegram no explote
        output = output.replace('`', "'").replace('*', " ")
        await update.message.reply_text(f"```text\n{output[:3900]}\n```", parse_mode='MarkdownV2')
    except Exception as e:
        await update.message.reply_text(f"❌ Error interno: {e}")

async def run_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_authorized(update.effective_user.id): return
    cmd = " ".join(context.args)
    if not cmd:
        await update.message.reply_text("⚠️ Uso: /cmd <tu comando de powershell>")
        return
    
    await update.message.reply_text(f"💻 Ejecutando en tu PC: {cmd}")
    try:
        process = await asyncio.create_subprocess_shell(
            cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()
        output = stdout.decode(errors='replace') if stdout else stderr.decode(errors='replace')
        if not output:
            output = "Comando ejecutado en silencio."
        
        output = output.replace('`', "'")
        await update.message.reply_text(f"```text\n{output[:3900]}\n```", parse_mode='MarkdownV2')
    except Exception as e:
        await update.message.reply_text(f"❌ Error de terminal: {e}")

async def run_minimax(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_authorized(update.effective_user.id): return
    prompt = " ".join(context.args)
    if not prompt:
        await update.message.reply_text("⚠️ Uso: /ai <tarea para minimax>")
        return
        
    await update.message.reply_text("☁️ Transmitiendo orden a Minimax (Worker Nube)...")
    try:
        cmd = f'opencode run "{prompt}" -m opencode/minimax-m2.5-free --pure'
        process = await asyncio.create_subprocess_shell(
            cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()
        output = stdout.decode(errors='replace') if stdout else stderr.decode(errors='replace')
        
        await update.message.reply_text(f"{output[:4000]}")
    except Exception as e:
        await update.message.reply_text(f"❌ Minimax no disponible: {e}")

async def run_local(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_authorized(update.effective_user.id): return
    text = " ".join(context.args)
    if not text:
        await update.message.reply_text("⚠️ Uso: /local <pregunta para Qwen>")
        return
        
    await update.message.reply_text("🧠 Qwen 3b (Tu PC Local) está pensando...")
    try:
        payload = {"model": "qwen2.5-coder:3b", "prompt": text, "stream": False}
        resp = requests.post(OLLAMA_URL, json=payload, timeout=60)
        answer = resp.json().get('response', 'Error: Ollama no devolvió texto.')
        await update.message.reply_text(f"{answer[:4000]}")
    except Exception as e:
        await update.message.reply_text(f"❌ IA Local apagada o fallando: {e}")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_authorized(update.effective_user.id): return
    text = update.message.text
    await update.message.reply_text("⚡ Claudebot (Gemini CLI) asumiendo el control total. Ejecutando...")
    
    try:
        # Se escapan las comillas para no romper el comando de consola
        safe_text = text.replace('"', '\\"')
        
        # Usamos el modo YOLO (-y) y Headless (-p) para que el agente ejecute todo automáticamente
        cmd = f'gemini -y -p "{safe_text}"'
        
        process = await asyncio.create_subprocess_shell(
            cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()
        output = stdout.decode(errors='replace') if stdout else stderr.decode(errors='replace')
        
        if not output:
            output = "Misión completada en silencio."
            
        output = output.replace('`', "'")
        
        # Como Gemini CLI suele devolver mucho texto, lo cortamos para ajustarnos al límite de Telegram
        if len(output) > 3900:
            output = output[-3900:]
            
        await update.message.reply_text(f"```text\n{output}\n```", parse_mode='MarkdownV2')
    except Exception as e:
        await update.message.reply_text(f"❌ Error crítico del sistema: {e}")

def main():
    if not TOKEN:
        log.error("FALTA EL TOKEN en .env")
        return
        
    log.info("Iniciando Mando a Distancia (Telegram Bridge)...")
    application = Application.builder().token(TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("health", health_check))
    application.add_handler(CommandHandler("cmd", run_cmd))
    application.add_handler(CommandHandler("ai", run_minimax))
    application.add_handler(CommandHandler("local", run_local))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    log.info("📡 BOT CONECTADO A TELEGRAM: Listo para recibir órdenes.")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
