import os
import shutil
import subprocess
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QLineEdit, QCheckBox, QStackedWidget, QPlainTextEdit, 
    QProgressBar, QGroupBox, QFormLayout, QMessageBox, QFrame
)
from PyQt6.QtCore import pyqtSignal, Qt, QProcess
from PyQt6.QtGui import QFont, QColor, QTextCursor

from .utils import GitValidatorWorker, save_gui_config, resolve_script_path, CONFIG_PATH

class ClickableCard(QFrame):
    clicked = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setObjectName("optionCard")
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)

class WelcomeScreen(QWidget):
    # Signals to transition to setup or restore forms
    on_new_setup = pyqtSignal()
    on_restore = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(24)
        self.setLayout(layout)

        # Title Section
        title_container = QWidget()
        title_layout = QVBoxLayout(title_container)
        title_layout.setContentsMargins(0, 0, 0, 0)
        title_layout.setSpacing(8)
        
        title_label = QLabel("Arch Backup & Restore Tool")
        title_label.setObjectName("welcomeTitle")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        subtitle_label = QLabel("A lightweight graphical utility for package baseline tracking, configuration dotfiles, and system recovery.")
        subtitle_label.setObjectName("welcomeSubtitle")
        subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle_label.setWordWrap(True)

        title_layout.addWidget(title_label)
        title_layout.addWidget(subtitle_label)
        layout.addWidget(title_container)

        # Cards/Buttons Layout
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(30)

        # New Backup Card
        self.new_card = ClickableCard()
        new_layout = QVBoxLayout(self.new_card)
        new_layout.setContentsMargins(20, 20, 20, 20)
        new_layout.setSpacing(12)
        
        new_icon = QLabel("⚙️")
        new_icon.setObjectName("cardIcon")
        new_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        new_title = QLabel("Configure New Backup")
        new_title.setObjectName("cardTitle")
        new_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        new_desc = QLabel("Set up package baseline snapshot and repository synchronization for the current machine.")
        new_desc.setObjectName("cardDesc")
        new_desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        new_desc.setWordWrap(True)
        
        new_layout.addWidget(new_icon)
        new_layout.addWidget(new_title)
        new_layout.addWidget(new_desc)
        buttons_layout.addWidget(self.new_card)

        # Restore Card
        self.restore_card = ClickableCard()
        restore_layout = QVBoxLayout(self.restore_card)
        restore_layout.setContentsMargins(20, 20, 20, 20)
        restore_layout.setSpacing(12)
        
        restore_icon = QLabel("♻️")
        restore_icon.setObjectName("cardIcon")
        restore_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        restore_title = QLabel("Restore from Backup")
        restore_title.setObjectName("cardTitle")
        restore_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        restore_desc = QLabel("Recover packages and dotfiles on a fresh machine from an existing GitHub repository backup.")
        restore_desc.setObjectName("cardDesc")
        restore_desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        restore_desc.setWordWrap(True)

        restore_layout.addWidget(restore_icon)
        restore_layout.addWidget(restore_title)
        restore_layout.addWidget(restore_desc)
        buttons_layout.addWidget(self.restore_card)

        layout.addLayout(buttons_layout)

        # Footer
        footer_label = QLabel("CachyOS & Arch Linux Backup Suite")
        footer_label.setObjectName("welcomeFooter")
        footer_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(footer_label)

        # Event connections
        self.new_card.clicked.connect(self.on_new_setup.emit)
        self.restore_card.clicked.connect(self.on_restore.emit)


