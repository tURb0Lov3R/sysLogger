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

    def check_user_credentials(self):
        current_time = datetime.datetime.now().time()
        if self.start_time <= current_time <= self.end_time:
            for user_info in self.users:
                user = user_info.get("user")
                original_passwd = user_info.get("user_passwd")

                if not user or not original_passwd or user in self.checked_users:
                    continue

                try:
                    # Check user credentials
                    command = f"net user {user} {original_passwd}"
                    result = subprocess.run(command, shell=True, capture_output=True, text=True)
                    if result.returncode == 0:
                        print(f"Credentials for user {user} are valid.")
                        self.checked_users.add(user)
                    else:
                        print(f"Invalid credentials for user {user}.")
                except subprocess.CalledProcessError as e:
                    print(f"Error verifying credentials for user {user}: {e}")

    def main(self):
        if not self.load_config():
            return

        while self.running:
            # Check if the flag file exists
            if os.path.exists(self.flag_file_path):
                self.check_user_credentials()
                # Remove the flag file after checking credentials
                os.remove(self.flag_file_path)

            # Sleep for 30 minutes
            time.sleep(1800)

if __name__ == '__main__':
    win32serviceutil.HandleCommandLine(SysLoggerService)
