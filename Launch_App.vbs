Set WshShell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")
strPath = fso.GetParentFolderName(WScript.ScriptFullName)
WshShell.CurrentDirectory = strPath
WshShell.Run """C:\Users\manan\AppData\Local\Programs\Python\Python312\pythonw.exe"" """ & strPath & "\main.py""", 0, False