class NewSetupForm(QWidget):
    on_back = pyqtSignal()
    on_start_init = pyqtSignal(dict) # Dict contains backup parameters

    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)
        self.setLayout(layout)

        # Title
        title = QLabel("New Backup Configuration")
        title.setObjectName("formTitle")
        layout.addWidget(title)

        # Form Layout
        form_layout = QFormLayout()
        form_layout.setSpacing(12)
        
        # Git Repo Input
        self.git_url = QLineEdit()
        self.git_url.setPlaceholderText("e.g. git@github.com:username/my-arch-backup.git")
        self.git_url.setObjectName("formInput")
        self.git_url.textChanged.connect(self.clear_validation_state)
        form_layout.addRow(QLabel("Empty GitHub Remote URL:"), self.git_url)

        # Local Repo Path Input
        self.local_path = QLineEdit(os.path.expanduser("~/cachyos-backup"))
        self.local_path.setObjectName("formInput")
        form_layout.addRow(QLabel("Local Repository Directory:"), self.local_path)
        
        layout.addLayout(form_layout)

        # Integration group boxes
        self.integrations_group = QGroupBox("Package & Config Integrations")
        self.integrations_group.setObjectName("formGroup")
        group_layout = QVBoxLayout(self.integrations_group)
        group_layout.setSpacing(14)

        # Chezmoi check
        chezmoi_installed = shutil.which("chezmoi") is not None
        chezmoi_row = QHBoxLayout()
        self.use_chezmoi = QCheckBox("Use Chezmoi (Dotfiles Tracking)")
        self.use_chezmoi.setChecked(chezmoi_installed)
        self.use_chezmoi.setEnabled(chezmoi_installed)
        chezmoi_row.addWidget(self.use_chezmoi)
        
        self.install_chezmoi_btn = QPushButton("Install Chezmoi")
        self.install_chezmoi_btn.setObjectName("smallActionBtn")
        self.install_chezmoi_btn.setVisible(not chezmoi_installed)
        self.install_chezmoi_btn.clicked.connect(lambda: self.install_dependency("chezmoi", self.install_chezmoi_btn, self.use_chezmoi))
        chezmoi_row.addWidget(self.install_chezmoi_btn)
        group_layout.addLayout(chezmoi_row)

        # Konsave check
        konsave_installed = shutil.which("konsave") is not None
        konsave_row = QHBoxLayout()
        self.use_konsave = QCheckBox("Use Konsave (KDE Plasma Configurations)")
        self.use_konsave.setChecked(konsave_installed)
        self.use_konsave.setEnabled(konsave_installed)
        konsave_row.addWidget(self.use_konsave)

        self.install_konsave_btn = QPushButton("Install Konsave")
        self.install_konsave_btn.setObjectName("smallActionBtn")
        self.install_konsave_btn.setVisible(not konsave_installed)
        self.install_konsave_btn.clicked.connect(lambda: self.install_dependency("konsave", self.install_konsave_btn, self.use_konsave))
        konsave_row.addWidget(self.install_konsave_btn)
        group_layout.addLayout(konsave_row)

        # Extras Checklist
        self.use_extras = QCheckBox("Enable Extras Tracking (Flatpak, Pip, Cargo, Npm)")
        self.use_extras.setChecked(True)
        group_layout.addWidget(self.use_extras)

        layout.addWidget(self.integrations_group)

        # Validation status label
        self.status_label = QLabel("")
        self.status_label.setObjectName("validationStatus")
        self.status_label.setWordWrap(True)
        layout.addWidget(self.status_label)

        # Button box
        btn_layout = QHBoxLayout()
        self.back_btn = QPushButton("Back")
        self.back_btn.setObjectName("secondaryBtn")
        self.back_btn.clicked.connect(self.on_back.emit)

        self.init_btn = QPushButton("Initialize")
        self.init_btn.setObjectName("primaryBtn")
        self.init_btn.clicked.connect(self.validate_and_start)

        btn_layout.addWidget(self.back_btn)
        btn_layout.addStretch()
        btn_layout.addWidget(self.init_btn)
        layout.addLayout(btn_layout)

        # Git Validation Worker
        self.validator_worker = None

    def clear_validation_state(self):
        self.status_label.setText("")
        self.init_btn.setEnabled(True)

    def get_terminal_command(self, cmd_list):
        for term in ["konsole", "gnome-terminal", "xfce4-terminal", "alacritty", "kitty"]:
            path = shutil.which(term)
            if path:
                if term == "konsole":
                    return [path, "-e"] + cmd_list
                elif term == "kitty":
                    return [path] + cmd_list
                elif term == "xfce4-terminal":
                    return [path, "-e", " ".join(cmd_list)]
                elif term == "alacritty":
                    return [path, "-e"] + cmd_list
                elif term == "gnome-terminal":
                    return [path, "--"] + cmd_list
        return None

    def install_dependency(self, package, button, checkbox):
        button.setEnabled(False)
        button.setText("Installing...")
        self.proc = QProcess()
        
        if package == "chezmoi":
            cmd = ["pkexec", "pacman", "-S", "--needed", "--noconfirm", "chezmoi"]
        else:
            helper = None
            if shutil.which("yay"):
                helper = "yay"
            elif shutil.which("paru"):
                helper = "paru"
                
            if helper:
                cmd_list = [helper, "-S", "--needed", "--noconfirm", package]
                terminal_cmd = self.get_terminal_command(cmd_list)
                if terminal_cmd:
                    cmd = terminal_cmd
                else:
                    cmd = cmd_list
            else:
                cmd = ["pkexec", "pacman", "-S", "--needed", "--noconfirm", package]

        self.proc.start(cmd[0], cmd[1:])
        self.proc.finished.connect(lambda exit_code, status: self.on_install_finished(exit_code, package, button, checkbox))

    def on_install_finished(self, exit_code, package, button, checkbox):
        if shutil.which(package) is not None:
            button.setVisible(False)
            checkbox.setEnabled(True)
            checkbox.setChecked(True)
            QMessageBox.information(self, "Success", f"Successfully installed {package}!")
        else:
            button.setEnabled(True)
            button.setText(f"Install {package}")
            QMessageBox.warning(self, "Failure", f"Failed to install {package}. Please install it manually.")

    def validate_and_start(self):
        url = self.git_url.text().strip()
        if not url:
            self.status_label.setText("⚠️ Git URL is required.")
            return

        self.status_label.setText("Checking remote Git repository...")
        self.init_btn.setEnabled(False)
        self.back_btn.setEnabled(False)

        self.validator_worker = GitValidatorWorker(url, check_type="new")
        self.validator_worker.result_ready.connect(self.on_validation_result)
        self.validator_worker.start()

    def on_validation_result(self, success, message, is_empty):
        self.back_btn.setEnabled(True)
        self.init_btn.setEnabled(True)
        if success:
            self.status_label.setText(f"✅ {message}")
            # Emit data to start recovery
            data = {
                "git_url": self.git_url.text().strip(),
                "local_path": self.local_path.text().strip(),
                "use_chezmoi": self.use_chezmoi.isChecked(),
                "use_konsave": self.use_konsave.isChecked(),
                "use_extras": self.use_extras.isChecked(),
            }
            self.on_start_init.emit(data)
        else:
            self.status_label.setText(f"❌ {message}")


