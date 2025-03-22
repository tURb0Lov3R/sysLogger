import os
import subprocess
import shutil
import sys
import ctypes

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

def install_chocolatey():
    """Installs Chocolatey if not found."""
    if not shutil.which("choco"):
        print("Chocolatey not found. Installing Chocolatey...")
        os.system("@powershell -NoProfile -ExecutionPolicy Bypass -Command \"[System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072; iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))\"")
    else:
        print("Chocolatey is already installed.")

def install_scoop():
    """Installs Scoop if not found."""
    if not shutil.which("scoop"):
        print("Scoop not found. Installing Scoop...")
        run_command("powershell -command \"iwr -useb get.scoop.sh | iex\"")
    else:
        print("Scoop is already installed.")

def install_packages():
    """Installs necessary packages using Chocolatey."""
    packages = ["pywin32",]
    for package in packages:
        if not shutil.which(package):
            print(f"Installing {package}...")
            run_command(f"choco install {package} -y")
        else:
            print(f"{package} is already installed.")

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

    install_chocolatey()
    install_scoop()
    run_command("choco upgrade all -y")
    run_command("scoop update")
    install_packages()
    install_service()
    print("Installation completed successfully!")

if __name__ == "__main__":
    main()
