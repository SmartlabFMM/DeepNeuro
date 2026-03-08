import sys
from PySide6.QtWidgets import QApplication
from auth_window import AuthWindow

def main():
    
    app = QApplication(sys.argv)
    
    
    window = AuthWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == '__main__':
    main()
