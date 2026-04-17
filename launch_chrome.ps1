$wshell = New-Object -ComObject WScript.Shell
# Abrir Chrome en la búsqueda de gatos
Start-Process "chrome.exe" "https://www.google.com/search?q=gato&tbm=isch"
Start-Sleep -Seconds 5

# Intentar enfocar y maximizar (Alt+Espacio, luego x)
$wshell.AppActivate("Google Chrome")
Start-Sleep -Seconds 1
$wshell.SendKeys("% x") 
Start-Sleep -Seconds 1