class RestoreForm(QWidget):
    on_back = pyqtSignal()
    on_start_restore = pyqtSignal(dict)

    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)
        self.setLayout(layout)

        # Title
        title = QLabel("Restore System from Backup")
        title.setObjectName("formTitle")
        layout.addWidget(title)

        # Form Layout
        form_layout = QFormLayout()
        form_layout.setSpacing(12)

        self.restore_url = QLineEdit()
        self.restore_url.setPlaceholderText("e.g. git@github.com:username/my-arch-backup.git")
        self.restore_url.setObjectName("formInput")
        self.restore_url.textChanged.connect(self.clear_validation_state)
        form_layout.addRow(QLabel("Backup GitHub URL (Restore From):"), self.restore_url)

        self.target_url = QLineEdit()
        self.target_url.setPlaceholderText("Optional (e.g. git@github.com:username/new-backup.git)")
        self.target_url.setObjectName("formInput")
        form_layout.addRow(QLabel("Target Backup URL (Sysadmin Mode):"), self.target_url)

        self.local_path = QLineEdit(os.path.expanduser("~/cachyos-backup"))
        self.local_path.setObjectName("formInput")
        form_layout.addRow(QLabel("Clone Repository Directory:"), self.local_path)

        layout.addLayout(form_layout)

        # Restorations Checkbox Options
        self.options_group = QGroupBox("Restoration Configuration")
        self.options_group.setObjectName("formGroup")
        group_layout = QVBoxLayout(self.options_group)
        group_layout.setSpacing(10)

        self.skip_chezmoi = QCheckBox("Skip Chezmoi dotfiles restoration")
        self.skip_extras = QCheckBox("Skip non-pacman package managers restoration (Flatpak, Pip, etc.)")
        self.dry_run = QCheckBox("Dry Run (Simulation mode - test installation without applying changes)")

        group_layout.addWidget(self.skip_chezmoi)
        group_layout.addWidget(self.skip_extras)
        group_layout.addWidget(self.dry_run)
        layout.addWidget(self.options_group)

        # Status label
        self.status_label = QLabel("")
        self.status_label.setObjectName("validationStatus")
        self.status_label.setWordWrap(True)
        layout.addWidget(self.status_label)

        # Button Box
        btn_layout = QHBoxLayout()
        self.back_btn = QPushButton("Back")
        self.back_btn.setObjectName("secondaryBtn")
        self.back_btn.clicked.connect(self.on_back.emit)

        self.restore_btn = QPushButton("Start Restoration")
        self.restore_btn.setObjectName("primaryBtn")
        self.restore_btn.clicked.connect(self.validate_and_start)

        btn_layout.addWidget(self.back_btn)
        btn_layout.addStretch()
        btn_layout.addWidget(self.restore_btn)
        layout.addLayout(btn_layout)

        self.validator_worker = None

    def clear_validation_state(self):
        self.status_label.setText("")
        self.restore_btn.setEnabled(True)

    def validate_and_start(self):
        url = self.restore_url.text().strip()
        if not url:
            self.status_label.setText("⚠️ Restore URL is required.")
            return

        self.status_label.setText("Inspecting remote Git repository backup files...")
        self.restore_btn.setEnabled(False)
        self.back_btn.setEnabled(False)

        self.validator_worker = GitValidatorWorker(url, check_type="restore")
        self.validator_worker.result_ready.connect(self.on_validation_result)
        self.validator_worker.start()

    def on_validation_result(self, success, message, is_empty):
        self.back_btn.setEnabled(True)
        self.restore_btn.setEnabled(True)
        if success:
            self.status_label.setText(f"✅ {message}")
            data = {
                "restore_url": self.restore_url.text().strip(),
                "target_url": self.target_url.text().strip(),
                "local_path": self.local_path.text().strip(),
                "skip_chezmoi": self.skip_chezmoi.isChecked(),
                "skip_extras": self.skip_extras.isChecked(),
                "dry_run": self.dry_run.isChecked(),
            }
            self.on_start_restore.emit(data)
        else:
            self.status_label.setText(f"❌ {message}")


