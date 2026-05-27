import os
import shutil
import subprocess
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QLineEdit, QListWidget, QListWidgetItem, QFileDialog, 
    QMessageBox, QTextBrowser, QTabWidget, QSplitter, QCheckBox,
    QComboBox
)
from PyQt6.QtCore import pyqtSignal, Qt, QProcess
from PyQt6.QtGui import QFont, QColor

from .utils import load_gui_config, save_gui_config, resolve_script_path, CONFIG_PATH

def get_pacman_install_dates():
    install_dates = {}
    db_path = "/var/lib/pacman/local"
    if not os.path.exists(db_path):
        return install_dates
    try:
        for entry in os.scandir(db_path):
            if entry.is_dir():
                desc_path = os.path.join(entry.path, "desc")
                if os.path.exists(desc_path):
                    pkg_name = None
                    install_date = 0
                    with open(desc_path, "r", encoding="utf-8", errors="ignore") as f:
                        lines = f.readlines()
                        for i, line in enumerate(lines):
                            line_stripped = line.strip()
                            if line_stripped == "%NAME%":
                                if i + 1 < len(lines):
                                    pkg_name = lines[i+1].strip()
                            elif line_stripped == "%INSTALLDATE%":
                                if i + 1 < len(lines):
                                    try:
                                        install_date = int(lines[i+1].strip())
                                    except ValueError:
                                        pass
                    if pkg_name:
                        install_dates[pkg_name] = install_date
    except Exception as e:
        print(f"Error reading pacman database: {e}")
    return install_dates

