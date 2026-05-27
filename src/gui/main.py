import sys
import os
from PyQt6.QtWidgets import QApplication, QMainWindow, QStackedWidget, QWidget, QVBoxLayout, QHBoxLayout, QLabel
from PyQt6.QtGui import QIcon, QPalette, QColor
from PyQt6.QtCore import Qt

from .wizard import OnboardingWizard, ProgressConsole
from .dashboard import DashboardWidget
from .utils import CONFIG_PATH

# Elegant dark-mode Qt Style Sheet (QSS)
DARK_STYLE = """
/* Global defaults */
QWidget {
    background-color: #121214;
    color: #e4e4e7;
    font-family: "Segoe UI", "Inter", "Liberation Sans", sans-serif;
    font-size: 13px;
}

/* Titles and labels */
#welcomeTitle {
    font-size: 26px;
    font-weight: bold;
    color: #ffffff;
    margin-bottom: 5px;
}

#welcomeSubtitle {
    font-size: 14px;
    color: #a1a1aa;
}

#formTitle {
    font-size: 20px;
    font-weight: bold;
    color: #ffffff;
}

#sectionTitle {
    font-size: 18px;
    font-weight: bold;
    color: #ffffff;
}

#subSectionTitle {
    font-size: 14px;
    font-weight: bold;
    color: #e4e4e7;
}

#dangerZoneTitle {
    font-size: 14px;
    font-weight: bold;
    color: #f43f5e;
}

#welcomeFooter {
    font-size: 11px;
    color: #52525b;
}

#validationStatus {
    font-weight: 500;
}

/* Cards on Welcome Screen */
#optionCard {
    background-color: #1c1c22;
    border: 2px solid #2d2d37;
    border-radius: 12px;
    outline: none;
    color: #ffffff;
}

#optionCard:hover {
    border-color: #14b8a6;
    background-color: #22222a;
}

#optionCard QLabel {
    color: #ffffff;
    background: transparent;
}

#optionCard QLabel#cardIcon {
    font-size: 40px;
}

#optionCard QLabel#cardTitle {
    font-size: 16px;
    font-weight: bold;
    color: #ffffff;
}

#optionCard QLabel#cardDesc {
    font-size: 12px;
    color: #a1a1aa;
}

/* Form items & Group boxes */
#formGroup {
    font-weight: bold;
    color: #ffffff;
    border: 1px solid #2d2d37;
    border-radius: 8px;
    margin-top: 15px;
    padding-top: 15px;
}

#formGroup::title {
    subcontrol-origin: margin;
    left: 10px;
    padding: 0 5px 0 5px;
}

#formInput {
    background-color: #1c1c22;
    border: 1px solid #2d2d37;
    border-radius: 6px;
    padding: 8px 12px;
    color: #ffffff;
}

#formInput:focus {
    border: 1px solid #14b8a6;
}

/* Standard Buttons */
QPushButton {
    border-radius: 6px;
    padding: 8px 16px;
    font-weight: 600;
    color: #e4e4e7;
}

#primaryBtn {
    background-color: #14b8a6;
    color: #0f172a;
    border: none;
}

#primaryBtn:hover {
    background-color: #0d9488;
}

#primaryBtn:disabled {
    background-color: #3f3f46;
    color: #71717a;
}

#secondaryBtn {
    background-color: #1c1c22;
    border: 1px solid #2d2d37;
    color: #e4e4e7;
}

#secondaryBtn:hover {
    background-color: #27272a;
    border-color: #3f3f46;
}

#secondaryBtn:disabled {
    color: #52525b;
    border-color: #27272a;
}

#smallActionBtn {
    background-color: #0e7490;
    color: #ffffff;
    font-size: 11px;
    padding: 4px 10px;
    border: none;
    border-radius: 4px;
}

#smallActionBtn:hover {
    background-color: #0891b2;
}

#settingsActionBtn {
    background-color: #27272a;
    border: 1px solid #3f3f46;
    color: #ffffff;
    padding: 10px;
    text-align: left;
}

#settingsActionBtn:hover {
    background-color: #3f3f46;
    border-color: #52525b;
}

#dangerBtn {
    background-color: #991b1b;
    color: #ffffff;
    border: none;
}

#dangerBtn:hover {
    background-color: #b91c1c;
}

/* Checkboxes */
QCheckBox {
    spacing: 8px;
}

QCheckBox::indicator {
    width: 18px;
    height: 18px;
    border: 1px solid #2d2d37;
    border-radius: 4px;
    background-color: #1c1c22;
}

QCheckBox::indicator:hover {
    border-color: #14b8a6;
}

QCheckBox::indicator:checked {
    background-color: #14b8a6;
    image: url(no-image); /* Workaround to prevent default check icon if styling is customized */
    border-color: #14b8a6;
}

/* Checkbox interior check symbol */
QCheckBox::indicator:checked {
    border: 1px solid #14b8a6;
    background-color: #14b8a6;
    /* Use Unicode character styling checkmark by using a check representation */
}

/* Tabs */
QTabWidget::pane {
    border: 1px solid #2d2d37;
    background-color: #121214;
    border-radius: 8px;
    top: -1px;
}

QTabBar::tab {
    background-color: #1c1c22;
    border: 1px solid #2d2d37;
    border-bottom: none;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
    padding: 8px 16px;
    color: #a1a1aa;
    margin-right: 2px;
}

QTabBar::tab:selected {
    background-color: #121214;
    color: #ffffff;
    border-color: #2d2d37;
    font-weight: bold;
}

QTabBar::tab:hover:!selected {
    background-color: #22222a;
    color: #e4e4e7;
}

/* Scrolllists and list items */
QListWidget {
    background-color: #1c1c22;
    border: 1px solid #2d2d37;
    border-radius: 8px;
    padding: 5px;
}

QListWidget::item {
    border-bottom: 1px solid #27272a;
    padding: 8px;
    border-radius: 4px;
}

QListWidget::item:hover {
    background-color: #27272a;
}

QListWidget::item:selected {
    background-color: #0f172a;
    color: #ffffff;
}

/* Console and Scrollbars */
#consoleOutput {
    background-color: #09090b;
    border: 1px solid #27272a;
    border-radius: 8px;
    color: #22c55e; /* Vibrant terminal green */
    padding: 10px;
}

#consoleProgress::chunk {
    background-color: #14b8a6;
    border-radius: 2px;
}

#consoleProgress {
    border: 1px solid #27272a;
    border-radius: 4px;
    text-align: center;
    background-color: #09090b;
    color: #ffffff;
    font-weight: bold;
    height: 15px;
}

/* Scrollbars styling */
QScrollBar:vertical {
    border: none;
    background-color: #121214;
    width: 10px;
    margin: 0px;
}

QScrollBar::handle:vertical {
    background-color: #2d2d37;
    min-height: 20px;
    border-radius: 5px;
}

QScrollBar::handle:vertical:hover {
    background-color: #14b8a6;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    border: none;
    background: none;
}
"""

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Package Backup & Recovery")
        self.resize(850, 680)

        # Set default window icon if available
        self.setWindowIcon(QIcon.fromTheme("system-software-update"))

        # Root layouts
        self.stacked_widget = QStackedWidget()
        self.setCentralWidget(self.stacked_widget)

        # Initialize core components
        # 0: Onboarding Wizard
        self.onboarding = OnboardingWizard()
        self.onboarding.onboarding_complete.connect(self.load_dashboard_view)
        self.stacked_widget.addWidget(self.onboarding)

        # 1: Dashboard View
        self.dashboard = DashboardWidget()
        self.dashboard.reset_requested.connect(self.load_onboarding_view)
        self.dashboard.run_action_requested.connect(self.run_dashboard_action)
        self.stacked_widget.addWidget(self.dashboard)

        # 2: Dedicated Dashboard Console (to show action logs post-onboarding)
        self.console = ProgressConsole()
        self.console.on_finished.connect(self.return_to_dashboard)
        self.stacked_widget.addWidget(self.console)

        # Perform initial state checking
        self.check_initial_state()

    def check_initial_state(self):
        if os.path.exists(CONFIG_PATH):
            self.load_dashboard_view()
        else:
            self.load_onboarding_view()

    def load_onboarding_view(self):
        self.onboarding.setCurrentIndex(0) # Reset wizard to welcome screen
        self.stacked_widget.setCurrentIndex(0)

    def load_dashboard_view(self):
        self.dashboard.load_dashboard_data()
        self.stacked_widget.setCurrentIndex(1)

    def run_dashboard_action(self, cmd, desc):
        # Switch to console and execute command
        self.stacked_widget.setCurrentIndex(2)
        self.console.start_generic_command(cmd, desc)

    def return_to_dashboard(self):
        # After console completes, reload dashboard lists and return
        self.dashboard.load_dashboard_data()
        self.stacked_widget.setCurrentIndex(1)

