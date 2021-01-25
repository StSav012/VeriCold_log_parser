# -*- coding: utf-8 -*-
from PyQt5.QtWidgets import QApplication

from gui._ui import MainWindow


def run():
    import sys

    app = QApplication(sys.argv)
    window = MainWindow()
    for argv in sys.argv[1:]:
        if window.load_file(argv[len('file:'):] if argv.startswith('file:') else argv):
            break
    window.show()
    app.exec()