class AppsTab(QWidget):
    # Emit command output or run complete signal
    status_message = pyqtSignal(str)
    run_backup_requested = pyqtSignal(dict) # Requests a background run of --backup

    def __init__(self):
        super().__init__()
        self.installed_packages = []
        self.baseline_packages = set()
        self.original_checked = set()
        self.current_checked = set()
        self.init_ui()
        self.load_packages()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(14)
        self.setLayout(layout)

        # Header with Search and Action Button
        header = QHBoxLayout()
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Search installed packages...")
        self.search_input.setObjectName("searchInput")
        self.search_input.textChanged.connect(self.filter_packages)
        header.addWidget(self.search_input)

        self.hide_preinstalled_cb = QCheckBox("Hide Preinstalled")
        self.hide_preinstalled_cb.stateChanged.connect(self.filter_packages)
        header.addWidget(self.hide_preinstalled_cb)

        self.checked_only_cb = QCheckBox("Checked Only")
        self.checked_only_cb.stateChanged.connect(self.filter_packages)
        header.addWidget(self.checked_only_cb)

        self.sort_dropdown = QComboBox()
        self.sort_dropdown.addItems(["Sort: Alphabetical", "Sort: Newest First", "Sort: Oldest First"])
        self.sort_dropdown.currentIndexChanged.connect(self.sort_and_rebuild_list)
        header.addWidget(self.sort_dropdown)

        self.update_btn = QPushButton("Update Backup")
        self.update_btn.setObjectName("primaryBtn")
        self.update_btn.setVisible(False)
        self.update_btn.clicked.connect(self.apply_changes)
        header.addWidget(self.update_btn)

        layout.addLayout(header)

        # Packages List
        self.list_widget = QListWidget()
        self.list_widget.setObjectName("packageList")
        self.list_widget.itemChanged.connect(self.on_item_changed)
        layout.addWidget(self.list_widget)

        # Status Label
        self.count_label = QLabel("Loading packages...")
        self.count_label.setObjectName("statusLabel")
        layout.addWidget(self.count_label)

    def load_packages(self):
        self.list_widget.clear()
        self.list_widget.blockSignals(True)
        
        config = load_gui_config()
        backup_repo = config.get("BACKUP_REPO", "")

        user_official_path = os.path.join(backup_repo, "user-official.txt")
        user_foreign_path = os.path.join(backup_repo, "user-foreign.txt")
        baseline_official_path = os.path.join(backup_repo, "baseline-official.txt")
        baseline_foreign_path = os.path.join(backup_repo, "baseline-foreign.txt")

        # Read checked packages from current backup state
        checked_pkgs = set()
        for path in [user_official_path, user_foreign_path]:
            if os.path.exists(path):
                try:
                    with open(path, "r") as f:
                        for line in f:
                            pkg = line.strip()
                            if pkg:
                                checked_pkgs.add(pkg)
                except Exception as e:
                    print(f"Error reading package list {path}: {e}")

        # Read baseline packages (preinstalled system baseline)
        self.baseline_packages = set()
        for path in [baseline_official_path, baseline_foreign_path]:
            if os.path.exists(path):
                try:
                    with open(path, "r") as f:
                        for line in f:
                            pkg = line.strip()
                            if pkg:
                                self.baseline_packages.add(pkg)
                except Exception as e:
                    print(f"Error reading baseline list {path}: {e}")

        self.original_checked = set(checked_pkgs)
        self.current_checked = set(checked_pkgs)

        # Load installed packages from pacman
        self.installed_packages = []
        install_dates = get_pacman_install_dates()
        try:
            # Official
            proc = subprocess.run(["pacman", "-Qqen"], stdout=subprocess.PIPE, text=True)
            if proc.returncode == 0:
                for line in proc.stdout.splitlines():
                    pkg = line.strip()
                    if pkg:
                        self.installed_packages.append((pkg, "official", install_dates.get(pkg, 0)))
            # Foreign
            proc = subprocess.run(["pacman", "-Qqem"], stdout=subprocess.PIPE, text=True)
            if proc.returncode == 0:
                for line in proc.stdout.splitlines():
                    pkg = line.strip()
                    if pkg:
                        self.installed_packages.append((pkg, "foreign", install_dates.get(pkg, 0)))
        except Exception as e:
            self.count_label.setText(f"Error loading pacman packages: {e}")
            self.list_widget.blockSignals(False)
            return

        self.sort_and_rebuild_list()
        self.update_btn.setVisible(False)

    def update_count_label(self):
        checked_count = len(self.current_checked)
        total_count = len(self.installed_packages)
        self.count_label.setText(f"Showing {self.list_widget.count()} of {total_count} packages | {checked_count} selected for backup")

    def sort_and_rebuild_list(self):
        sort_mode = self.sort_dropdown.currentIndex()
        if sort_mode == 0: # Alphabetical
            self.installed_packages.sort(key=lambda x: x[0].lower())
        elif sort_mode == 1: # Newest First
            self.installed_packages.sort(key=lambda x: x[2], reverse=True)
        elif sort_mode == 2: # Oldest First
            self.installed_packages.sort(key=lambda x: x[2])

        self.list_widget.blockSignals(True)
        self.list_widget.clear()

        for pkg, pkg_type, install_date in self.installed_packages:
            item = QListWidgetItem(pkg)
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            
            if pkg_type == "foreign":
                item.setText(f"{pkg} (AUR)")
                item.setForeground(QColor("#14b8a6"))
            
            if pkg in self.current_checked:
                item.setCheckState(Qt.CheckState.Checked)
            else:
                item.setCheckState(Qt.CheckState.Unchecked)

            item.setData(Qt.ItemDataRole.UserRole, (pkg, pkg_type))
            self.list_widget.addItem(item)

        self.list_widget.blockSignals(False)
        self.filter_packages()

    def filter_packages(self):
        query = self.search_input.text().strip().lower()
        hide_preinstalled = self.hide_preinstalled_cb.isChecked()
        checked_only = self.checked_only_cb.isChecked()

        self.list_widget.blockSignals(True)
        
        visible_count = 0
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            pkg, _ = item.data(Qt.ItemDataRole.UserRole)
            
            matches_query = query in pkg.lower()
            is_preinstalled = pkg in self.baseline_packages
            matches_preinstalled = not (hide_preinstalled and is_preinstalled)
            
            is_checked = pkg in self.current_checked
            matches_checked_only = not (checked_only and not is_checked)
            
            if matches_query and matches_preinstalled and matches_checked_only:
                item.setHidden(False)
                visible_count += 1
            else:
                item.setHidden(True)
                
        self.list_widget.blockSignals(False)
        total_count = len(self.installed_packages)
        checked_count = len(self.current_checked)
        self.count_label.setText(f"Showing {visible_count} of {total_count} packages | {checked_count} selected for backup")

    def on_item_changed(self, item):
        pkg, pkg_type = item.data(Qt.ItemDataRole.UserRole)
        is_checked = item.checkState() == Qt.CheckState.Checked
        
        if is_checked:
            self.current_checked.add(pkg)
        else:
            self.current_checked.discard(pkg)

        # Check if changes differ from original checked list
        has_changed = self.current_checked != self.original_checked
        self.update_btn.setVisible(has_changed)
        self.update_count_label()

    def apply_changes(self):
        config = load_gui_config()
        backup_repo = config.get("BACKUP_REPO", "")
        if not backup_repo or not os.path.exists(backup_repo):
            QMessageBox.critical(self, "Error", "Backup repository path does not exist.")
            return

        # Prepare lists to write
        user_official = []
        baseline_official = []
        user_foreign = []
        baseline_foreign = []

        for pkg, pkg_type, install_date in self.installed_packages:
            is_checked = pkg in self.current_checked
            if pkg_type == "official":
                if is_checked:
                    user_official.append(pkg)
                else:
                    baseline_official.append(pkg)
            else:
                if is_checked:
                    user_foreign.append(pkg)
                else:
                    baseline_foreign.append(pkg)

        # Sort lists alphabetically to ensure bash 'comm' operations do not fail
        user_official.sort()
        baseline_official.sort()
        user_foreign.sort()
        baseline_foreign.sort()

        # Write partitioned lists back to repository files
        try:
            with open(os.path.join(backup_repo, "user-official.txt"), "w") as f:
                f.write("\n".join(user_official) + ("\n" if user_official else ""))
            with open(os.path.join(backup_repo, "baseline-official.txt"), "w") as f:
                f.write("\n".join(baseline_official) + ("\n" if baseline_official else ""))
            with open(os.path.join(backup_repo, "user-foreign.txt"), "w") as f:
                f.write("\n".join(user_foreign) + ("\n" if user_foreign else ""))
            with open(os.path.join(backup_repo, "baseline-foreign.txt"), "w") as f:
                f.write("\n".join(baseline_foreign) + ("\n" if baseline_foreign else ""))

            # Reset baseline comparison baseline
            self.original_checked = set(self.current_checked)
            self.update_btn.setVisible(False)
            
            # Emit signal to request backup run in parent dashboard
            self.run_backup_requested.emit(config)

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save package lists: {e}")