def main():
    app = QApplication(sys.argv)
    
    # Force dark fusion style first to ensure consistency across systems
    app.setStyle("Fusion")
    
    # Set dark colors for window system items (e.g. tooltips, menus)
    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window, QColor("#121214"))
    palette.setColor(QPalette.ColorRole.WindowText, QColor("#e4e4e7"))
    palette.setColor(QPalette.ColorRole.Base, QColor("#1c1c22"))
    palette.setColor(QPalette.ColorRole.AlternateBase, QColor("#121214"))
    palette.setColor(QPalette.ColorRole.ToolTipBase, QColor("#1c1c22"))
    palette.setColor(QPalette.ColorRole.ToolTipText, QColor("#ffffff"))
    palette.setColor(QPalette.ColorRole.Text, QColor("#ffffff"))
    palette.setColor(QPalette.ColorRole.Button, QColor("#1c1c22"))
    palette.setColor(QPalette.ColorRole.ButtonText, QColor("#ffffff"))
    palette.setColor(QPalette.ColorRole.BrightText, QColor("#14b8a6"))
    palette.setColor(QPalette.ColorRole.Link, QColor("#14b8a6"))
    palette.setColor(QPalette.ColorRole.Highlight, QColor("#14b8a6"))
    palette.setColor(QPalette.ColorRole.HighlightedText, QColor("#0f172a"))
    app.setPalette(palette)

    # Apply our custom QSS visual styles
    app.setStyleSheet(DARK_STYLE)

    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
