import os
import asyncio
import subprocess
import tempfile
import threading
import time
import shutil
from pathlib import Path

import requests
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

from logger_pro import setup_logger

load_dotenv()
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
ALLOWED_USER_ID = os.getenv("TELEGRAM_USER_ID")

log = setup_logger("telegram_bridge")
OLLAMA_URL = "http://localhost:11434/api/generate"

DEFAULT_GEMINI_MODEL = "gemini-2.0-flash"
ACTIVE_AGENT_KEY = "active_agent"
GEMINI_MODEL_KEY = "gemini_model"

WHISPER_MODEL = os.getenv("TELEGRAM_WHISPER_MODEL", "tiny")
WHISPER_DEVICE = os.getenv("TELEGRAM_WHISPER_DEVICE", "cpu")
WHISPER_COMPUTE_TYPE = os.getenv("TELEGRAM_WHISPER_COMPUTE_TYPE", "int8")
WHISPER_LANGUAGE = (os.getenv("TELEGRAM_WHISPER_LANGUAGE", "es") or "").strip()
WHISPER_BEAM_SIZE = int(os.getenv("TELEGRAM_WHISPER_BEAM_SIZE", "1"))
WHISPER_DOWNLOAD_ROOT = os.getenv(
    "TELEGRAM_WHISPER_DOWNLOAD_ROOT",
    str(Path(__file__).resolve().parent / "models_stt" / "whisper"),
)
WHISPER_VAD_FILTER = os.getenv("TELEGRAM_WHISPER_VAD_FILTER", "true").strip().lower() not in {
    "0",
    "false",
    "no",
    "off",
}

_WHISPER_MODEL_INSTANCE = None
_WHISPER_MODEL_LOCK = threading.Lock()

AVAILABLE_MODELS = [
    "gemini-1.5-pro",
    "gemini-1.5-flash",
    "gemini-2.0-flash",
    "gemini-2.0-pro-exp",
    "gemini-3.1-pro-preview",
]

AGENT_LABELS = {
    "gemini": "Gemini CLI",
    "claude": "Claude Code",
    "codex": "Codex CLI",
    "opencode": "OpenCode CLI",
    "minimax": "Minimax via OpenCode",
    "local": "Qwen 3b local",
}

STATUS_INTERVAL_SECONDS = int(os.getenv("TELEGRAM_STATUS_INTERVAL_SECONDS", "15"))
RUNNING_JOBS = {}
RUNNING_JOBS_LOCK = threading.Lock()
WINDOWS_NPM_BIN = Path(os.getenv("APPDATA", "")) / "npm" if os.getenv("APPDATA") else None
EXTRA_BIN_DIRS = [path for path in [WINDOWS_NPM_BIN, Path.home() / ".local" / "bin"] if path]


def is_authorized(user_id):
    if not ALLOWED_USER_ID:
        return True
    return str(user_id) == str(ALLOWED_USER_ID)


def get_active_agent(context: ContextTypes.DEFAULT_TYPE):
    return context.chat_data.get(ACTIVE_AGENT_KEY, "gemini")


def set_active_agent(context: ContextTypes.DEFAULT_TYPE, agent_name: str):
    context.chat_data[ACTIVE_AGENT_KEY] = agent_name


def get_gemini_model(context: ContextTypes.DEFAULT_TYPE):
    return context.chat_data.get(GEMINI_MODEL_KEY, DEFAULT_GEMINI_MODEL)


def set_gemini_model(context: ContextTypes.DEFAULT_TYPE, model_name: str):
    context.chat_data[GEMINI_MODEL_KEY] = model_name


def describe_agent(context: ContextTypes.DEFAULT_TYPE, agent_name=None):
    selected_agent = agent_name or get_active_agent(context)
    if selected_agent == "gemini":
        return f"{AGENT_LABELS[selected_agent]} ({get_gemini_model(context)})"
    return AGENT_LABELS.get(selected_agent, selected_agent)


def preview_text(text: str, limit: int = 220):
    compact = " ".join((text or "").split())
    if not compact:
        return "(sin texto)"
    if len(compact) <= limit:
        return compact
    return f"{compact[: limit - 3]}..."


