[Setup]
AppName=البوصلة
AppVersion=1.5.2
DefaultDirName={sd}\البوصلة
OutputDir=.\Output
OutputBaseFilename=البوصلة
Compression=lzma2
SolidCompression=yes

[Files]
; Install the main executable (built from login.py) to the application folder.
Source: ".\Dist\AlBousala.exe"; DestDir: "{app}"; Flags: ignoreversion

; Copy the entire icons folder to {app}\icons.
Source: ".\Resources\icons\*"; DestDir: "{app}\icons"; Flags: ignoreversion recursesubdirs

; Copy all sound files from the resources\sounds folder to {app}\sounds.
Source: ".\Resources\sounds\*"; DestDir: "{app}\sounds"; Flags: ignoreversion recursesubdirs

; Copy additional resources to the application folder.
Source: ".\Resources\background.png"; DestDir: "{app}"; Flags: ignoreversion
Source: ".\Resources\Cairo.ttf"; DestDir: "{app}"; Flags: ignoreversion
Source: ".\Resources\offline_employees_cache.json"; DestDir: "{app}"; Flags: ignoreversion
Source: ".\Resources\offline_shipments_cache.json"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
; Create a desktop shortcut that uses the external icon from {app}\icons.
Name: "{userdesktop}\البوصلة"; Filename: "{app}\البوصلة.exe"; IconFilename: "{app}\icons\alien_icon.ico"
Name: "{group}\البوصلة"; Filename: "{app}\البوصلة.exe"
