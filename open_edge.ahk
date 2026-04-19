#NoEnv
SetTitleMatchMode, 2
Run, msedge.exe
WinWait, ahk_exe msedge.exe, , 5
if !ErrorLevel
    WinActivate, ahk_exe msedge.exe
