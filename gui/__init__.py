# -*- coding: utf-8 -*-
from typing import Set

from PyQt5.QtCore import QLibraryInfo, QLocale, QTranslator, QUrl
from PyQt5.QtWidgets import QApplication

from gui._ui import MainWindow


def run() -> None:
    import sys

    app: QApplication = QApplication(sys.argv)

    languages: Set[str] = set(QLocale().uiLanguages() + [QLocale().bcp47Name(), QLocale().name()])
    language: str
    qt_translator: QTranslator = QTranslator()
    for language in languages:
        if qt_translator.load('qt_' + language,
                              QLibraryInfo.location(QLibraryInfo.TranslationsPath)):
            app.installTranslator(qt_translator)
            break
    qtbase_translator: QTranslator = QTranslator()
    for language in languages:
        if qtbase_translator.load('qtbase_' + language,
                                  QLibraryInfo.location(QLibraryInfo.TranslationsPath)):
            app.installTranslator(qtbase_translator)
            break

    window: MainWindow = MainWindow(application=app)
    argv: str
    for argv in sys.argv[1:]:
        if window.load_file(QUrl(argv).path()):
            break
    window.show()
    app.exec()
