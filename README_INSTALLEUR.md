# Division 2 DPS Tracker — Guide de construction de l'installeur Windows

## Ce que vous obtiendrez

Un fichier unique **`Division2_DPS_Tracker_Setup.exe`** qui :
- Installe automatiquement **Python 3.12** si absent
- Installe automatiquement **Tesseract OCR** si absent
- Installe toutes les **bibliothèques Python** (Flask, OpenCV, etc.)
- Crée les **raccourcis dans le menu Démarrer** (et optionnellement le Bureau)
- Permet de lancer l'app directement après l'installation

---

## Étape 1 — Télécharger Inno Setup (gratuit)

Rendez-vous sur https://jrsoftware.org/isdl.php  
Téléchargez et installez **Inno Setup 6.x** (version gratuite, stable).

---

## Étape 2 — Préparer la structure des dossiers

Créez cette arborescence sur votre PC :

```
Division2_Installer/
├── setup.iss              ← le script fourni
├── install_deps.bat       ← le script fourni
├── app/
│   ├── server.py          ← votre fichier
│   ├── index.html         ← votre fichier
│   └── lancer.bat         ← le script fourni (version améliorée)
└── redist/
    ├── python-3.12.x-amd64.exe    ← à télécharger (voir ci-dessous)
    └── tesseract-ocr-w64-setup.exe ← à télécharger (voir ci-dessous)
```

---

## Étape 3 — Télécharger les installeurs tiers

### Python 3.12
1. Allez sur https://www.python.org/downloads/windows/
2. Cherchez **"Python 3.12.x"** → **Windows installer (64-bit)**
3. Téléchargez et renommez le fichier en exactement :  
   `python-3.12.x-amd64.exe`
4. Placez-le dans le dossier `redist/`

> **Important :** Mettez à jour le nom exact dans `setup.iss` ligne :
> `Source: "redist\python-3.12.x-amd64.exe"` → remplacez `3.12.x` par la version réelle, ex: `3.12.10`
> Idem pour la ligne `Parameters:` du bloc `[Run]`

### Tesseract OCR (avec données anglaises)
1. Allez sur https://github.com/UB-Mannheim/tesseract/wiki
2. Téléchargez **tesseract-ocr-w64-setup-x.x.x.exe** (64-bit, dernière version)
3. Renommez-le en exactement :  
   `tesseract-ocr-w64-setup.exe`
4. Placez-le dans le dossier `redist/`

> Tesseract s'installe en silencieux avec `/S`, il inclut les données anglaises par défaut.

---

## Étape 4 — Compiler l'installeur

1. Ouvrez **Inno Setup Compiler**
2. **File → Open** → sélectionnez `setup.iss`
3. Vérifiez que les chemins correspondent à votre arborescence
4. Cliquez sur **Build → Compile** (ou touche F9)
5. L'installeur final sera dans le dossier `output/` :  
   **`Division2_DPS_Tracker_Setup.exe`**

---

## Ce que fait l'installeur (côté utilisateur)

L'utilisateur double-clique sur `Division2_DPS_Tracker_Setup.exe` et voit :

1. **Écran de bienvenue** avec description de ce qui sera installé
2. **Choix du dossier** d'installation (défaut : `C:\Program Files\Division2DPSTracker`)
3. **Choix du groupe** dans le menu Démarrer
4. **Option** d'ajouter une icône sur le Bureau
5. **Résumé** des actions avant installation
6. L'installeur :
   - Installe Python 3.12 silencieusement (si absent)
   - Installe Tesseract OCR silencieusement (si absent)
   - Installe les dépendances Python (pip) en arrière-plan
   - Copie les fichiers de l'application
7. **Proposition** de lancer l'application immédiatement

---

## Personnalisation avancée

### Ajouter une icône .ico personnalisée
1. Créez ou trouvez un fichier `icon.ico`
2. Placez-le dans le dossier racine `Division2_Installer/`
3. Dans `setup.iss`, décommentez/modifiez :
   ```
   SetupIconFile=icon.ico
   ```
4. Dans `[Icons]`, ajoutez `IconFilename: "{app}\icon.ico"` à chaque raccourci

### Changer la langue
Le script est configuré en **français** (`French.isl`).  
Pour ajouter l'anglais, dans `[Languages]` ajoutez :
```
Name: "english"; MessagesFile: "compiler:Default.isl"
```

### Distribution
- Le fichier `Division2_DPS_Tracker_Setup.exe` est **autonome** (tout inclus)
- Taille estimée : ~50-80 Mo (Python + Tesseract + app)
- Compatible **Windows 10 / 11** 64-bit

---

## Dépannage fréquent

| Problème | Solution |
|----------|----------|
| "File not found: redist\python-..." | Vérifiez le nom exact du fichier téléchargé |
| "File not found: redist\tesseract-..." | Vérifiez le nom exact du fichier téléchargé |
| Python pas trouvé après install | Relancez le PC (PATH mis à jour au redémarrage) |
| Les dépendances pip échouent | Vérifiez la connexion internet pendant l'install |
| Tesseract non détecté | Relancez `lancer.bat` en tant qu'administrateur |
