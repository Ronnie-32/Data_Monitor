Set shell = CreateObject("WScript.Shell")
folder = CreateObject("Scripting.FileSystemObject").GetParentFolderName(WScript.ScriptFullName)
quote = Chr(34)
command = "pwsh.exe -NoLogo -NoProfile -NonInteractive -File " & quote & folder & "\start.ps1" & quote
shell.Run command, 0, False
