#define AppVersion "1.0.0"
#define PortableDir "dist\Downloader"
#define AppIcon "_internal\customtkinter\assets\icons\CustomTkinter_icon_Windows.ico"

[Setup]
AppId={{E839CBFF-6B44-4394-BAA8-6ECB715DC890}
AppName=Downloader
AppVersion={#AppVersion}
DefaultDirName={localappdata}\Programs\Downloader
DisableDirPage=yes
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
ArchitecturesAllowed=x64os
ArchitecturesInstallIn64BitMode=x64os
MinVersion=10.0
UninstallDisplayIcon={app}\Downloader.exe
CloseApplications=yes
RestartApplications=no
OutputDir=dist
OutputBaseFilename=Downloader-Setup-{#AppVersion}-x64
SetupIconFile={#PortableDir}\{#AppIcon}
Compression=lzma2
SolidCompression=yes
WizardStyle=modern

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "{#PortableDir}\Downloader.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#PortableDir}\DownloaderWorker.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#PortableDir}\_internal\*"; DestDir: "{app}\_internal"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{userprograms}\Downloader"; Filename: "{app}\Downloader.exe"; WorkingDir: "{app}"; IconFilename: "{app}\{#AppIcon}"
Name: "{userdesktop}\Downloader"; Filename: "{app}\Downloader.exe"; WorkingDir: "{app}"; IconFilename: "{app}\{#AppIcon}"; Tasks: desktopicon

[Run]
Filename: "{app}\Downloader.exe"; Description: "{cm:LaunchProgram,Downloader}"; Flags: nowait postinstall skipifsilent
