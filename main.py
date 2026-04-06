import sys

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication, QMainWindow, QDesktopWidget, QStyleFactory

from gui.main_view_backend import MainView

# Enable High DPI scaling
QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)

# Use high DPI pixmaps (icons look sharper)
QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

if __name__ == "__main__":
    app = QApplication(sys.argv)

    # Apply the Windows theme
    app.setStyle(QStyleFactory.create("Windows"))

    # Screen resolution
    screen_resolution = QDesktopWidget().screenGeometry()

    # Main application window
    main_window = QMainWindow()
    main_window.setWindowTitle("PCB Faults")
    main_window.setMinimumSize(1280, 800)
    main_window.setMaximumSize(screen_resolution.width(), screen_resolution.height())

    # TODO: Change start size if needed
    # main_window.resize(QSize(600, 800))

    # Set the main view as the central widget
    main_view = MainView()
    main_window.setCentralWidget(main_view)

    # Show the main window
    main_window.show()

    # Execute the application
    sys.exit(app.exec_())