class ProgressConsole(QWidget):
    on_finished = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(16)
        self.setLayout(layout)

        # Title
        self.title_label = QLabel("Executing Operation...")
        self.title_label.setObjectName("formTitle")
        layout.addWidget(self.title_label)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0) # Indeterminate style on start
        self.progress_bar.setObjectName("consoleProgress")
        layout.addWidget(self.progress_bar)

        # Console area
        self.console = QPlainTextEdit()
        self.console.setReadOnly(True)
        self.console.setObjectName("consoleOutput")
        self.console.setFont(QFont("Monospace", 10))
        layout.addWidget(self.console)

        # Action Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        self.continue_btn = QPushButton("Continue")
        self.continue_btn.setObjectName("primaryBtn")
        self.continue_btn.setEnabled(False)
        self.continue_btn.clicked.connect(self.on_finished.emit)
        btn_layout.addWidget(self.continue_btn)
        layout.addLayout(btn_layout)

        self.process = None
        self.commands_queue = []
        self.current_step = 0
        self.on_success_callback = None
    def start_generic_command(self, cmd, desc):
        self.console.clear()
        self.continue_btn.setEnabled(False)
        self.progress_bar.setRange(0, 0)
        self.title_label.setText(desc)
        self.is_recovery_run = False

        self.commands_queue = [
            (cmd, desc)
        ]
        self.current_step = 0
        self.run_next_command()

    def start_new_setup_pipeline(self, data):
        self.console.clear()
        self.continue_btn.setEnabled(False)
        self.progress_bar.setRange(0, 0)
        self.title_label.setText("Initializing Backup Setup...")
        self.is_recovery_run = False

        local_path = data["local_path"]
        git_url = data["git_url"]
        
        # Save config
        config = {
            "BACKUP_REPO": local_path,
            "GITHUB_REMOTE": git_url,
            "AUR_HELPER": "yay" if shutil.which("yay") else ("paru" if shutil.which("paru") else "yay"),
            "CHEZMOI_SOURCE": "",
            "EXTRAS_ENABLED": "flatpak pip cargo npm" if data["use_extras"] else "",
            "TIMER_INTERVAL": "daily"
        }
        
        # We will run standard sequence of commands
        # 1. mkdir -p local_path
        # 2. git init
        # 3. git remote add origin git_url
        # 4. save config file
        # 5. run backup --baseline
        # 6. run backup --backup

        self.write_log(f"Creating local directory at {local_path}...\n")
        os.makedirs(local_path, exist_ok=True)

        self.commands_queue = [
            # Git init
            (["git", "-C", local_path, "init"], "Initializing Git repository..."),
            # Git remote
            (["git", "-C", local_path, "remote", "add", "origin", git_url], "Adding Git remote origin..."),
            # Save config locally first (so bash scripts can source it)
            (lambda: save_gui_config(config), "Writing backup config..."),
            # Baseline
            ([resolve_script_path("cachyos-backup"), "--baseline"], "Capturing baseline package snapshot..."),
            # Sync & First Push
            ([resolve_script_path("cachyos-backup"), "--backup"], "Performing first backup and pushing package differences...")
        ]
        
        self.current_step = 0
        self.run_next_command()

    def start_restore_pipeline(self, data):
        self.console.clear()
        self.continue_btn.setEnabled(False)
        self.progress_bar.setRange(0, 0)
        self.title_label.setText("Running System Restoration...")
        self.is_recovery_run = True

        local_path = data["local_path"]
        restore_url = data["restore_url"]
        target_url = data["target_url"]
        
        # Flags
        rec_args = ["--repo", restore_url, "--local", local_path]
        
        # Aur helper search
        helper = "yay" if shutil.which("yay") else ("paru" if shutil.which("paru") else "")
        if helper:
            rec_args += ["--aur-helper", helper]
            
        if data["skip_chezmoi"]:
            rec_args += ["--skip-dotfiles"]
        if data["skip_extras"]:
            rec_args += ["--skip-extras"]
        if data["dry_run"]:
            rec_args += ["--dry-run"]

        # If Target URL is provided, we need to overwrite the remote and config afterwards
        def update_config_post_restore():
            final_remote = target_url if target_url else restore_url
            
            # Write final config file
            config = {
                "BACKUP_REPO": local_path,
                "GITHUB_REMOTE": final_remote,
                "AUR_HELPER": helper if helper else "yay",
                "CHEZMOI_SOURCE": "",
                "EXTRAS_ENABLED": "flatpak pip cargo npm" if not data["skip_extras"] else "",
                "TIMER_INTERVAL": "daily"
            }
            save_gui_config(config)

            # Update git remote url if sysadmin target is different
            if target_url and not data["dry_run"]:
                subprocess.run(["git", "-C", local_path, "remote", "set-url", "origin", target_url])
                self.write_log(f"Updated Git remote URL to Target: {target_url}\n")
            return True

        self.commands_queue = [
            # 1. Run recovery script
            ([resolve_script_path("cachyos-recovery")] + rec_args, "Executing package and settings restoration..."),
            # 2. Write configuration and update remote
            (update_config_post_restore, "Updating configuration and setting backup remote targets...")
        ]
        
        self.current_step = 0
        self.run_next_command()

    def run_next_command(self):
        if self.current_step >= len(self.commands_queue):
            self.on_pipeline_success()
            return

        cmd, desc = self.commands_queue[self.current_step]
        self.write_log(f"\n>>> [Step {self.current_step + 1}/{len(self.commands_queue)}] {desc}\n")
        
        if callable(cmd):
            # Run python function step
            try:
                res = cmd()
                if res:
                    self.write_log("✅ Step completed successfully.\n")
                    self.current_step += 1
                    self.run_next_command()
                else:
                    self.on_pipeline_failure("Function step returned failure status.")
            except Exception as e:
                self.on_pipeline_failure(f"Error in execution step: {str(e)}")
        else:
            # Run shell process step
            self.process = QProcess()
            self.process.setProcessChannelMode(QProcess.ProcessChannelMode.MergedChannels)
            self.process.readyReadStandardOutput.connect(self.read_process_output)
            self.process.finished.connect(self.process_finished)
            
            # Print execution details
            self.write_log(f"Running: {' '.join(cmd)}\n")
            
            # Start
            self.process.start(cmd[0], cmd[1:])

    def read_process_output(self):
        data = self.process.readAllStandardOutput().data().decode("utf-8", errors="ignore")
        self.write_log(data)

    def process_finished(self, exit_code, exit_status):
        if exit_code == 0:
            self.write_log(f"✅ Process finished successfully.\n")
            self.current_step += 1
            self.run_next_command()
        else:
            self.on_pipeline_failure(f"Process crashed with exit code {exit_code}.")

    def write_log(self, text):
        self.console.moveCursor(QTextCursor.MoveOperation.End)
        self.console.insertPlainText(text)
        self.console.moveCursor(QTextCursor.MoveOperation.End)

    def on_pipeline_success(self):
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(100)
        self.title_label.setText("Operation Completed Successfully! ✅")
        self.continue_btn.setEnabled(True)
        self.write_log("\n*** SETUP PIPELINE COMPLETED SUCCESSFULLY ***\n")

    def on_pipeline_failure(self, error_msg):
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.title_label.setText("Operation Failed ❌")
        self.write_log(f"\n❌ ERROR: {error_msg}\n")
        self.write_log("\nPlease review the logs above. You can close the app or try again.\n")
        
        # Enable continue button so user isn't permanently locked out of resolving the issue
        # (Though dashboard is locked, they can go back if we allow it, or restart)
        self.continue_btn.setEnabled(True)
        self.continue_btn.setText("Go Back / Reset")
        self.continue_btn.clicked.disconnect()
        self.continue_btn.clicked.connect(self.reset_console_flow)

    def reset_console_flow(self):
        # Disconnect and reset
        self.continue_btn.clicked.disconnect()
        self.continue_btn.clicked.connect(self.on_finished.emit)
        self.continue_btn.setText("Continue")
        # Trigger parent layout reset
        self.on_finished.emit()


