; ============================================================
;  Division 2 — DPS Tracker
;  Script Inno Setup 6.x
;  Génère : Division2_DPS_Tracker_Setup.exe
;
;  AVANT DE COMPILER :
;  1) Placez vos fichiers dans le dossier "app\"
;  2) Téléchargez Python et Tesseract dans "redist\"
;     → Ajustez PYTHON_EXE ci-dessous avec le nom exact
; ============================================================

; ── Nom exact des installeurs dans redist\ ────────────────────────────────
; Changez ces deux lignes pour correspondre à vos fichiers téléchargés :
#define PYTHON_EXE   "python-3.12.10-amd64.exe"
#define TESSERACT_EXE "tesseract-ocr-w64-setup-5.5.0.20241111.exe"

; ── Métadonnées de l'application ─────────────────────────────────────────
#define AppName      "Division 2 DPS Tracker"
#define AppVersion   "1.0"
#define AppPublisher "Division 2 Tools"

[Setup]
AppId={{A3F2B8C1-4D7E-4F2A-9C3B-1E5F8D2A6B4C}
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisherURL=https://github.com/UB-Mannheim/tesseract/wiki
AppSupportURL=https://github.com/UB-Mannheim/tesseract/wiki
DefaultDirName={autopf}\Division2DPSTracker
DefaultGroupName={#AppName}
AllowNoIcons=no
PrivilegesRequired=admin
OutputDir=output
OutputBaseFilename=Division2_DPS_Tracker_Setup
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
WizardResizable=no
UninstallDisplayName={#AppName}
VersionInfoVersion={#AppVersion}
VersionInfoDescription={#AppName} Installer

[Languages]
Name: "french"; MessagesFile: "compiler:Languages\French.isl"

[Messages]
WelcomeLabel1=Bienvenue dans l'assistant d'installation de%n{#AppName}
WelcomeLabel2=Cet assistant va installer {#AppName} sur votre ordinateur.%n%nL'installation va automatiquement :%n  ✓  Installer Python 3.12 (si absent de votre PC)%n  ✓  Installer Tesseract OCR (moteur de reconnaissance de texte)%n  ✓  Installer les bibliothèques Python nécessaires%n  ✓  Créer les raccourcis dans le menu Démarrer%n%nAucune connaissance technique n'est requise.%nCliquez sur Suivant pour continuer.

[Tasks]
Name: "desktopicon"; Description: "Créer une icône sur le &Bureau"; GroupDescription: "Icônes supplémentaires :"

[Files]
; ── Fichiers de l'application ────────────────────────────────────────────
Source: "app\server.py";    DestDir: "{app}"; Flags: ignoreversion
Source: "app\index.html";   DestDir: "{app}"; Flags: ignoreversion
Source: "app\lancer.bat";   DestDir: "{app}"; Flags: ignoreversion
Source: "install_deps.bat"; DestDir: "{app}"; Flags: ignoreversion deleteafterinstall

; ── Installeurs tiers ────────────────────────────────────────────────────
Source: "redist\{#PYTHON_EXE}";    DestDir: "{tmp}"; Flags: deleteafterinstall; Check: NeedsPython
Source: "redist\{#TESSERACT_EXE}"; DestDir: "{tmp}"; Flags: deleteafterinstall; Check: NeedsTesseract

[Icons]
; ── Menu Démarrer ─────────────────────────────────────────────────────────
Name: "{group}\{#AppName}"; Filename: "{app}\lancer.bat"; WorkingDir: "{app}"; Comment: "Lancer le tracker DPS pour Division 2"
Name: "{group}\Désinstaller {#AppName}"; Filename: "{uninstallexe}"

; ── Bureau (optionnel) ────────────────────────────────────────────────────
Name: "{autodesktop}\{#AppName}"; Filename: "{app}\lancer.bat"; WorkingDir: "{app}"; Tasks: desktopicon; Comment: "Lancer le tracker DPS pour Division 2"

[Run]
; ── Étape 1 : Python (silencieux, si absent) ──────────────────────────────
Filename: "{tmp}\{#PYTHON_EXE}"; Parameters: "/quiet InstallAllUsers=0 PrependPath=1 Include_pip=1 Include_tcltk=0"; StatusMsg: "Installation de Python 3.12 (peut prendre 1-2 minutes)..."; Flags: waituntilterminated; Check: NeedsPython

; ── Étape 2 : Tesseract OCR (silencieux, si absent) ───────────────────────
Filename: "{tmp}\{#TESSERACT_EXE}"; Parameters: "/S"; StatusMsg: "Installation de Tesseract OCR..."; Flags: waituntilterminated; Check: NeedsTesseract

; ── Étape 3 : Dépendances Python via pip ──────────────────────────────────
Filename: "cmd.exe"; Parameters: "/c call ""{app}\install_deps.bat"""; WorkingDir: "{app}"; StatusMsg: "Installation des bibliothèques Python (Flask, OpenCV, Pillow...)..."; Flags: waituntilterminated runhidden

; ── Étape 4 : Proposer de lancer (post-install) ───────────────────────────
Filename: "{app}\lancer.bat"; Description: "Lancer {#AppName} maintenant"; Flags: nowait postinstall skipifsilent shellexec

[Code]
// ─────────────────────────────────────────────────────────────────────────────
//  Détection Python
// ─────────────────────────────────────────────────────────────────────────────
function FindPython(): String;
var
  Candidates: TArrayOfString;
  i: Integer;
begin
  Result := '';
  SetArrayLength(Candidates, 10);
  Candidates[0] := ExpandConstant('{localappdata}') + '\Programs\Python\Python312\python.exe';
  Candidates[1] := ExpandConstant('{localappdata}') + '\Programs\Python\Python311\python.exe';
  Candidates[2] := ExpandConstant('{localappdata}') + '\Programs\Python\Python310\python.exe';
  Candidates[3] := ExpandConstant('{localappdata}') + '\Programs\Python\Python39\python.exe';
  Candidates[4] := ExpandConstant('{pf}') + '\Python312\python.exe';
  Candidates[5] := ExpandConstant('{pf}') + '\Python311\python.exe';
  Candidates[6] := ExpandConstant('{pf}') + '\Python310\python.exe';
  Candidates[7] := ExpandConstant('{pf}') + '\Python39\python.exe';
  Candidates[8] := ExpandConstant('{pf32}') + '\Python312\python.exe';
  Candidates[9] := ExpandConstant('{pf32}') + '\Python311\python.exe';

  for i := 0 to GetArrayLength(Candidates) - 1 do
    if FileExists(Candidates[i]) then
    begin
      Result := Candidates[i];
      Exit;
    end;
end;

function NeedsPython(): Boolean;
begin
  Result := (FindPython() = '');
end;

// ─────────────────────────────────────────────────────────────────────────────
//  Détection Tesseract
// ─────────────────────────────────────────────────────────────────────────────
function FindTesseract(): String;
var
  Candidates: TArrayOfString;
  i: Integer;
  RegPath: String;
begin
  Result := '';
  SetArrayLength(Candidates, 5);
  Candidates[0] := ExpandConstant('{pf}') + '\Tesseract-OCR\tesseract.exe';
  Candidates[1] := ExpandConstant('{pf32}') + '\Tesseract-OCR\tesseract.exe';
  Candidates[2] := ExpandConstant('{localappdata}') + '\Programs\Tesseract-OCR\tesseract.exe';
  Candidates[3] := ExpandConstant('{localappdata}') + '\Tesseract-OCR\tesseract.exe';
  Candidates[4] := 'C:\Tesseract-OCR\tesseract.exe';

  for i := 0 to GetArrayLength(Candidates) - 1 do
    if FileExists(Candidates[i]) then
    begin
      Result := Candidates[i];
      Exit;
    end;

  // Registre HKLM
  if RegQueryStringValue(HKLM, 'SOFTWARE\Tesseract-OCR', 'InstallDir', RegPath) then
    if FileExists(RegPath + '\tesseract.exe') then
    begin
      Result := RegPath + '\tesseract.exe';
      Exit;
    end;

  // Registre HKCU
  if RegQueryStringValue(HKCU, 'SOFTWARE\Tesseract-OCR', 'InstallDir', RegPath) then
    if FileExists(RegPath + '\tesseract.exe') then
      Result := RegPath + '\tesseract.exe';
end;

function NeedsTesseract(): Boolean;
begin
  Result := (FindTesseract() = '');
end;

// ─────────────────────────────────────────────────────────────────────────────
//  Vérification des fichiers redist avant compilation
// ─────────────────────────────────────────────────────────────────────────────
function InitializeSetup(): Boolean;
begin
  Result := True;
  // Les checks sont faits à l'exécution via Check: NeedsPython / NeedsTesseract
end;