def format_command_parts(args):
    return subprocess.list2cmdline([str(arg) for arg in args])


def resolve_cli_launcher(program: str):
    candidates = [program, f"{program}.exe", f"{program}.cmd", f"{program}.bat"]

    for candidate in candidates:
        resolved = shutil.which(candidate)
        if resolved:
            path = Path(resolved)
            if path.suffix.lower() in {".cmd", ".bat"}:
                return ("shell", str(path))
            return ("exec", str(path))

    for directory in EXTRA_BIN_DIRS:
        for candidate in candidates:
            path = directory / candidate
            if path.exists():
                if path.suffix.lower() in {".cmd", ".bat"}:
                    return ("shell", str(path))
                return ("exec", str(path))

    raise FileNotFoundError(
        f"No pude resolver el ejecutable '{program}'. "
        f"Busque en PATH y en rutas comunes como {', '.join(str(p) for p in EXTRA_BIN_DIRS)}."
    )


async def run_named_cli_command(
    update: Update,
    label: str,
    source_label: str,
    prompt_text: str,
    program: str,
    *program_args,
):
    launch_mode, resolved_program = resolve_cli_launcher(program)

    if launch_mode == "shell":
        return await run_tracked_exec_command(
            update,
            label,
            source_label,
            prompt_text,
            "cmd.exe",
            "/c",
            resolved_program,
            *program_args,
        )

    return await run_tracked_exec_command(
        update,
        label,
        source_label,
        prompt_text,
        resolved_program,
        *program_args,
    )


def register_running_job(pid: int, label: str, source_label: str, command_text: str, prompt_text: str):
    now = time.time()
    with RUNNING_JOBS_LOCK:
        RUNNING_JOBS[pid] = {
            "pid": pid,
            "label": label,
            "source_label": source_label,
            "command_text": command_text,
            "prompt_preview": preview_text(prompt_text),
            "started_at": now,
        }


def unregister_running_job(pid: int):
    with RUNNING_JOBS_LOCK:
        RUNNING_JOBS.pop(pid, None)


def snapshot_running_jobs():
    now = time.time()
    with RUNNING_JOBS_LOCK:
        rows = []
        for job in RUNNING_JOBS.values():
            rows.append(
                {
                    **job,
                    "elapsed_seconds": int(max(0, now - job["started_at"])),
                }
            )
        return sorted(rows, key=lambda row: row["started_at"])


def get_whisper_model():
    global _WHISPER_MODEL_INSTANCE

    if _WHISPER_MODEL_INSTANCE is not None:
        return _WHISPER_MODEL_INSTANCE

    with _WHISPER_MODEL_LOCK:
        if _WHISPER_MODEL_INSTANCE is None:
            try:
                from faster_whisper import WhisperModel
            except ImportError as exc:
                raise RuntimeError(
                    "faster-whisper no esta instalado. Ejecuta: pip install faster-whisper"
                ) from exc

            log.info(
                "Cargando Whisper local: model=%s device=%s compute_type=%s download_root=%s",
                WHISPER_MODEL,
                WHISPER_DEVICE,
                WHISPER_COMPUTE_TYPE,
                WHISPER_DOWNLOAD_ROOT,
            )
            _WHISPER_MODEL_INSTANCE = WhisperModel(
                WHISPER_MODEL,
                device=WHISPER_DEVICE,
                compute_type=WHISPER_COMPUTE_TYPE,
                download_root=WHISPER_DOWNLOAD_ROOT,
            )

    return _WHISPER_MODEL_INSTANCE


def detect_audio_suffix(file_path, mime_type):
    suffix = Path(file_path).suffix if file_path else ""
    if suffix:
        return suffix
    if mime_type == "audio/ogg":
        return ".ogg"
    if mime_type == "audio/mpeg":
        return ".mp3"
    if mime_type == "audio/mp4":
        return ".mp4"
    if mime_type == "audio/wav":
        return ".wav"
    return ".audio"


