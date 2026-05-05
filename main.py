import sys
import os
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QGuiApplication, QCursor
from auth_window import AuthWindow
from splash import SplashScreen


def main():
    app = QApplication(sys.argv)

    logo_path = os.path.join(os.path.dirname(__file__), "DeepNeuro logo.png")
    splash = SplashScreen(logo_path=logo_path)
    splash.resize(520, 360)

    screen = QGuiApplication.screenAt(QCursor.pos()) or QGuiApplication.primaryScreen()
    if screen:
        rect = splash.frameGeometry()
        rect.moveCenter(screen.availableGeometry().center())
        splash.move(rect.topLeft())

    splash.show()

    def _show_auth():
        window = AuthWindow()
        window.show()
        app._main_window = window
        splash.close()

    splash.finished.connect(_show_auth)

    sys.exit(app.exec())


if __name__ == '__main__':
    main()
