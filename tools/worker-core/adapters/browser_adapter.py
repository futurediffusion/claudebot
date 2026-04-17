from __future__ import annotations

import asyncio
import json
import re
import subprocess
import time
from typing import Any
from urllib import error, request
from urllib.parse import urlparse

from app.config import Config
from app.logger import get_logger


class BrowserAdapter:
    """Adaptador para browser-use.

    Si BROWSER_CDP_URL esta configurado, se conecta a un Edge/Chromium existente.
    Si no, lanza un navegador visible con la configuracion indicada.
    """

    _VISION_MODEL_HINTS = (
        "gemma4",
        "qwen3.5",
        "ministral-3",
        "devstral-small-2",
        "kimi-k2.5",
        "gemini-3-flash-preview",
        "mistral-large-3",
        "qwen3-vl",
    )
    _FREEPIK_URL = "https://www.freepik.com/pikaso/ai-image-generator"
    _FREEPIK_PROMPT_PATTERNS = (
        r"campo principal:\s*['\"](?P<prompt>.+?)['\"]",
        r"prompt(?: principal)?\s*:\s*['\"](?P<prompt>.+?)['\"]",
        r"prompt.*?['\"](?P<prompt>.+?)['\"]",
    )

    def __init__(self, config: Config) -> None:
        self._config = config
        self._logger = get_logger("browser_adapter", config.logs_dir)

    def run(self, task: str) -> dict:
        """Ejecuta una tarea de automatizacion de navegador."""
        self._check_allowlist()
        self._ensure_cdp_ready()

        direct_result = self._maybe_run_direct_flow(task)
        if direct_result is not None:
            return direct_result

        from browser_use import Agent  # type: ignore
        from browser_use.browser.profile import BrowserProfile  # type: ignore

        # Inyectar Gemini si la key está presente
        gemini_key = getattr(self._config, 'gemini_api_key', None)
        if gemini_key:
            self._logger.info("Usando Gemini SECRETO como cerebro de Navegador", extra={"model": "gemini-2.0-flash"})
            from browser_use.llm.google.chat import ChatGoogle # type: ignore
            llm = ChatGoogle(model="gemini-2.0-flash", api_key=gemini_key)
        else:
            from browser_use.llm.anthropic.chat import ChatAnthropic  # type: ignore
            llm_kwargs: dict[str, Any] = {
                "model": self._config.browser_model,
                "api_key": self._config.anthropic_api_key,
            }
            if self._config.anthropic_base_url:
                llm_kwargs["base_url"] = self._config.anthropic_base_url
            llm = ChatAnthropic(**llm_kwargs)

        profile = BrowserProfile(**self._browser_profile_kwargs())
        agent = Agent(
            task=task,
            llm=llm,
            browser_profile=profile,
            use_vision=self._resolve_use_vision(),
            max_failures=self._config.max_retries + 1,
        )
        history = agent.run_sync(max_steps=self._config.max_steps_browser)

        is_done, content = self._parse_history(history)
        return {
            "success": is_done,
            "content": content,
            "error": None if is_done else "El agente de navegador no completo la tarea",
        }

    def _browser_profile_kwargs(self) -> dict[str, Any]:
        kwargs: dict[str, Any] = {
            "headless": self._config.browser_headless,
        }

        if self._config.browser_cdp_url:
            kwargs["cdp_url"] = self._config.browser_cdp_url
            return kwargs

        if self._config.browser_channel:
            kwargs["channel"] = self._config.browser_channel
        if self._config.browser_executable_path:
            kwargs["executable_path"] = self._config.browser_executable_path
        if self._config.browser_user_data_dir:
            kwargs["user_data_dir"] = self._config.browser_user_data_dir
        if self._config.browser_profile_directory:
            kwargs["profile_directory"] = self._config.browser_profile_directory

        return kwargs

    def _parse_history(self, history) -> tuple[bool, str | None]:
        """Extrae is_done y content del AgentHistoryList de forma defensiva."""
        try:
            items = history.history
            if not items:
                return False, None
            last = items[-1]
            results = getattr(last, "result", None) or []
            is_done = any(getattr(result, "is_done", False) for result in results)
            content = next(
                (
                    getattr(result, "extracted_content", None)
                    for result in results
                    if getattr(result, "extracted_content", None)
                ),
                None,
            )
            return is_done, content
        except Exception:
            return bool(getattr(history, "history", [])), None

    def _check_allowlist(self) -> None:
        if "browser" not in self._config.action_allowlist:
            raise RuntimeError("El adaptador 'browser' no esta en ACTION_ALLOWLIST.")

    def _ensure_cdp_ready(self) -> None:
        if not self._config.browser_cdp_url:
            return
        if self._is_cdp_available():
            return

        command = self._build_edge_bootstrap_command()
        if self._edge_is_running():
            raise RuntimeError(
                "Edge ya esta abierto sin CDP en el puerto configurado. "
                "Cierra todas las ventanas de Edge y vuelve a ejecutar la tarea. "
                f"Comando requerido en PowerShell: {command}"
            )

        self._launch_edge_bootstrap_command(command)
        if self._wait_for_cdp():
            return

        raise RuntimeError(
            "No pude conectar a Edge por CDP despues de intentar abrirlo. "
            f"Comando usado en PowerShell: {command}"
        )

    def _build_edge_bootstrap_command(self) -> str:
        edge_path = self._resolve_edge_executable()
        port = self._cdp_port()
        profile = self._config.browser_profile_directory or "Default"
        start_url = self._config.browser_cdp_bootstrap_url
        return (
            f'& "{edge_path}" '
            f"--remote-debugging-port={port} "
            f"--profile-directory={profile} "
            f'"{start_url}"'
        )

    def _resolve_edge_executable(self) -> str:
        if self._config.browser_executable_path:
            return self._config.browser_executable_path

        candidates = (
            r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
            r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
        )
        for candidate in candidates:
            try:
                with open(candidate, "rb"):
                    return candidate
            except OSError:
                continue

        raise RuntimeError(
            "No encontre msedge.exe. Define BROWSER_EXECUTABLE_PATH en worker-core/.env."
        )

    def _cdp_port(self) -> int:
        if not self._config.browser_cdp_url:
            raise RuntimeError("BROWSER_CDP_URL no esta definida.")
        parsed = urlparse(self._config.browser_cdp_url)
        if parsed.port is None:
            raise RuntimeError(
                f"No pude extraer el puerto desde BROWSER_CDP_URL={self._config.browser_cdp_url!r}."
            )
        return parsed.port

    def _cdp_version_url(self) -> str:
        if not self._config.browser_cdp_url:
            raise RuntimeError("BROWSER_CDP_URL no esta definida.")
        return self._config.browser_cdp_url.rstrip("/") + "/json/version"

    def _is_cdp_available(self) -> bool:
        try:
            with request.urlopen(self._cdp_version_url(), timeout=1.5) as response:
                return response.status == 200
        except (error.URLError, TimeoutError, ValueError):
            return False

    def _wait_for_cdp(self, timeout_s: float = 15.0) -> bool:
        deadline = time.time() + timeout_s
        while time.time() < deadline:
            if self._is_cdp_available():
                return True
            time.sleep(0.5)
        return False

    def _edge_is_running(self) -> bool:
        result = subprocess.run(
            [
                "powershell",
                "-NoProfile",
                "-Command",
                "@(Get-Process msedge -ErrorAction SilentlyContinue).Count",
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        return result.returncode == 0 and result.stdout.strip() not in {"", "0"}

    def _launch_edge_bootstrap_command(self, command: str) -> None:
        subprocess.Popen(
            [
                "powershell",
                "-NoProfile",
                "-Command",
                command,
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

    def _resolve_use_vision(self) -> bool:
        configured = self._config.browser_use_vision
        if configured != "auto":
            return configured

        model = self._config.browser_model.strip().lower()
        return any(hint in model for hint in self._VISION_MODEL_HINTS)

    def _maybe_run_direct_flow(self, task: str) -> dict[str, Any] | None:
        if not self._is_freepik_generation_task(task):
            return None

        prompt = self._extract_freepik_prompt(task)
        if not prompt:
            return None

        self._logger.info(
            "browser_adapter_direct_freepik",
            extra={"adapter": "browser", "site": "freepik", "mode": "one-shot"},
        )
        return asyncio.run(self._run_freepik_generation(prompt))

    def _is_freepik_generation_task(self, task: str) -> bool:
        normalized = task.lower()
        if "freepik" not in normalized and "pikaso" not in normalized:
            return False

        has_prompt_instruction = "prompt" in normalized or "campo principal" in normalized
        has_generate_instruction = any(
            keyword in normalized
            for keyword in ("generate", "genera", "generar", "crear la imagen", "crea la imagen")
        )
        return has_prompt_instruction and has_generate_instruction

    def _extract_freepik_prompt(self, task: str) -> str | None:
        for pattern in self._FREEPIK_PROMPT_PATTERNS:
            match = re.search(pattern, task, flags=re.IGNORECASE | re.DOTALL)
            if match:
                prompt = match.group("prompt").strip()
                if prompt:
                    return prompt
        return None

    async def _run_freepik_generation(self, prompt: str) -> dict[str, Any]:
        from browser_use import BrowserSession  # type: ignore

        browser = BrowserSession(**self._browser_session_kwargs())
        try:
            await browser.start()
            page = await browser.new_page(self._FREEPIK_URL)
            await self._wait_for_freepik_dom(page)

            if await self._freepik_generation_in_progress(page):
                return {
                    "success": True,
                    "content": "Freepik ya estaba generando una imagen; no hice otro submit.",
                    "error": None,
                }

            await self._fill_freepik_prompt(page, prompt)
            await asyncio.sleep(1.0)

            button = await self._find_freepik_generate_button(page)
            await button.click()

            started = await self._wait_for_freepik_generation_started(page)
            if started:
                return {
                    "success": True,
                    "content": "Freepik acepto el prompt y empezo a generar la imagen.",
                    "error": None,
                }

            return {
                "success": True,
                "content": "Hice click en Generate una sola vez, pero no confirme el estado de progreso a tiempo.",
                "error": None,
            }
        finally:
            await browser.close()

    def _browser_session_kwargs(self) -> dict[str, Any]:
        kwargs: dict[str, Any] = {
            "allowed_domains": ["freepik.com", "www.freepik.com"],
            "keep_alive": True,
        }

        if self._config.browser_cdp_url:
            kwargs["cdp_url"] = self._config.browser_cdp_url
            return kwargs

        kwargs["headless"] = self._config.browser_headless
        if self._config.browser_channel:
            kwargs["channel"] = self._config.browser_channel
        if self._config.browser_executable_path:
            kwargs["executable_path"] = self._config.browser_executable_path
        if self._config.browser_user_data_dir:
            kwargs["user_data_dir"] = self._config.browser_user_data_dir
        if self._config.browser_profile_directory:
            kwargs["profile_directory"] = self._config.browser_profile_directory
        return kwargs

    async def _wait_for_freepik_dom(self, page, timeout_s: float = 45.0) -> None:
        deadline = time.time() + timeout_s
        while time.time() < deadline:
            raw = await page.evaluate(
                """() => JSON.stringify({
                    readyState: document.readyState,
                    bodyText: (document.body?.innerText || '').slice(0, 3000),
                    textareas: document.querySelectorAll('textarea').length,
                    inputs: document.querySelectorAll('input').length,
                    buttons: document.querySelectorAll('button').length
                })"""
            )
            snapshot = json.loads(raw)
            body = snapshot["bodyText"].lower()
            if "access denied" in body or "\n403\n" in body:
                raise RuntimeError("Freepik devolvio Access Denied / 403 desde este entorno.")
            if snapshot["readyState"] == "complete" and (
                snapshot["textareas"] or snapshot["inputs"] or snapshot["buttons"]
            ):
                return
            await asyncio.sleep(1.5)

        raise RuntimeError("La pagina de Freepik no expuso controles interactivos a tiempo.")

    async def _extract_element_metadata(self, element) -> dict[str, Any]:
        raw = await element.evaluate(
            """() => JSON.stringify({
                text: (this.innerText || this.textContent || '').trim(),
                placeholder: this.getAttribute('placeholder'),
                ariaLabel: this.getAttribute('aria-label'),
                title: this.getAttribute('title'),
                className: this.className || '',
                tagName: this.tagName,
                type: this.getAttribute('type'),
                visible: (() => {
                    const style = window.getComputedStyle(this);
                    const rect = this.getBoundingClientRect();
                    return style.display !== 'none'
                        && style.visibility !== 'hidden'
                        && rect.width > 0
                        && rect.height > 0;
                })(),
                disabled: Boolean(this.disabled || this.getAttribute('aria-disabled') === 'true'),
                contentEditable: this.getAttribute('contenteditable')
            })"""
        )
        return json.loads(raw)

    async def _find_freepik_prompt_element(self, page):
        selectors = (
            "textarea",
            "input[type='text']",
            "[role='textbox']",
            "[contenteditable='true']",
            "div[contenteditable='true']",
        )
        preferred_terms = ("prompt", "describe", "idea", "image", "scene", "what", "text")

        fallback = None
        for selector in selectors:
            for element in await page.get_elements_by_css_selector(selector):
                meta = await self._extract_element_metadata(element)
                if not meta["visible"] or meta["disabled"]:
                    continue
                haystack = " ".join(
                    str(meta.get(key) or "")
                    for key in ("text", "placeholder", "ariaLabel", "title", "className", "tagName")
                ).lower()
                if any(term in haystack for term in preferred_terms):
                    return element, meta
                if fallback is None:
                    fallback = (element, meta)

        if fallback is not None:
            return fallback

        raise RuntimeError("No encontre un campo editable para el prompt en Freepik.")

    async def _fill_freepik_prompt(self, page, prompt: str) -> None:
        element, meta = await self._find_freepik_prompt_element(page)
        tag_name = str(meta["tagName"]).lower()
        content_editable = str(meta.get("contentEditable") or "").lower() == "true"

        if tag_name in {"textarea", "input"} and not content_editable:
            await element.fill(prompt)
            return

        await element.click()
        await element.evaluate(
            """(value) => {
                this.focus();
                if ('value' in this) {
                    this.value = value;
                } else {
                    this.textContent = value;
                }
                this.dispatchEvent(new Event('input', { bubbles: true }));
                this.dispatchEvent(new Event('change', { bubbles: true }));
            }""",
            prompt,
        )

    async def _find_freepik_generate_button(self, page):
        candidates = await page.get_elements_by_css_selector("button, [role='button']")
        positive_terms = ("generate", "crear", "create", "go")

        for element in candidates:
            meta = await self._extract_element_metadata(element)
            if not meta["visible"] or meta["disabled"]:
                continue
            haystack = " ".join(
                str(meta.get(key) or "") for key in ("text", "ariaLabel", "title", "className")
            ).lower()
            if any(term in haystack for term in positive_terms):
                return element

        raise RuntimeError("No encontre un boton Generate/Create habilitado en Freepik.")

    async def _freepik_generation_in_progress(self, page) -> bool:
        raw = await page.evaluate(
            """() => JSON.stringify({
                bodyText: (document.body?.innerText || '').slice(0, 4000)
            })"""
        )
        body = json.loads(raw)["bodyText"].lower()
        return "generating" in body or "creating..." in body or "processing" in body

    async def _wait_for_freepik_generation_started(self, page, timeout_s: float = 15.0) -> bool:
        deadline = time.time() + timeout_s
        while time.time() < deadline:
            raw = await page.evaluate(
                """() => JSON.stringify({
                    bodyText: (document.body?.innerText || '').slice(0, 4000),
                    hasBusy: Boolean(document.querySelector('[aria-busy="true"]')),
                    disabledButtons: Array.from(document.querySelectorAll('button,[role="button"]'))
                        .some(el => Boolean(el.disabled || el.getAttribute('aria-disabled') === 'true'))
                })"""
            )
            snapshot = json.loads(raw)
            body = snapshot["bodyText"].lower()
            if (
                "generating" in body
                or "creating..." in body
                or "processing" in body
                or snapshot["hasBusy"]
                or snapshot["disabledButtons"]
            ):
                return True
            await asyncio.sleep(1.0)
        return False
