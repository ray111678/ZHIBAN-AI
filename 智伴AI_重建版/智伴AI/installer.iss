#define MyAppName "智伴 AI"
#define MyAppVersion "1.0.0"
#define MyAppExeName "智伴AI.exe"
[Setup]
AppId={{8E5AC9F7-3A7A-4E9A-9D1A-7B5A1C0D9F11}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
DefaultDirName={autopf}\ZhiBanAI
DefaultGroupName={#MyAppName}
OutputDir=installer_output
OutputBaseFilename=智伴AI_Windows安装程序
Compression=lzma2
SolidCompression=yes
ArchitecturesInstallIn64BitMode=x64
PrivilegesRequired=lowest
UninstallDisplayIcon={app}\{#MyAppExeName}
[Files]
Source: "dist\智伴AI\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
[Icons]
Name: "{group}\智伴 AI"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\智伴 AI"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon
[Tasks]
Name: "desktopicon"; Description: "创建桌面快捷方式"; GroupDescription: "附加快捷方式："; Flags: unchecked
[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "启动智伴 AI"; Flags: postinstall nowait skipifsilent