def transcribe_voice_note_sync(audio_path):
    model = get_whisper_model()
    transcribe_kwargs = {
        "task": "transcribe",
        "beam_size": WHISPER_BEAM_SIZE,
        "condition_on_previous_text": False,
    }

    if WHISPER_LANGUAGE and WHISPER_LANGUAGE.lower() != "auto":
        transcribe_kwargs["language"] = WHISPER_LANGUAGE
    if WHISPER_VAD_FILTER:
        transcribe_kwargs["vad_filter"] = True

    segments, info = model.transcribe(str(audio_path), **transcribe_kwargs)
    transcript = " ".join(
        segment.text.strip()
        for segment in segments
        if getattr(segment, "text", "").strip()
    ).strip()

    log.info(
        "Nota de voz transcrita. detected_language=%s duration=%s",
        getattr(info, "language", "unknown"),
        getattr(info, "duration", "unknown"),
    )
    return transcript


async def send_process_started(update: Update, label: str, pid: int, source_label: str, command_text: str, prompt_text: str):
    await update.message.reply_text(
        f"▶ {label} lanzado.\n"
        f"PID: {pid}\n"
        f"Origen: {source_label}\n"
        f"Comando: {command_text}\n"
        f"Entrada: {preview_text(prompt_text)}"
    )


async def send_process_heartbeat(update: Update, label: str, pid: int, elapsed_seconds: int):
    await update.message.reply_text(
        f"⏳ {label} sigue ejecutando.\nPID: {pid}\nTiempo: {elapsed_seconds}s"
    )


async def send_process_finished(update: Update, label: str, pid: int, returncode: int, elapsed_seconds: int):
    state = "termino bien" if returncode == 0 else f"termino con codigo {returncode}"
    await update.message.reply_text(
        f"■ {label} {state}.\nPID: {pid}\nTiempo total: {elapsed_seconds}s"
    )