class ChezmoiTab(QWidget):
    status_message = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.init_ui()
        self.load_dotfiles()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(14)
        self.setLayout(layout)

        # Header Info
        header_layout = QHBoxLayout()
        title = QLabel("Tracked Configuration Dotfiles")
        title.setObjectName("sectionTitle")
        header_layout.addWidget(title)
        
        self.add_btn = QPushButton("+ Track New File")
        self.add_btn.setObjectName("primaryBtn")
        self.add_btn.clicked.connect(self.browse_and_add)
        header_layout.addWidget(self.add_btn)

        layout.addLayout(header_layout)

        # Dotfile list
        self.list_widget = QListWidget()
        self.list_widget.setObjectName("dotfileList")
        self.list_widget.itemChanged.connect(self.on_item_changed)
        layout.addWidget(self.list_widget)

        # Info footer
        self.footer = QLabel("Chezmoi managing dotfiles configuration.")
        self.footer.setObjectName("statusLabel")
        layout.addWidget(self.footer)

        self.proc = None

    def load_dotfiles(self):
        self.list_widget.clear()
        self.list_widget.blockSignals(True)

        if not shutil.which("chezmoi"):
            self.footer.setText("⚠️ chezmoi is not installed on this system.")
            self.add_btn.setEnabled(False)
            self.list_widget.blockSignals(False)
            return

        # List of common configuration files to check
        common_files = [
            ".bashrc", ".zshrc", ".gitconfig", ".profile", ".xprofile",
            ".config/fish/config.fish",
            ".config/kitty/kitty.conf",
            ".config/alacritty/alacritty.toml",
            ".config/i3/config",
            ".config/sway/config",
            ".config/waybar/config",
            ".config/neofetch/config.conf",
        ]

        # Query currently managed files from chezmoi
        managed_files = set()
        try:
            proc = subprocess.run(["chezmoi", "managed"], stdout=subprocess.PIPE, text=True)
            if proc.returncode == 0:
                for line in proc.stdout.splitlines():
                    managed_files.add(line.strip())
        except Exception as e:
            print(f"Error querying chezmoi managed files: {e}")

        # Populate checklist
        home = os.path.expanduser("~")
        
        # Merge common files and currently managed files
        all_dotfiles = sorted(list(set(common_files) | managed_files))

        for file_rel in all_dotfiles:
            abs_path = os.path.join(home, file_rel)
            
            # If the file exists on system or is already managed by chezmoi
            is_managed = file_rel in managed_files
            if os.path.exists(abs_path) or is_managed:
                # Format text as a visual directory tree
                parts = file_rel.split("/")
                basename = parts[-1]
                depth = len(parts) - 1
                
                # Add padding for folder depth
                indent = "    " * depth
                
                # Check type
                if os.path.isdir(abs_path):
                    display_text = f"{indent}📁 {basename}"
                else:
                    display_text = f"{indent}📄 {basename}"
                
                item = QListWidgetItem(display_text)
                item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
                if is_managed:
                    item.setCheckState(Qt.CheckState.Checked)
                else:
                    item.setCheckState(Qt.CheckState.Unchecked)
                
                item.setData(Qt.ItemDataRole.UserRole, abs_path)
                self.list_widget.addItem(item)

        self.list_widget.blockSignals(False)
        self.footer.setText(f"Tracking {len(managed_files)} dotfile(s) via chezmoi")

    def on_item_changed(self, item):
        abs_path = item.data(Qt.ItemDataRole.UserRole)
        is_checked = item.checkState() == Qt.CheckState.Checked
        
        self.list_widget.setEnabled(False)
        self.footer.setText("Updating chezmoi tracking state...")

        self.proc = QProcess()
        if is_checked:
            # chezmoi add
            self.proc.start("chezmoi", ["add", "--force", abs_path])
        else:
            # chezmoi forget
            self.proc.start("chezmoi", ["forget", "--force", abs_path])

        self.proc.finished.connect(self.on_chezmoi_action_finished)

    def on_chezmoi_action_finished(self, exit_code, status):
        self.list_widget.setEnabled(True)
        if exit_code == 0:
            self.status_message.emit("Chezmoi tracking updated successfully.")
        else:
            self.status_message.emit("⚠️ Chezmoi command execution failed.")
        self.load_dotfiles()

    def browse_and_add(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Dotfile to Track", os.path.expanduser("~"), "All Files (*)"
        )
        if file_path:
            # Verify file is in user home directory
            home = os.path.expanduser("~")
            if not file_path.startswith(home):
                QMessageBox.warning(self, "Invalid Path", "Chezmoi can only track files inside your user home directory.")
                return

            self.list_widget.setEnabled(False)
            self.footer.setText(f"Adding {os.path.basename(file_path)} to chezmoi...")
            
            self.proc = QProcess()
            self.proc.start("chezmoi", ["add", "--force", file_path])
            self.proc.finished.connect(self.on_chezmoi_action_finished)


