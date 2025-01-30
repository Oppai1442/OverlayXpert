# OverlayXpert - Oppai [0.0.3]

OverlayXpert is a lightweight overlay manager for Windows, designed for creating persistent overlays that can follow specific applications. It supports transparency, process linking, and easy customization.

## 🚀 Features
- Create and manage multiple overlays.
- Adjustable transparency, color, and border thickness.
- Assign overlays to specific processes.
- Persistent settings (saved in `overlays.json`).
- Lightweight and easy to use.

## 🛠 Installation
### **1. Install Dependencies**
Ensure you have **Python 3.8+** installed and then install the required libraries:

```bash
pip install -r requirements.txt
```

Alternatively, install them manually:
```bash
pip install pyqt5 psutil pywin32
```

### **2. Run the Application**
To start the application, simply run:

```bash
python app.py
```

## 📦 Build Executable with PyInstaller
To create a standalone `.exe` for Windows:

```bash
pyinstaller --clean --onefile --noconsole --icon=icon.ico --add-data "icon.ico;." --name OverlayXpert app.py
```

- `--onefile`: Creates a single executable file.
- `--noconsole`: Hides the console window (for GUI apps).
- `--icon=icon.ico`: Sets a custom icon (optional).
- `--name OverlayXpert`: Defines the output filename.

After successful build, the `.exe` file will be located in the `dist/` folder.

## 🔍 Verify File Integrity (SHA-256 Hash)
To ensure the file has not been tampered with, check the hash:

### **For Windows (PowerShell)**
```powershell
Get-FileHash dist\OverlayXpert.exe -Algorithm SHA256
```

### **For Linux/macOS**
```bash
sha256sum dist/OverlayXpert
```

### **Expected Hash:**
```
7BB498610638297EA6C50DC4795763DB4623B16B1B5622925527C3A8219EAC0E
```

## 📁 Configuration
OverlayXpert saves all overlay configurations in `overlays.json`. This file is automatically created and updated whenever you modify overlays.

## 🛠 Troubleshooting
1. **Missing Dependencies?**  
   Reinstall requirements:  
   ```bash
   pip install --upgrade --force-reinstall -r requirements.txt
   ```
2. **Application Won't Start?**  
   Ensure `PyQt5`, `psutil`, and `pywin32` are correctly installed.

3. **Overlays Not Showing?**  
   Check if the assigned process is running.

## 📜 License
This project is licensed under the **GNU General Public License v3.0 (GPL-3.0)**. 

For more details, see the full license text: [GNU GPL-3.0](https://www.gnu.org/licenses/gpl-3.0.en.html)

---

Developed by **Oppai1442**.
