import argparse
import datetime
import sys
import subprocess
import json
import os
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

def check_service_status(service_name):
    """Check if the specified service is running."""
    try:
        result = subprocess.run(["sc", "query", service_name], capture_output=True, text=True)
        if "RUNNING" in result.stdout:
            print(f"The {service_name} is currently running.")
        else:
            print(f"The {service_name} is not running.")
            try:
                print(f"Running: python syslogger_service.py start")
                result = subprocess.run("python syslogger_service.py start", shell=True, check=True, capture_output=True, text=True)
                print(result.stdout.strip())
            except subprocess.CalledProcessError as e:
                print(f"Failed to execute: python syslogger_service.py start")
                print(e.stderr)
    except Exception as e:
        print(f"Failed to query the service status: {e}")

def verify_user_credentials(username, password):
    """Verify if the user credentials are correct."""
    try:
        command = f"net user {username} {password}"
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            return True
        else:
            print(f"Invalid credentials for user {username}.")
            return False
    except subprocess.CalledProcessError as e:
        print(f"Error verifying credentials for user {username}: {e}")
        return False

def main():
    if not is_admin():
        print("This script requires administrator privileges. Re-launching as administrator...")
        run_as_admin()
        return

    check_service_status("SysLoggerService")
    parser = argparse.ArgumentParser(description="System Logger Configuration")
    parser.add_argument("-s", "--start_time", help="Set a starting time")
    parser.add_argument("-e", "--end_time", help="Set an ending time")
    parser.add_argument("-u", "--users", required=True, nargs='+', help="Enter the usernames and passwords in the format user1:user1_passwd user2:user2_passwd ...")
    parser.add_argument("-v", "--verbose", action="store_true", help="Enable verbose output.")
    
    args = parser.parse_args()

    users = []
    for user_passwd in args.users:
        user, passwd = user_passwd.split(':')
        if verify_user_credentials(user, passwd):
            users.append({"user": user, "user_passwd": passwd})
        else:
            print(f"Skipping user {user} due to invalid credentials.")

    if not users:
        print("No valid user credentials provided. Exiting.")
        sys.exit(1)

    if not args.start_time:
        start_time = datetime.datetime.now().replace(hour=8, minute=0, second=0, microsecond=0).strftime("%H:%M")
    else:
        start_time = datetime.datetime.strptime(args.start_time, "%H:%M").strftime("%H:%M")

    if not args.end_time:
        end_time = (datetime.datetime.strptime(start_time, "%H:%M") + datetime.timedelta(hours=8)).strftime("%H:%M")
    else:
        end_time = datetime.datetime.strptime(args.end_time, "%H:%M").strftime("%H:%M")
    
    if datetime.datetime.strptime(start_time, "%H:%M") >= datetime.datetime.strptime(end_time, "%H:%M"):
        print(f"Impossible Time Range, please provide a new time range.")
        sys.exit(1)

    config = {
        "start_time": start_time,
        "end_time": end_time,
        "users": users
    }

    config_path = os.path.join(os.path.dirname(__file__), 'config.json')
    with open(config_path, 'w') as config_file:
        json.dump(config, config_file)

    print("Configuration updated successfully!")

if __name__ == "__main__":
    main()