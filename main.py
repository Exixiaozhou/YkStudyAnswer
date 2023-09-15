import sys
from MyLib.gui import YkGui
from PySide2.QtWidgets import QApplication


if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    ykGuiObj = YkGui()
    ykGuiObj.ui.show()
    sys.exit(app.exec_())

