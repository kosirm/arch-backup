# Package Backup and Recovery System

Welcome! This system helps you automatically back up your installed packages, application lists, and system dotfiles (configurations) on any Arch-based Linux (even if it was primarily intended for my CachyOS), and restore them quickly if you ever need to install fresh system. Program can be used either commandline or with a GUI.
To install GUI on Arch Linux:

   ```bash
   yay -S arch-backup-tool-git
   ```

---

## Table of Contents
- [Package Backup and Recovery System](#package-backup-and-recovery-system)
  - [Table of Contents](#table-of-contents)
  - [How to Install](#how-to-install)
    - [Option A: From the AUR (Recommended)](#option-a-from-the-aur-recommended)
    - [Option B: Manual Installation (From Source)](#option-b-manual-installation-from-source)
  - [Step 1: Set Up Your GitHub Repository](#step-1-set-up-your-github-repository)
  - [Step 2: Initialize and Start Backups](#step-2-initialize-and-start-backups)
  - [How to initialize on old system (many apps installed)](#how-to-initialize-on-old-system-many-apps-installed)
  - [How Your Backups Run Automatically](#how-your-backups-run-automatically)
  - [How to Customize Your Configuration](#how-to-customize-your-configuration)
  - [If you want to use it together with Chezmoi:](#if-you-want-to-use-it-together-with-chezmoi)
  - [If you DO NOT want to use it with Chezmoi:](#if-you-do-not-want-to-use-it-with-chezmoi)
  - [Key Settings to Know:](#key-settings-to-know)
  - [How to Recover Everything on a New System](#how-to-recover-everything-on-a-new-system)
    - [Option A: Via the AUR (Recommended)](#option-a-via-the-aur-recommended)
    - [Option B: Directly from GitHub (Without installing first)](#option-b-directly-from-github-without-installing-first)
  - [Command Flags for Advanced Recovery](#command-flags-for-advanced-recovery)
  - [How to back up KDE Plasma settings?](#how-to-back-up-kde-plasma-settings)
    - [Automated Backup (Easiest)](#automated-backup-easiest)
    - [Manual Command-Line Backup (Alternative)](#manual-command-line-backup-alternative)
  - [How to Uninstall](#how-to-uninstall)

---

## How to Install

### Option A: From the AUR (Recommended)
If you are on Arch Linux or CachyOS, you can install the package directly from the AUR using an AUR helper like `yay` or `paru`:
```bash
yay -S arch-backup-tool-git
```

### Option B: Manual Installation (From Source)
If you prefer to install manually from source:
1. Open your terminal.
2. Clone this repository and navigate to it:
   ```bash
   git clone https://github.com/kosirm/arch-backup.git
   cd arch-backup
   ```
3. Run the installation script with administrator (`sudo`) privileges:
   ```bash
   chmod +x install.sh uninstall.sh
   sudo ./install.sh
   ```

*What this does:* This installs the system command-line utilities (`cachyos-backup` and `cachyos-recovery`), the Pacman hook for automated changes tracking, and the daily backup automation timers.

---

## Step 1: Set Up Your GitHub Repository

To keep your backup data safe in the cloud (so you can access it on a fresh machine), we store it in a GitHub repository.

1. Go to [github.com](https://github.com) and log in (or create a free account).
2. In the top-right corner, click the **`+`** icon and select **New repository**.
3. Fill out the details:
   * **Repository name**: We recommend `cachyos-backup`.
   * **Public/Private**: We **strongly recommend choosing Private** so your system details and personal configurations are not visible to the public.
   * **Initialize repository**: Do **NOT** add a README, `.gitignore`, or license. Keep it completely empty.
4. Click **Create repository**.
5. Once created, copy your repository's URL. It will look like one of these:
   * **HTTPS:** `https://github.com/your-username/cachyos-backup.git`
   * **SSH:** `git@github.com:your-username/cachyos-backup.git` (Recommended if you already have SSH keys set up).

---

## Step 2: Initialize and Start Backups

Once you have your GitHub URL, you can link the system to it and take your first snapshot.

1. Run the initialization command:
   ```bash
   cachyos-backup --init
   ```
2. The terminal will ask you for two things:
   * **Backup repository path**: Press `Enter` to accept the default (`~/cachyos-backup`).
   * **GitHub remote URL**: Paste the GitHub repository URL you copied in Step 1.

3. Capture your system's "baseline state" (the starting state of official and AUR packages):
   ```bash
   cachyos-backup --baseline
   ```
4. Now, trigger the first full backup to push all package list files to your GitHub repository:
   ```bash
   cachyos-backup --backup
   ```
5. Check your GitHub repository in your web browser. You will see new text files like `user-official.txt` and `user-foreign.txt` representing your customized package changes!

---

## How to initialize on old system (many apps installed)

1. Run the initialization command:
   ```bash
      cachyos-backup --init
   ```

2. Instead of running --baseline, run these commands to create completely blank baseline files in your local backup folder:

   ```bash
      mkdir -p ~/cachyos-backup
      touch ~/cachyos-backup/baseline-official.txt ~/cachyos-backup/baseline-foreign.txt
   ```

3. Run the backup:
   ```bash
      cachyos-backup --backup
   ```

***Why this works***: Because the baseline files are empty, the system subtracts nothing from your current packages. This forces the backup tool to treat every single package currently on your system as user-added, saving your entire list of packages into user-official.txt and user-foreign.txt and uploading it to GitHub.

--- 

## How Your Backups Run Automatically

You don't need to manually run backups anymore! The system handles it for you:
* **Whenever you install, update, or remove software**: A system hook runs automatically after the transaction is complete, updating your package lists and pushing the changes to GitHub.
* **Every Day**: A background service automatically checks and backs up any extra app store packages (Flatpak, Pip, NPM, Cargo) and pushes them.

---

## How to Customize Your Configuration

You can customize your backup behavior at any time by editing the configuration file located at `~/.config/cachyos-backup/config`.

Open it in a text editor (like Nano or your favorite GUI text editor):
```bash
nano ~/.config/cachyos-backup/config
```
---

## If you want to use it together with Chezmoi:

**What it does:** It backs up your custom settings (like your terminal configurations, app preferences, shortcut keys, themes, etc.).

**If you don't have chezmoi installed**: 
```bash
sudo pacman -S chezmoi
```

Tell Chezmoi which files you want it to track (for example, your bash configuration):
```bash
chezmoi add ~/.bashrc
```

- **Our system** will automatically detect Chezmoi, pull any updates to those configurations when you make changes, and push them to your GitHub backup repository.
- **On a new machine**, cachyos-recovery will automatically restore all of those settings right back to where they belong.

---

## If you DO NOT want to use it with Chezmoi:

- **The system** will still work completely fine for package backups!
- **It will print** a warning that chezmoi is missing, skip dotfile synchronization, and continue to safely back up your list of packages (official apps, AUR helper apps, Flatpaks, Pip, NPM, Cargo).
- **On a fresh machine**, it will reinstall all of your apps, but the apps will start with their default settings rather than your customized configurations.

---

## Key Settings to Know:

* **`AUR_HELPER`**: Set to `"yay"` or `"paru"` depending on which helper you prefer to use for AUR packages (Default: `yay`).
* **`EXTRAS_ENABLED`**: A list of non-standard package managers to track. Add or remove names separated by spaces, like:
  ```bash
  EXTRAS_ENABLED="flatpak pip cargo npm"
  ```
  *(Leave it empty if you only want to back up standard pacman/AUR packages).*
* **`CHEZMOI_SOURCE`**: If you use `chezmoi` to manage your dotfiles, this points to your chezmoi directory (default is standard chezmoi home).

---

## How to Recover Everything on a New System

If you are on a completely new system (or just reinstalled your OS) and want to recover all your packages, configurations, and settings:

### Option A: Via the AUR (Recommended)
1. Install the tool from the AUR:
   ```bash
   yay -S arch-backup-tool-git
   ```
2. Run the recovery tool using your backup GitHub URL:
   ```bash
   cachyos-recovery --repo https://github.com/your-username/my-cachyos-backup.git
   ```

### Option B: Directly from GitHub (Without installing first)
1. Download the recovery script from this repository:
   ```bash
   curl -sSfL https://raw.githubusercontent.com/kosirm/arch-backup/main/src/cachyos-recovery -o cachyos-recovery
   chmod +x cachyos-recovery
   ```
2. Run the recovery tool to clone and restore everything:
   ```bash
   ./cachyos-recovery --repo https://github.com/your-username/my-cachyos-backup.git
   ```
---

## Command Flags for Advanced Recovery

You can add these flags to the recovery command if you wish to adjust the process:
* **`--dry-run`**: Shows you everything that would be installed without actually installing anything. Use this first if you want to double-check!
  ```bash
  ~/cachyos-backup/cachyos-recovery --local ~/cachyos-backup --dry-run
  ```
* **`--skip-dotfiles`**: Skips restoring configuration dotfiles (chezmoi).
* **`--skip-extras`**: Skips restoring Flatpak, NPM, Pip, and Cargo packages.
* **`--aur-helper paru`**: Force-uses `paru` instead of `yay` to install AUR packages during recovery.

Once the recovery completes, it will print a friendly summary showing exactly how many packages were successfully installed, skipped (already present), or failed.

---

## How to back up KDE Plasma settings?

### Automated Backup (Easiest)
If **Use Konsave** is enabled in Settings (or configured in `~/.config/cachyos-backup/config`), the background daily timer (or the **Execute Daily Backup Routine Instantly** button in Settings) will automatically:
1. Capture your active KDE Plasma configurations to a profile named `cachyos-kde-profile`.
2. Compute a directory hash to check if configurations have changed.
3. Export the profile to `cachyos-kde-profile.knsv` inside your backup repository and push it to GitHub if changes are detected.

During restoration, `cachyos-recovery` will automatically import the profile. You can then apply it using:
```bash
konsave -a cachyos-kde-profile
```

### Manual Command-Line Backup (Alternative)
If you want to manage desktop settings profiles manually:
 1. Install Konsave:
    ```bash
    sudo pacman -S konsave
    ```
 2. Save your current setup as a profile (e.g. `my-kde-setup`):
    ```bash
    konsave -s my-kde-setup
    ```
 3. Export the profile to a single archive file:
    ```bash
    konsave -e my-kde-setup
    ```
    *(This creates a `.knsv` file in your home directory, e.g. `~/my-kde-setup.knsv`).*
 4. Add the exported file to Chezmoi so it is tracked:
    ```bash
    chezmoi add ~/my-kde-setup.knsv
    ```

**On a fresh system**, after restoring, apply the profile manually using:
```bash
konsave -i ~/my-kde-setup.knsv
konsave -a my-kde-setup
```
This restores all your wallpapers, widgets, panels, and shortcuts at once!

---

## How to Uninstall

If you wish to remove the backup automation, hook, and command line tools from your machine:

1. Open your terminal and go to the directory:
   ```bash
   cd ~/<download-location>/cachyos-package-backup
   ```
2. Run the uninstaller:
   ```bash
   sudo ./uninstall.sh
   ```

*Note:* To protect your backup data, uninstalling only removes the automation and tools from system folders. It **preserves** your local configuration folder (`~/.config/cachyos-backup`) and local backup data folder (`~/cachyos-backup`). If you want to remove them too, you can delete them manually.

