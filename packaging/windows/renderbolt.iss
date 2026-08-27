#define MyAppName "Renderbolt"
#define MyAppVersion "1.0.7"
#define MyAppPublisher "JMHBM"
#define MyAppURL "https://github.com/JMHBM/Renderbolt"
#define MyAppExeName "Renderbolt.exe"
#ifndef DistDir
#define DistDir "dist\Renderbolt"
#endif

[Setup]
AppId={{B7E4C31A-8F2D-4C9E-9A61-7A1C0E107001}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}/releases
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
LicenseFile=..\..\LICENSE
OutputDir=..\..\public\downloads
OutputBaseFilename=Renderbolt-1.0.7-setup
SetupIconFile=renderbolt.ico
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
ArchitecturesAllowed=x64
ArchitecturesInstallIn64BitMode=x64
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog
UninstallDisplayIcon={app}\{#MyAppExeName}
MinVersion=10.0
InfoBeforeFile=readme-installer.txt

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Create a desktop icon"; GroupDescription: "Additional icons:"

[Files]
Source: "{#DistDir}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{autoprograms}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Launch Renderbolt"; Flags: nowait postinstall skipifsilent
