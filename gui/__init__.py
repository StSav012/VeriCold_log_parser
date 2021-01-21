# -*- coding: utf-8 -*-
import sys

from PyQt5.QtWidgets import QApplication

from gui._ui import MainWindow


def run():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    app.exec()
