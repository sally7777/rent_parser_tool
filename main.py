import sys
from PyQt5 import QtWidgets
import PyQt5.QtGui as qg
from PyQt5.QtWidgets import QApplication
from UI.Poster_UI import Ui_RentAutoPoster
from UI_control import MainWindow_controller
"""打包成exe檔
pip install pyinstaller
打包成exe
pyinstaller -D --name=rent_tool main.py
"""

class App(QtWidgets.QMainWindow, Ui_RentAutoPoster):
    def __init__(self, parent=None):
        super(App, self).__init__(parent)
        self.setupUi(self)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    form = App()
    window = MainWindow_controller()
    window.setWindowTitle("台灣房屋--台中區發文小工具 V1.0")
    window.setWindowIcon(qg.QIcon("./picture/home.png"))
    window.show()
    sys.exit(app.exec_())
