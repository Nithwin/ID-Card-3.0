
# Build Workflow

## Android (APK)
To create an APK for installation on Android devices:
1. Open terminal in `frontend/`.
2. Run:
   ```powershell
   flutter build apk --release
   ```
3. The APK will be at: `frontend/build/app/outputs/flutter-apk/app-release.apk`.
4. Copy this file to your phone and install.

## Windows (EXE)
To create a standard Windows executable:
1. Open terminal in `frontend/`.
2. Run:
   ```powershell
   flutter build windows --release
   ```
3. The executable will be at: `frontend/build/windows/runner/Release/`.

## Backend (Server)
The backend does not require "building" but can be frozen using PyInstaller if standalone EXE is required.
1. Install PyInstaller: `pip install pyinstaller`.
2. Run:
   ```powershell
   pyinstaller --onefile --name IDCardServer backend/server.py
   ```
   *Note: You may need to manually add `dataset` and `*.pt` files to the dist folder.*
