from __future__ import annotations

from app.config import Config
from app.logger import get_logger


class WindowsAdapter:
    """Adaptador para windows-use. Importa windows_use de forma lazy
    para no fallar en sistemas sin pywin32/COM instalado."""

    def __init__(self, config: Config) -> None:
        self._config = config
        self._logger = get_logger("windows_adapter", config.logs_dir)

    def run(self, task: str) -> dict:
        """Ejecuta una tarea de automatización de escritorio Windows.

        Returns:
            {"success": bool, "content": str|None, "error": str|None}
        """
        self._check_allowlist()

        try:
            from windows_use.agent import Agent  # type: ignore
            from windows_use.agent.service import Browser  # type: ignore
            
            # Intentar usar Gemini si la key está presente
            gemini_key = getattr(self._config, 'gemini_api_key', None)
            if gemini_key:
                self._logger.info("Usando Gemini SECRETO como cerebro de Windows", extra={"model": "gemini-2.0-flash"})
                from windows_use.providers.google import ChatGoogle # type: ignore
                llm = ChatGoogle(model="gemini-2.0-flash", api_key=gemini_key)
            else:
                from windows_use.providers.anthropic import ChatAnthropic  # type: ignore
                llm_kwargs: dict = {
                    "model": self._config.windows_model,
                    "api_key": self._config.anthropic_api_key,
                }
                if self._config.anthropic_base_url:
                    llm_kwargs["base_url"] = self._config.anthropic_base_url
                llm = ChatAnthropic(**llm_kwargs)
        except ImportError as exc:
            raise ImportError(
                "windows-use no está instalado o faltan dependencias (pywin32, comtypes). "
                f"Detalle: {exc}"
            ) from exc

        self._logger.info(
            "windows_adapter_run",
            extra={"adapter": "windows", "using_gemini": bool(gemini_key)},
        )

        agent = Agent(
            llm=llm,
            browser=Browser.EDGE,
            use_vision=False,
            max_steps=self._config.max_steps_windows,
            log_to_console=False,
        )
        result = agent.invoke(task)
        return {
            "success": bool(result.is_done),
            "content": result.content,
            "error": result.error,
        }

    def _check_allowlist(self) -> None:
        if "windows" not in self._config.action_allowlist:
            raise RuntimeError(
                "El adaptador 'windows' no está en ACTION_ALLOWLIST. "
                "Agrégalo a la variable de entorno para habilitarlo."
            )
