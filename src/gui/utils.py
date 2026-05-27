import os
import re
import tempfile
import shutil
import subprocess
from PyQt6.QtCore import QThread, pyqtSignal, QProcess

CONFIG_PATH = os.path.expanduser("~/.config/cachyos-backup/config")

def load_gui_config():
    """Load config file parse bash-style declarations."""
    defaults = {
        "BACKUP_REPO": os.path.expanduser("~/cachyos-backup"),
        "GITHUB_REMOTE": "",
        "AUR_HELPER": "yay",
        "CHEZMOI_SOURCE": "",
        "USE_CHEZMOI": "true",
        "USE_KONSAVE": "true",
        "EXTRAS_ENABLED": "",
        "TIMER_INTERVAL": "daily",
    }
    if not os.path.exists(CONFIG_PATH):
        return defaults

    config = dict(defaults)
    try:
        with open(CONFIG_PATH, "r") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                match = re.match(r"^([A-Z_]+)\s*=\s*(.*)$", line)
                if match:
                    key, val = match.groups()
                    if (val.startswith('"') and val.endswith('"')) or (val.startswith("'") and val.endswith("'")):
                        val = val[1:-1]
                    if key == "BACKUP_REPO":
                        val = os.path.expanduser(val.replace("${HOME}", "~").replace("$HOME", "~"))
                    config[key] = val
    except Exception as e:
        print(f"Error loading config: {e}")
    return config

def save_gui_config(config):
    """Save configuration in bash-compatible format."""
    os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
    try:
        with open(CONFIG_PATH, "w") as f:
            f.write("# CachyOS Backup Configuration\n\n")
            f.write(f'# Path to the local backup repository\nBACKUP_REPO="{config.get("BACKUP_REPO", "")}"\n\n')
            f.write(f'# GitHub remote URL\nGITHUB_REMOTE="{config.get("GITHUB_REMOTE", "")}"\n\n')
            f.write(f'# AUR helper: yay or paru\nAUR_HELPER="{config.get("AUR_HELPER", "yay")}"\n\n')
            f.write(f'# Chezmoi source directory (leave empty for default)\nCHEZMOI_SOURCE="{config.get("CHEZMOI_SOURCE", "")}"\n\n')
            f.write(f'# Use Chezmoi integration\nUSE_CHEZMOI="{config.get("USE_CHEZMOI", "true")}"\n\n')
            f.write(f'# Use Konsave integration\nUSE_KONSAVE="{config.get("USE_KONSAVE", "true")}"\n\n')
            f.write(f'# Enabled non-pacman package managers (space-separated)\n# Options: flatpak pip cargo npm\nEXTRAS_ENABLED="{config.get("EXTRAS_ENABLED", "")}"\n\n')
            f.write(f'# Periodic timer interval (systemd OnCalendar syntax)\nTIMER_INTERVAL="{config.get("TIMER_INTERVAL", "daily")}"\n')
        return True
    except Exception as e:
        print(f"Error saving config: {e}")
        return False

