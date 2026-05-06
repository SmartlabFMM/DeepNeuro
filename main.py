import sys
import os

# Set OpenGL to software mode BEFORE creating QApplication to prevent VTK blocking
# Advanced VTK/PyOpenGL overrides are platform-specific; only apply them on Linux
os.environ["QT_OPENGL"] = "software"
if sys.platform.startswith("linux"):
    os.environ["QT_XCB_GL_INTEGRATION"] = "xcb_glx"
    os.environ["PYOPENGL_PLATFORM"] = "osmesa"  # Force off-screen Mesa rendering for VTK on Linux

from PySide6.QtGui import QGuiApplication, QCursor
from PySide6.QtWidgets import QApplication
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
