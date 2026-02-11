# Android APK Packaging Guide

## Prerequisites
- Windows Subsystem for Linux (WSL) installed (Ubuntu recommended).
- Python 3 installed in WSL.
- Git installed in WSL.

## Steps

1. **Open WSL Terminal**
   Navigate to the project directory in WSL.
   (e.g., `cd /mnt/e/MyGame/Trea/挂机成神`)

2. **Install Buildozer Dependencies**
   Run the following commands in WSL:
   ```bash
   sudo apt update
   sudo apt install -y git zip unzip openjdk-17-jdk python3-pip autoconf libtool pkg-config zlib1g-dev libncurses5-dev libncursesw5-dev libtinfo5 cmake libffi-dev libssl-dev
   pip3 install --user --upgrade buildozer Cython==0.29.36
   ```

3. **Build the APK**
   Run the following command in the project root:
   ```bash
   # Use python3 -m to avoid PATH issues
   python3 -m buildozer android debug
   ```
   *Note: The first build will take a long time as it downloads the Android SDK/NDK.*

4. **Locate the APK**
   Once finished, the APK will be in the `bin/` directory.

## Notes
- **Code Backup**: The PC version source code has been backed up to `backups/src_pc_backup/`.
- **Screen Adaptation**: The game engine has been updated to automatically scale the UI to fit mobile screens (maintaining aspect ratio with black bars if necessary).
- **Input**:
  - **Left Click**: Tap screen.
  - **Right Click**: **Long Press** (hold for >0.6s).
- **Files**:
  - `buildozer.spec`: Configuration file for the build.
  - `main.py`: Entry point for the Android app.