class GitValidatorWorker(QThread):
    """
    QThread for validating Git URL without freezing the GUI.
    Emits (success, message, is_empty)
    """
    result_ready = pyqtSignal(bool, str, bool)

    def __init__(self, url, check_type="new"):
        super().__init__()
        self.url = url
        self.check_type = check_type # 'new' or 'restore'

    def run(self):
        if not self.url:
            self.result_ready.emit(False, "URL is empty.", False)
            return

        # Basic format check
        if not (self.url.startswith("git@") or self.url.startswith("http://") or self.url.startswith("https://")):
            self.result_ready.emit(False, "Invalid Git URL. Must start with git@, http://, or https://", False)
            return

        try:
            # First, check if reachable using git ls-remote
            env = os.environ.copy()
            env["GIT_TERMINAL_PROMPT"] = "0"  # Prevent git from asking password interactively
            env["GIT_SSH_COMMAND"] = "ssh -o BatchMode=yes"

            proc = subprocess.run(
                ["git", "ls-remote", self.url],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                env=env,
                timeout=10
            )

            if proc.returncode != 0:
                err_msg = proc.stderr.strip()
                if "Permission denied" in err_msg or "fatal: Could not read from remote repository" in err_msg:
                    err_msg = "Could not connect to remote repository. Check SSH key/URL permissions."
                elif not err_msg:
                    err_msg = "Git repository not found or not accessible."
                self.result_ready.emit(False, f"Git validation failed: {err_msg}", False)
                return

            # If check_type is 'new', we expect the repository to be completely empty
            is_empty = len(proc.stdout.strip()) == 0

            if self.check_type == "new":
                if is_empty:
                    self.result_ready.emit(True, "Repository is valid and empty.", True)
                else:
                    self.result_ready.emit(False, "Repository is not empty. Please provide an empty repository for New Setup.", False)
            else: # 'restore'
                if is_empty:
                    self.result_ready.emit(False, "Repository is empty. Cannot restore from an empty repository.", True)
                    return

                # Clone --depth 1 to temporary directory to verify backup files
                temp_dir = tempfile.mkdtemp()
                try:
                    clone_proc = subprocess.run(
                        ["git", "clone", "--depth", "1", self.url, temp_dir],
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        env=env,
                        timeout=15
                    )
                    if clone_proc.returncode != 0:
                        self.result_ready.emit(False, f"Failed to inspect repo files: {clone_proc.stderr.decode().strip()}", False)
                        return

                    required_file = os.path.join(temp_dir, "user-official.txt")
                    if os.path.exists(required_file):
                        self.result_ready.emit(True, "Repository is valid and contains backup files.", False)
                    else:
                        self.result_ready.emit(False, "Repository does not contain valid backup data (user-official.txt missing).", False)
                finally:
                    shutil.rmtree(temp_dir, ignore_errors=True)

        except subprocess.TimeoutExpired:
            self.result_ready.emit(False, "Git command timed out. Check network connection.", False)
        except Exception as e:
            self.result_ready.emit(False, f"Error validating repo: {str(e)}", False)

def resolve_script_path(script_name):
    script_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    local_path = os.path.join(script_dir, script_name)
    if os.path.exists(local_path):
        return local_path
    system_path = shutil.which(script_name)
    if system_path:
        return system_path
    return script_name

def sync_user_systemd_timer(interval):
    """
    Generate and enable a systemd user timer for cachyos-backup-extras.
    interval can be: 'daily', 'weekly', or a time like '14:30'.
    """
    import subprocess
    user_systemd_dir = os.path.expanduser("~/.config/systemd/user")
    os.makedirs(user_systemd_dir, exist_ok=True)
    
    # Format OnCalendar value
    if ":" in interval:
        on_calendar = f"*-*-* {interval}:00"
    else:
        on_calendar = interval # 'daily', 'weekly', etc.
        
    timer_path = os.path.join(user_systemd_dir, "cachyos-backup-extras.timer")
    service_path = os.path.join(user_systemd_dir, "cachyos-backup-extras.service")
    
    try:
        # Write timer unit
        with open(timer_path, "w") as f:
            f.write(f"""[Unit]
Description=Daily tracking of non-pacman packages and KDE settings

[Timer]
OnCalendar={on_calendar}
Persistent=true
RandomizedDelaySec=900

[Install]
WantedBy=timers.target
""")
            
        # Write service unit
        cli_path = resolve_script_path("cachyos-backup")
        if not cli_path.startswith("/"):
            cli_path = "/usr/local/bin/cachyos-backup"
            
        with open(service_path, "w") as f:
            f.write(f"""[Unit]
Description=Non-pacman package backup and KDE settings backup
After=network-online.target
Wants=network-online.target

[Service]
Type=oneshot
ExecStart={cli_path} --extras
""")
            
        # Reload daemon and enable timer
        subprocess.run(["systemctl", "--user", "daemon-reload"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.run(["systemctl", "--user", "enable", "--now", "cachyos-backup-extras.timer"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True
    except Exception as e:
        print(f"Error syncing systemd timer: {e}")
        return False
