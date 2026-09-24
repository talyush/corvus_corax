' Corvus Corax - Ollama otomatik baslatma (gizli, pencere acmadan)
' Windows oturum acilisinda calisir. Port zaten aciksa ollama_start.bat
' hicbir sey yapmadan cikar; kapaliysa ollama serve baslatir.
Set shell = CreateObject("WScript.Shell")
shell.Run """C:\Users\deneme\OneDrive\Masaüstü\corvus_corax\scripts\ollama_start.bat""", 0, False
Set shell = Nothing
