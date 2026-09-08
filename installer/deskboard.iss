; DeskBoard standard per-user Windows installer.
; Build the onedir payload first with scripts\build.ps1.

#ifndef AppVersion
#define AppVersion "0.1.0"
#endif

[Setup]
AppId={{E8B7E1E3-44E4-4AA7-9E19-7E3F9D2AF3D2}
AppName=DeskBoard
AppVersion={#AppVersion}
AppPublisher=DeskBoard
SetupIconFile=..\src\deskboard\assets\deskboard-icon.ico
DefaultDirName={localappdata}\Programs\DeskBoard
DefaultGroupName=DeskBoard
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
OutputDir=..\dist\installer
OutputBaseFilename=DeskBoard-Setup-{#AppVersion}
Compression=lzma2/max
SolidCompression=yes
WizardStyle=modern
UninstallDisplayName=DeskBoard
UninstallDisplayIcon={app}\DeskBoard.exe
SetupLogging=yes

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Create a &desktop shortcut"; GroupDescription: "Additional icons:"; Flags: unchecked

[Files]
Source: "..\dist\DeskBoard\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\DeskBoard"; Filename: "{app}\DeskBoard.exe"
Name: "{autodesktop}\DeskBoard"; Filename: "{app}\DeskBoard.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\DeskBoard.exe"; Description: "Launch DeskBoard"; Flags: nowait postinstall skipifsilent

; The uninstaller deliberately leaves %LOCALAPPDATA%\DeskBoard untouched.
; The user's SQLite database and logs remain after uninstall unless the user removes
; them explicitly.
