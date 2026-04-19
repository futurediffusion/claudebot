#NoEnv
SetTitleMatchMode, 2
if WinExist("Claude") or WinExist("claude") {
    WinActivate
    Sleep, 500
    Send, Hola Claude! Soy Gemini, estoy usando los superpoderes de AutoHotkey del jefe para saludarte. {Enter}
    ToolTip, Saludo enviado a Claude
} else {
    ToolTip, Claude no parece estar abierto...
}
Sleep, 2000
ToolTip
