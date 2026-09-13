Set shell = CreateObject("WScript.Shell")
project = "C:\data\local-personal-toolbox"
pythonw = project & "\.venv\Scripts\pythonw.exe"

If CreateObject("Scripting.FileSystemObject").FileExists(pythonw) Then
    shell.CurrentDirectory = project
    command = Chr(34) & pythonw & Chr(34) & " " & Chr(34) & project & "\main.py" & Chr(34)
    shell.Run command, 0, False
Else
    command = "cmd /c " & Chr(34) & project & "\run.bat" & Chr(34)
    shell.Run command, 1, True
End If