class OnboardingWizard(QStackedWidget):
    onboarding_complete = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        # 0: Welcome Screen
        self.welcome = WelcomeScreen()
        self.welcome.on_new_setup.connect(lambda: self.setCurrentIndex(1))
        self.welcome.on_restore.connect(lambda: self.setCurrentIndex(2))
        self.addWidget(self.welcome)

        # 1: New Setup Form
        self.new_setup = NewSetupForm()
        self.new_setup.on_back.connect(lambda: self.setCurrentIndex(0))
        self.new_setup.on_start_init.connect(self.start_initialization_flow)
        self.addWidget(self.new_setup)

        # 2: Restore Form
        self.restore = RestoreForm()
        self.restore.on_back.connect(lambda: self.setCurrentIndex(0))
        self.restore.on_start_restore.connect(self.start_restoration_flow)
        self.addWidget(self.restore)

        # 3: Progress Console
        self.console = ProgressConsole()
        self.console.on_finished.connect(self.on_console_finished)
        self.addWidget(self.console)

    def start_initialization_flow(self, data):
        self.setCurrentIndex(3)
        self.console.start_new_setup_pipeline(data)

    def start_restoration_flow(self, data):
        self.setCurrentIndex(3)
        self.console.start_restore_pipeline(data)

    def on_console_finished(self):
        # If success, tell parent (main window) to load dashboard
        if os.path.exists(CONFIG_PATH):
            self.onboarding_complete.emit()
        else:
            # Went back/failed, redirect to welcome
            self.setCurrentIndex(0)
