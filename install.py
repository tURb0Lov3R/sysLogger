import os
import subprocess
import shutil
import sys
import ctypes
import json

def is_admin():
    """Check if the script is running with administrator privileges."""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def run_as_admin():
    """Re-launch the script with administrator privileges."""
    try:
        ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)
    except Exception as e:
        print(f"Failed to elevate privileges: {e}")
        sys.exit(1)

def run_command(command):
    """Runs a system command and handles errors."""
    try:
        print(f"Running: {command}")
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(result.stdout.strip())
    except subprocess.CalledProcessError as e:
        print(f"Failed to execute: {command}")
        print(e.stderr)

def install_packages():
    """Installs necessary Python packages."""
    packages = ["pywin32"]
    for package in packages:
        print(f"Installing {package}...")
        run_command(f"pip install {package}")

def create_default_config():
    """Creates a default config.json file if it doesn't exist."""
    config_path = os.path.join(os.path.dirname(__file__), 'config.json')
    if not os.path.exists(config_path):
        print(f"Creating default config.json at {config_path}")
        default_config = {
            "start_time": "08:00",
            "end_time": "17:00",
            "users": []
        }
        with open(config_path, 'w') as config_file:
            json.dump(default_config, config_file, indent=4)
    else:
        print(f"config.json already exists at {config_path}")

def install_service():
    """Installs the SysLoggerService."""
    print(f"Installing SysLogger Service...")
    run_command("python syslogger_service.py install")
    print(f"Starting SysLogger Service...")
    run_command("python syslogger_service.py start")

def main():
    if not is_admin():
        print("This script requires administrator privileges. Re-launching as administrator...")
        run_as_admin()
        return

    install_packages()
    create_default_config()
    install_service()
    print("Installation completed successfully!")

if __name__ == "__main__":
    main()
