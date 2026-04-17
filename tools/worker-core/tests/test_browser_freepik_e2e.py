from __future__ import annotations

import asyncio
import json
import os
import random
import sys
import uuid

import pytest


pytestmark = [pytest.mark.browser_e2e]


FREEPIK_URL = "https://www.freepik.com/pikaso/ai-image-generator"


def _require_opt_in() -> None:
    if os.environ.get("RUN_FREEPIK_BROWSER_E2E") != "1":
        pytest.skip(
            "Test externo deshabilitado. "
            "Usa RUN_FREEPIK_BROWSER_E2E=1 para ejecutarlo."
        )


def _headless_from_env() -> bool:
    return os.environ.get("BROWSER_E2E_HEADLESS", "0") == "1"


def _browser_cdp_url_from_env() -> str | None:
    return (
        os.environ.get("FREEPIK_BROWSER_CDP_URL")
        or os.environ.get("BROWSER_CDP_URL")
        or None
    )


def _build_random_prompt() -> str:
    subjects = ["robot gardener", "floating city", "retro spaceship", "ancient library"]
    styles = ["cinematic", "isometric", "watercolor", "photorealistic"]
    moods = ["golden hour", "soft neon", "stormy sky", "warm studio light"]
    token = uuid.uuid4().hex[:8]
    return (
        f"{random.choice(subjects)}, {random.choice(styles)}, "
        f"{random.choice(moods)}, highly detailed, test run {token}"
    )


async def _wait_for_dom(page, timeout_s: float = 45.0) -> None:
    deadline = asyncio.get_running_loop().time() + timeout_s
    while asyncio.get_running_loop().time() < deadline:
        raw = await page.evaluate(
            """() => JSON.stringify({
                readyState: document.readyState,
                bodyText: (document.body?.innerText || '').slice(0, 2000),
                textareas: document.querySelectorAll('textarea').length,
                inputs: document.querySelectorAll('input').length,
                buttons: document.querySelectorAll('button').length
            })"""
        )
        snapshot = json.loads(raw)
        body = snapshot["bodyText"].lower()
        if "access denied" in body or "\n403\n" in body or body.startswith("error\n403"):
            pytest.skip("Freepik bloqueo el acceso desde este entorno (HTTP 403 / Access denied).")
        if snapshot["readyState"] == "complete" and (
            snapshot["textareas"] or snapshot["inputs"] or snapshot["buttons"]
        ):
            return
        await asyncio.sleep(2)
    raise AssertionError("La pagina de Freepik no expuso controles interactivos a tiempo.")


async def _extract_element_metadata(element) -> dict[str, object]:
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


async def _find_prompt_element(page):
    selectors = [
        "textarea",
        "input[type='text']",
        "[role='textbox']",
        "[contenteditable='true']",
        "div[contenteditable='true']",
    ]
    preferred_terms = (
        "prompt",
        "describe",
        "idea",
        "image",
        "scene",
        "what",
        "text",
    )

    fallback = None
    for selector in selectors:
        for element in await page.get_elements_by_css_selector(selector):
            meta = await _extract_element_metadata(element)
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

    raise AssertionError("No encontre un campo editable para el prompt.")


async def _fill_prompt(page, prompt: str) -> None:
    element, meta = await _find_prompt_element(page)
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


async def _find_generate_button(page):
    candidates = await page.get_elements_by_css_selector("button, [role='button']")
    positive_terms = ("generate", "crear", "create", "go")

    for element in candidates:
        meta = await _extract_element_metadata(element)
        if not meta["visible"] or meta["disabled"]:
            continue
        haystack = " ".join(
            str(meta.get(key) or "") for key in ("text", "ariaLabel", "title", "className")
        ).lower()
        if any(term in haystack for term in positive_terms):
            return element, meta

    raise AssertionError("No encontre un boton Generate/Create habilitado.")


async def _run_freepik_flow() -> None:
    if sys.version_info < (3, 11):
        pytest.skip("browser-use requiere Python 3.11 o superior.")

    browser_use = pytest.importorskip("browser_use")
    BrowserSession = browser_use.BrowserSession

    cdp_url = _browser_cdp_url_from_env()
    browser_kwargs = {
        "allowed_domains": ["freepik.com", "www.freepik.com"],
    }
    if cdp_url:
        browser_kwargs["cdp_url"] = cdp_url
    else:
        browser_kwargs["headless"] = _headless_from_env()
        browser_kwargs["channel"] = "msedge"

    browser = BrowserSession(**browser_kwargs)
    prompt = _build_random_prompt()

    try:
        await browser.start()
        page = await browser.new_page(FREEPIK_URL)
        await _wait_for_dom(page)
        await _fill_prompt(page, prompt)
        await asyncio.sleep(1.5)

        echoed_prompt = await page.evaluate(
            """() => {
                const editable = document.querySelector('textarea, input[type="text"], [role="textbox"], [contenteditable="true"]');
                if (!editable) return '';
                if ('value' in editable) return editable.value || '';
                return editable.textContent || '';
            }"""
        )
        assert prompt.split(",")[0] in str(echoed_prompt)

        button, _ = await _find_generate_button(page)
        await button.click()
        await asyncio.sleep(5)
    finally:
        await browser.kill()


def test_freepik_pikaso_can_fill_prompt_and_click_generate() -> None:
    _require_opt_in()
    asyncio.run(_run_freepik_flow())
