; Instalador do NaView para Windows (Inno Setup 6). Montado pelo GitHub Actions
; (.github/workflows/windows.yml) a partir da pasta dist\NaView do PyInstaller.
;
; Instala só para o usuário atual, sem pedir senha de administrador, em
; %LOCALAPPDATA%\Programs\NaView, com atalho no menu Iniciar.

#ifndef Versao
  #define Versao "0"
#endif

[Setup]
AppId={{6F1E0D52-3C1B-4B7A-9C55-5A0C8E1B7A11}
AppName=NaView
AppVersion={#Versao}
AppPublisher=NaView
DefaultDirName={localappdata}\Programs\NaView
DefaultGroupName=NaView
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
OutputDir=..\saida
OutputBaseFilename=NaView-instalador
SetupIconFile=icone.ico
UninstallDisplayIcon={app}\NaView.exe
Compression=lzma2/max
SolidCompression=yes
WizardStyle=modern
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
CloseApplications=yes

[Languages]
Name: "ptbr"; MessagesFile: "compiler:Languages\BrazilianPortuguese.isl"

[Tasks]
Name: "atalho"; Description: "Criar atalho na área de trabalho"; Flags: unchecked

[Files]
Source: "..\dist\NaView\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\NaView"; Filename: "{app}\NaView.exe"
Name: "{userdesktop}\NaView"; Filename: "{app}\NaView.exe"; Tasks: atalho

[Run]
Filename: "{app}\NaView.exe"; Description: "Abrir o NaView agora"; Flags: nowait postinstall skipifsilent
