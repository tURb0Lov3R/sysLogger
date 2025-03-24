# System Logger Service

System Logger Service is a Windows-only tool designed to manage user access by changing user passwords and logging them out during specified hours. This service runs in the background and performs actions based on a configuration file.

## Features

- **Windows-only Tool**: This service is designed to run on Windows operating systems.
- **Change User Password**: The service attempts to change the password of specified users during the configured time frame.
- **Log Out Users**: After changing the password, the service logs out the users.
- **Configuration File**: The service uses a `config.json` file to specify the time frame and user details.

## Prerequisites

- Python 3.x
- `pywin32` library

## Installation

1. **Install Python 3.x**: Ensure Python 3.x is installed on your system.
2. **Install `pywin32`**: Install the `pywin32` library using pip:
    ```sh
    pip install pywin32
    ```

## Usage

### Adding Users and Setting Time Frame

To add users and set the time frame, run the following command:

```sh
python syslogger.py -u username1:password1 -u username2:password2 -s 08:00 -e 18:00
```
### Options

-u: Specifies a user and their password in the format username:password. You can add multiple users by repeating the -u flag.

-s: Specifies the start time for the time frame in the format HH:MM.

-e: Specifies the end time for the time frame in the format HH:MM.

