# -*- coding: utf-8 -*-
from typing import Set

from pyqtgraph.Qt import QtCore, QtWidgets

from gui._ui import MainWindow


def run() -> None:
    import sys

    app: QtWidgets.QApplication = QtWidgets.QApplication(sys.argv)

    languages: Set[str] = set(QtCore.QLocale().uiLanguages() + [QtCore.QLocale().bcp47Name(), QtCore.QLocale().name()])
    language: str
    qt_translator: QtCore.QTranslator = QtCore.QTranslator()
    for language in languages:
        if qt_translator.load('qt_' + language,
                              QtCore.QLibraryInfo.location(QtCore.QLibraryInfo.TranslationsPath)):
            app.installTranslator(qt_translator)
            break
    qtbase_translator: QtCore.QTranslator = QtCore.QTranslator()
    for language in languages:
        if qtbase_translator.load('qtbase_' + language,
                                  QtCore.QLibraryInfo.location(QtCore.QLibraryInfo.TranslationsPath)):
            app.installTranslator(qtbase_translator)
            break

    window: MainWindow = MainWindow(application=app)
    argv: str
    for argv in sys.argv[1:]:
        if window.load_file(QtCore.QUrl(argv).path()):
            break
    window.show()
    app.exec()
