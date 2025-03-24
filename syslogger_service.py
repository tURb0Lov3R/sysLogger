import subprocess
import win32serviceutil
import win32service
import win32event
import servicemanager
import json
import os
import time
import datetime

class SysLoggerService(win32serviceutil.ServiceFramework):
    _svc_name_ = "SysLoggerService"
    _svc_display_name_ = "System Logger Service"
    _svc_description_ = "A service that blocks system access during specified hours."

    def __init__(self, args):
        win32serviceutil.ServiceFramework.__init__(self, args)
        self.hWaitStop = win32event.CreateEvent(None, 0, 0, None)
        self.running = True
        self.start_time = None
        self.end_time = None
        self.users = []
        self.checked_users = set()
        self.flag_file_path = os.path.join(os.path.dirname(__file__), 'check_flag.txt')
        self.initial_check_done = False

    def SvcStop(self):
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        win32event.SetEvent(self.hWaitStop)
        self.running = False

    def SvcDoRun(self):
        servicemanager.LogMsg(servicemanager.EVENTLOG_INFORMATION_TYPE,
                              servicemanager.PYS_SERVICE_STARTED,
                              (self._svc_name_, ""))
        self.main()

    def load_config(self):
        try:
            config_path = os.path.join(os.path.dirname(__file__), 'config.json')
            if not os.path.exists(config_path):
                return False

            with open(config_path, 'r') as config_file:
                config = json.load(config_file)
            
            self.start_time = datetime.datetime.strptime(config["start_time"], "%H:%M").time()
            self.end_time = datetime.datetime.strptime(config["end_time"], "%H:%M").time()
            self.users = config.get("users", [])
            return True
        except FileNotFoundError:
            pass
        except json.JSONDecodeError:
            pass
        except KeyError:
            pass
        except Exception:
            pass
        return False

    def change_password_and_log_out(self):
        new_password = "new_password"  # Define the new password here
        for user_info in self.users:
            user = user_info.get("user")
            original_passwd = user_info.get("user_passwd")

            if not user or not original_passwd or user in self.checked_users:
                continue

            try:
                # Change user password using PowerShell
                command = f"powershell -command \"Set-LocalUser -Name '{user}' -Password (ConvertTo-SecureString -AsPlainText '{new_password}' -Force)\""
                result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
                if result.returncode == 0:
                    print(f"Password for user {user} changed: {result.stdout}")
                    self.checked_users.add(user)

                    # Log out the user
                    self.log_out_user(user)
                else:
                    print(f"Failed to change password for user {user}: {result.stderr}")
            except subprocess.CalledProcessError as e:
                print(f"Error changing password for user {user}: {e}")
            except Exception as e:
                print(f"Unexpected error changing password for user {user}: {e}")

    def log_out_user(self, username):
        try:
            # Find the session ID of the user
            result = subprocess.run(["query", "user"], capture_output=True, text=True)
            lines = result.stdout.splitlines()
            for line in lines:
                if username in line:
                    session_id = int(line.split()[2])
                    # Log off the user using PowerShell
                    command = f"powershell -command \"logoff {session_id}\""
                    result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
                    print(f"User {username} logged off: {result.stdout}")
                    return
            print(f"User {username} not found.")
        except subprocess.CalledProcessError as e:
            print(f"Error logging out user {username}: {e}")
        except Exception as e:
            print(f"Unexpected error logging out user {username}: {e}")

    def main(self):
        if not self.load_config():
            return

        while self.running:
            current_time = datetime.datetime.now().time()

            # Perform the initial check once if within the time frame
            if not self.initial_check_done and self.start_time <= current_time <= self.end_time:
                self.change_password_and_log_out()
                self.initial_check_done = True

            # Check if the flag file exists
            if os.path.exists(self.flag_file_path):
                if self.start_time <= current_time <= self.end_time:
                    self.change_password_and_log_out()
                try:
                    os.remove(self.flag_file_path)
                    print(f"Flag file {self.flag_file_path} removed.")
                except Exception as e:
                    print(f"Error removing flag file {self.flag_file_path}: {e}")

            # Check user credentials once if outside the time frame
            if not (self.start_time <= current_time <= self.end_time):
                self.change_password_and_log_out()
                self.initial_check_done = False  # Reset for the next time frame

            # Sleep for a short interval to check the flag file more frequently
            time.sleep(10)

if __name__ == '__main__':
    win32serviceutil.HandleCommandLine(SysLoggerService)