class SettingsTab(QWidget):
    status_message = pyqtSignal(str)
    reset_requested = pyqtSignal()
    run_action_requested = pyqtSignal(list, str) # Emits cmd args, and action description label

    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(25, 25, 25, 25)
        layout.setSpacing(18)
        self.setLayout(layout)

        # Title
        title = QLabel("Application Settings")
        title.setObjectName("sectionTitle")
        layout.addWidget(title)

        # GitHub Remote Edit
        remote_box = QWidget()
        remote_layout = QVBoxLayout(remote_box)
        remote_layout.setContentsMargins(0, 0, 0, 0)
        remote_layout.setSpacing(6)
        
        remote_label = QLabel("GitHub Remote Repository URL:")
        self.remote_input = QLineEdit()
        self.remote_input.setObjectName("formInput")
        
        save_remote_btn = QPushButton("Save Remote URL")
        save_remote_btn.setObjectName("secondaryBtn")
        save_remote_btn.clicked.connect(self.save_remote_url)

        remote_layout.addWidget(remote_label)
        remote_layout.addWidget(self.remote_input)
        remote_layout.addWidget(save_remote_btn)
        layout.addWidget(remote_box)

        layout.addSpacing(10)

        # Action Buttons
        actions_title = QLabel("System Maintenance Actions")
        actions_title.setObjectName("subSectionTitle")
        layout.addWidget(actions_title)

        # Regenerate Baseline Button
        self.baseline_btn = QPushButton("Regenerate Packages Baseline Snapshot")
        self.baseline_btn.setObjectName("settingsActionBtn")
        self.baseline_btn.clicked.connect(self.regenerate_baseline)
        layout.addWidget(self.baseline_btn)

        layout.addStretch()

        # Danger zone / Reset
        danger_title = QLabel("Danger Zone")
        danger_title.setObjectName("dangerZoneTitle")
        layout.addWidget(danger_title)

        self.reset_btn = QPushButton("Reset Application (Factory Reset)")
        self.reset_btn.setObjectName("dangerBtn")
        self.reset_btn.clicked.connect(self.reset_application)
        layout.addWidget(self.reset_btn)

    def load_settings(self):
        config = load_gui_config()
        self.remote_input.setText(config.get("GITHUB_REMOTE", ""))

    def save_remote_url(self):
        new_url = self.remote_input.text().strip()
        config = load_gui_config()
        config["GITHUB_REMOTE"] = new_url
        
        if save_gui_config(config):
            # Also update Git remote URL in local git repo
            backup_repo = config.get("BACKUP_REPO", "")
            if backup_repo and os.path.exists(os.path.join(backup_repo, ".git")):
                try:
                    subprocess.run(["git", "-C", backup_repo, "remote", "set-url", "origin", new_url])
                    self.status_message.emit("Saved Remote URL and successfully updated git repository origin.")
                except Exception as e:
                    self.status_message.emit(f"Saved Remote URL locally, but failed to update git remote: {e}")
            else:
                self.status_message.emit("Saved configuration file successfully.")
        else:
            QMessageBox.critical(self, "Error", "Failed to update configuration file.")

    def regenerate_baseline(self):
        reply = QMessageBox.question(
            self, "Regenerate Baseline",
            "Are you sure you want to capture a new baseline snapshot of current installed packages?\n\nThis will overwrite baseline-official.txt and baseline-foreign.txt.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            cmd = [resolve_script_path("cachyos-backup"), "--baseline"]
            self.run_action_requested.emit(cmd, "Regenerating Baseline Snapshot")

    def reset_application(self):
        reply = QMessageBox.warning(
            self, "Reset Application",
            "This will delete the configuration file (~/.config/cachyos-backup/config) and reset the application back to the onboarding welcome flow.\n\nAre you sure you want to continue?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            try:
                if os.path.exists(CONFIG_PATH):
                    os.remove(CONFIG_PATH)
                self.status_message.emit("Application has been reset successfully.")
                self.reset_requested.emit()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to reset application configuration: {e}")


class AboutTab(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        self.setLayout(layout)

        self.browser = QTextBrowser()
        self.browser.setObjectName("aboutBrowser")
        layout.addWidget(self.browser)

    def load_readme(self):
        # Resolve README.md location
        # Check in project root, or fall back to description
        root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        readme_path = os.path.join(root_dir, "README.md")
        
        content = ""
        if os.path.exists(readme_path):
            try:
                with open(readme_path, "r") as f:
                    content = f.read()
            except Exception as e:
                print(f"Error loading README: {e}")
                
        if not content:
            content = """# Arch Backup & Recovery Tool

This graphical application serves as a visual wrapper for local package tracking, configuration dotfiles, and system recovery.

### Features
* **Apps Selection**: Select explicitly installed packages (official and AUR/foreign) to include in your remote backups.
* **Dotfiles Syncing**: Track your shell configuration and other configurations inside your home directory using `chezmoi`.
* **KDE Plasma Profiles**: Backup and restore graphical layout profiles via `konsave`.
* **Disaster Recovery**: Bootstraps fresh machines by automatically installing your backup's package checklist, syncs tracked dotfiles, and restores extras.
"""
        self.browser.setMarkdown(content)


class DashboardWidget(QTabWidget):
    status_message = pyqtSignal(str)
    reset_requested = pyqtSignal()
    run_action_requested = pyqtSignal(list, str) # Emits command and desc label to execute in console

    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        self.setObjectName("mainDashboard")
        
        self.apps_tab = AppsTab()
        self.apps_tab.status_message.connect(self.status_message.emit)
        self.apps_tab.run_backup_requested.connect(self.run_backup)
        self.addTab(self.apps_tab, "📦 Installed Packages")

        self.chezmoi_tab = ChezmoiTab()
        self.chezmoi_tab.status_message.connect(self.status_message.emit)
        self.addTab(self.chezmoi_tab, "🔧 Config Dotfiles")

        self.settings_tab = SettingsTab()
        self.settings_tab.status_message.connect(self.status_message.emit)
        self.settings_tab.reset_requested.connect(self.reset_requested.emit)
        self.settings_tab.run_action_requested.connect(self.run_action_requested.emit)
        self.addTab(self.settings_tab, "⚙️ Settings")

        self.about_tab = AboutTab()
        self.addTab(self.about_tab, "ℹ️ About")

        # Load data on tab change to keep everything synced
        self.currentChanged.connect(self.on_tab_changed)

    def load_dashboard_data(self):
        self.apps_tab.load_packages()
        self.chezmoi_tab.load_dotfiles()
        self.settings_tab.load_settings()
        self.about_tab.load_readme()

    def on_tab_changed(self, index):
        if index == 0:
            self.apps_tab.load_packages()
        elif index == 1:
            self.chezmoi_tab.load_dotfiles()
        elif index == 2:
            self.settings_tab.load_settings()
        elif index == 3:
            self.about_tab.load_readme()

    def run_backup(self, config):
        # Triggers a full cachyos-backup --backup in background console
        cmd = [resolve_script_path("cachyos-backup"), "--backup"]
        self.run_action_requested.emit(cmd, "Performing Package Backup and Sync")