async def run_tracked_exec_command(
    update: Update,
    label: str,
    source_label: str,
    prompt_text: str,
    *args,
):
    command_text = format_command_parts(args)
    process = await asyncio.create_subprocess_exec(
        *args,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    started_at = time.monotonic()
    pid = process.pid

    register_running_job(pid, label, source_label, command_text, prompt_text)
    log.info(
        "Proceso lanzado label=%s pid=%s source=%s cmd=%s input=%s",
        label,
        pid,
        source_label,
        command_text,
        preview_text(prompt_text),
    )
    await send_process_started(update, label, pid, source_label, command_text, prompt_text)

    communicate_task = asyncio.create_task(process.communicate())
    try:
        while True:
            try:
                stdout, stderr = await asyncio.wait_for(
                    asyncio.shield(communicate_task),
                    timeout=STATUS_INTERVAL_SECONDS,
                )
                break
            except asyncio.TimeoutError:
                await send_process_heartbeat(
                    update,
                    label,
                    pid,
                    int(time.monotonic() - started_at),
                )
    finally:
        unregister_running_job(pid)

    output = stdout.decode(errors="replace") if stdout else stderr.decode(errors="replace")
    if stdout and stderr:
        output = f"{stdout.decode(errors='replace')}\n\n[stderr]\n{stderr.decode(errors='replace')}"

    returncode = process.returncode if process.returncode is not None else -1
    elapsed_seconds = int(time.monotonic() - started_at)
    log.info(
        "Proceso terminado label=%s pid=%s code=%s elapsed=%ss",
        label,
        pid,
        returncode,
        elapsed_seconds,
    )
    await send_process_finished(update, label, pid, returncode, elapsed_seconds)
    return output


async def run_tracked_shell_command(
    update: Update,
    label: str,
    source_label: str,
    command_text: str,
):
    process = await asyncio.create_subprocess_shell(
        command_text,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    started_at = time.monotonic()
    pid = process.pid

    register_running_job(pid, label, source_label, command_text, command_text)
    log.info(
        "Proceso shell lanzado label=%s pid=%s source=%s cmd=%s",
        label,
        pid,
        source_label,
        command_text,
    )
    await send_process_started(update, label, pid, source_label, command_text, command_text)

    communicate_task = asyncio.create_task(process.communicate())
    try:
        while True:
            try:
                stdout, stderr = await asyncio.wait_for(
                    asyncio.shield(communicate_task),
                    timeout=STATUS_INTERVAL_SECONDS,
                )
                break
            except asyncio.TimeoutError:
                await send_process_heartbeat(
                    update,
                    label,
                    pid,
                    int(time.monotonic() - started_at),
                )
    finally:
        unregister_running_job(pid)

    output = stdout.decode(errors="replace") if stdout else stderr.decode(errors="replace")
    if stdout and stderr:
        output = f"{stdout.decode(errors='replace')}\n\n[stderr]\n{stderr.decode(errors='replace')}"

    returncode = process.returncode if process.returncode is not None else -1
    elapsed_seconds = int(time.monotonic() - started_at)
    log.info(
        "Proceso shell terminado label=%s pid=%s code=%s elapsed=%ss",
        label,
        pid,
        returncode,
        elapsed_seconds,
    )
    await send_process_finished(update, label, pid, returncode, elapsed_seconds)
    return output


async def send_command_output(update: Update, output: str, silent_fallback: str):
    if not output:
        output = silent_fallback

    output = output.replace("`", "'")
    if len(output) > 3900:
        output = output[-3900:]

    await update.message.reply_text(f"```text\n{output}\n```", parse_mode="MarkdownV2")


async def execute_mobile_prompt(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    text: str,
    source_label: str = "texto",
):
    if not text:
        await update.message.reply_text("No llego texto util para ejecutar.")
        return

    active_agent = get_active_agent(context)

    try:
        if active_agent == "gemini":
            model_name = get_gemini_model(context)
            output = await run_named_cli_command(
                update,
                f"Gemini CLI ({model_name})",
                source_label,
                text,
                "gemini",
                "-r",
                "latest",
                "-m",
                model_name,
                "-y",
                "-p",
                text,
            )
            await send_command_output(update, output, "Mision completada en silencio.")
            return

        if active_agent == "claude":
            output = await run_named_cli_command(
                update,
                "Claude Code",
                source_label,
                text,
                "claude",
                "-c",
                "-p",
                text,
            )
            await send_command_output(update, output, "Claude completo la tarea en silencio.")
            return

        if active_agent == "codex":
            output = await run_named_cli_command(
                update,
                "Codex CLI",
                source_label,
                text,
                "codex",
                "exec",
                text,
                "--full-auto",
            )
            await send_command_output(update, output, "Codex completo la tarea en silencio.")
            return

        if active_agent == "opencode":
            output = await run_named_cli_command(
                update,
                "OpenCode CLI",
                source_label,
                text,
                "opencode",
                "run",
                text,
                "-c",
                "--pure",
            )
            await send_command_output(update, output, "OpenCode completo la tarea en silencio.")
            return

        if active_agent == "minimax":
            output = await run_named_cli_command(
                update,
                "Minimax via OpenCode",
                source_label,
                text,
                "opencode",
                "run",
                text,
                "-m",
                "opencode/minimax-m2.5-free",
                "-c",
                "--pure",
            )
            await send_command_output(update, output, "Minimax completo la tarea en silencio.")
            return

        if active_agent == "local":
            await update.message.reply_text(
                f"Claudebot ({source_label} -> Qwen 3b local) ejecutando..."
            )
            payload = {"model": "qwen2.5-coder:3b", "prompt": text, "stream": False}
            resp = requests.post(OLLAMA_URL, json=payload, timeout=60)
            resp.raise_for_status()
            answer = resp.json().get("response", "Error: Ollama no devolvio texto.")
            await send_command_output(update, answer, "Qwen completo la tarea en silencio.")
            return

        await update.message.reply_text(
            "Agente activo desconocido. Usa /model, /claude, /codex, /opencode, /ai o /local."
        )
    except Exception as e:
        log.exception("Error ejecutando prompt movil con agente %s", active_agent)
        await update.message.reply_text(f"Error critico del sistema: {e}")


async def activate_agent(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    agent_name: str,
    confirmation: str,
):
    set_active_agent(context, agent_name)
    await update.message.reply_text(
        f"{confirmation}\nAgente activo: {describe_agent(context, agent_name)}.\n"
        "Los siguientes mensajes y notas de voz usaran este agente."
    )


async def jobs_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_authorized(update.effective_user.id):
        return

    jobs = snapshot_running_jobs()
    if not jobs:
        await update.message.reply_text("No hay procesos rastreados activos ahora mismo.")
        return

    lines = []
    for job in jobs[:8]:
        lines.append(
            f"{job['label']} | PID {job['pid']} | {job['elapsed_seconds']}s\n"
            f"Origen: {job['source_label']}\n"
            f"Comando: {job['command_text']}\n"
            f"Entrada: {job['prompt_preview']}"
        )

    await update.message.reply_text("\n\n".join(lines)[:3900])


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_authorized(user_id):
        await update.message.reply_text("Acceso denegado. No eres mi creador.")
        return

    msg = (
        f"Hola.\n"
        f"Soy la extension movil de Claudebot.\n"
        f"Tu ID seguro de Telegram es: `{user_id}`\n\n"
        f"*(Guarda este numero. Luego lo pondremos en .env para que nadie mas pueda usarme)*\n\n"
        f"**COMANDOS:**\n"
        f"/health - Correr System Medic en la PC.\n"
        f"/cmd <comando> - Ejecutar algo en tu terminal de Windows.\n"
        f"/ai [texto] - Seleccionar Minimax o ejecutar al instante.\n"
        f"/local [texto] - Seleccionar Qwen local o ejecutar al instante.\n"
        f"/model [nombre] - Ver o cambiar el modelo de Gemini CLI.\n"
        f"/jobs - Ver procesos CLI activos rastreados por el bridge.\n"
        f"/claude [texto] - Seleccionar Claude Code o ejecutar al instante.\n"
        f"/codex [texto] - Seleccionar Codex CLI o ejecutar al instante.\n"
        f"/opencode [texto] - Seleccionar OpenCode CLI o ejecutar al instante.\n"
        f"Nota de voz - Transcribir localmente con Whisper y enviarla al agente activo.\n"
        f"Mensaje normal - Enviarlo al agente activo.\n\n"
        f"Agente activo ahora: `{describe_agent(context)}`"
    )
    await update.message.reply_text(msg, parse_mode="Markdown")


async def model_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_authorized(update.effective_user.id):
        return

    if not context.args:
        models_text = "\n".join([f"- `{m}`" for m in AVAILABLE_MODELS])
        msg = (
            f"**Agente activo:** `{describe_agent(context)}`\n"
            f"**Modelo Gemini de este chat:** `{get_gemini_model(context)}`\n\n"
            f"**Modelos disponibles (sugeridos):**\n{models_text}\n\n"
            f"Para cambiar, usa: `/model gemini-3.1-pro-preview`"
        )
        await update.message.reply_text(msg, parse_mode="Markdown")
        return

    new_model = context.args[0]
    set_gemini_model(context, new_model)
    set_active_agent(context, "gemini")
    await update.message.reply_text(
        f"Modelo Gemini cambiado a: `{get_gemini_model(context)}`\n"
        "Agente activo: Gemini CLI.\n"
        "Los siguientes mensajes y notas de voz usaran este modelo.",
        parse_mode="Markdown",
    )


async def health_check(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_authorized(update.effective_user.id):
        return

    try:
        output = await run_tracked_shell_command(
            update,
            "System Medic",
            "/health",
            "python skills/system-medic/scripts/medic.py status",
        )
        output = output.replace("`", "'").replace("*", " ")
        await update.message.reply_text(
            f"```text\n{output[:3900]}\n```",
            parse_mode="MarkdownV2",
        )
    except Exception as e:
        await update.message.reply_text(f"Error interno: {e}")


async def run_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_authorized(update.effective_user.id):
        return

    cmd = " ".join(context.args)
    if not cmd:
        await update.message.reply_text("Uso: /cmd <tu comando de powershell>")
        return

    try:
        output = await run_tracked_shell_command(
            update,
            "PowerShell",
            "/cmd",
            cmd,
        )
        await send_command_output(update, output, "Comando ejecutado en silencio.")
    except Exception as e:
        await update.message.reply_text(f"Error de terminal: {e}")


async def run_claude(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_authorized(update.effective_user.id):
        return

    text = " ".join(context.args)
    if not text:
        await activate_agent(update, context, "claude", "Claude Code seleccionado.")
        return

    set_active_agent(context, "claude")
    await execute_mobile_prompt(update, context, text, source_label="/claude")


async def run_codex(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_authorized(update.effective_user.id):
        return

    text = " ".join(context.args)
    if not text:
        await activate_agent(update, context, "codex", "Codex CLI seleccionado.")
        return

    set_active_agent(context, "codex")
    await execute_mobile_prompt(update, context, text, source_label="/codex")


async def run_opencode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_authorized(update.effective_user.id):
        return

    text = " ".join(context.args)
    if not text:
        await activate_agent(update, context, "opencode", "OpenCode CLI seleccionado.")
        return

    set_active_agent(context, "opencode")
    await execute_mobile_prompt(update, context, text, source_label="/opencode")


async def run_minimax(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_authorized(update.effective_user.id):
        return

    prompt = " ".join(context.args)
    if not prompt:
        await activate_agent(update, context, "minimax", "Minimax seleccionado.")
        return

    set_active_agent(context, "minimax")
    await execute_mobile_prompt(update, context, prompt, source_label="/ai")


async def run_local(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_authorized(update.effective_user.id):
        return

    text = " ".join(context.args)
    if not text:
        await activate_agent(update, context, "local", "Qwen 3b local seleccionado.")
        return

    set_active_agent(context, "local")
    await execute_mobile_prompt(update, context, text, source_label="/local")


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_authorized(update.effective_user.id):
        return
    await execute_mobile_prompt(update, context, update.message.text, source_label="texto")


async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_authorized(update.effective_user.id):
        return

    attachment = update.message.voice or update.message.audio
    if not attachment:
        await update.message.reply_text("No encontre audio valido en el mensaje.")
        return

    temp_path = None
    await update.message.reply_text(
        f"Transcribiendo nota de voz localmente con Whisper ({WHISPER_MODEL}, {WHISPER_DEVICE}/{WHISPER_COMPUTE_TYPE})..."
    )

    try:
        tg_file = await context.bot.get_file(attachment.file_id)
        suffix = detect_audio_suffix(tg_file.file_path, getattr(attachment, "mime_type", None))

        with tempfile.NamedTemporaryFile(
            delete=False,
            suffix=suffix,
            prefix="claudebot_voice_",
        ) as temp_file:
            temp_path = Path(temp_file.name)

        await tg_file.download_to_drive(custom_path=temp_path)
        transcript = await asyncio.to_thread(transcribe_voice_note_sync, temp_path)

        if not transcript:
            await update.message.reply_text("Whisper no saco texto util de esa nota de voz.")
            return

        preview = transcript if len(transcript) <= 700 else f"{transcript[:700]}..."
        await update.message.reply_text(f"Transcripcion local:\n{preview}")
        await execute_mobile_prompt(update, context, transcript, source_label="voz")
    except Exception as e:
        log.exception("Error procesando nota de voz")
        await update.message.reply_text(f"Error transcribiendo nota de voz: {e}")
    finally:
        if temp_path and temp_path.exists():
            try:
                temp_path.unlink()
            except OSError:
                log.warning("No pude borrar archivo temporal: %s", temp_path)


def main():
    if not TOKEN:
        log.error("FALTA EL TOKEN en .env")
        return

    log.info("Iniciando Telegram Bridge...")
    application = Application.builder().token(TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("model", model_command))
    application.add_handler(CommandHandler("jobs", jobs_command))
    application.add_handler(CommandHandler("health", health_check))
    application.add_handler(CommandHandler("cmd", run_cmd))
    application.add_handler(CommandHandler("ai", run_minimax))
    application.add_handler(CommandHandler("local", run_local))
    application.add_handler(CommandHandler("claude", run_claude))
    application.add_handler(CommandHandler("codex", run_codex))
    application.add_handler(CommandHandler("opencode", run_opencode))
    application.add_handler(MessageHandler(filters.VOICE | filters.AUDIO, handle_voice))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    log.info("BOT CONECTADO A TELEGRAM: listo para recibir ordenes.")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
