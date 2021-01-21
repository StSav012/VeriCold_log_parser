# -*- coding: utf-8 -*-
from datetime import datetime
from typing import List, Optional, Union

import numpy as np

from gui._settings import Settings

try:
    from typing import Final
except ImportError:
    class _Final:
        def __getitem__(self, item):
            return item


    Final = _Final()

from PyQt5.QtCore import QAbstractTableModel, QCoreApplication, QModelIndex, QRect, Qt
from PyQt5.QtGui import QCloseEvent, QIcon
from PyQt5.QtWidgets import QAbstractItemView, QAction, QApplication, QDesktopWidget, QFileDialog, QGridLayout, \
    QHeaderView, \
    QMainWindow, QMenu, \
    QMenuBar, \
    QMessageBox, QStatusBar, QTableView, QWidget

from parser import parse


def copy_to_clipboard(plain_text: str, rich_text: str = '', text_type: Union[Qt.TextFormat, str] = Qt.PlainText):
    from PyQt5.QtGui import QClipboard
    from PyQt5.QtCore import QMimeData

    clipboard: QClipboard = QApplication.clipboard()
    mime_data: QMimeData = QMimeData()
    if isinstance(text_type, str):
        mime_data.setData(text_type, plain_text.encode())
    elif text_type == Qt.RichText:
        mime_data.setHtml(rich_text)
        mime_data.setText(plain_text)
    else:
        mime_data.setText(plain_text)
    clipboard.setMimeData(mime_data, QClipboard.Clipboard)


class DataModel(QAbstractTableModel):
    ROW_BATCH_COUNT: Final[int] = 5

    def __init__(self, parent=None):
        super().__init__(parent)
        self._data: np.ndarray = np.empty((0, 0))
        self._rows_loaded: int = self.ROW_BATCH_COUNT

        self._header: List[str] = []

    @property
    def header(self) -> List[str]:
        return self._header

    def rowCount(self, parent=None) -> int:
        return min(self._data.shape[1], self._rows_loaded)

    def columnCount(self, parent=None) -> int:
        return len(self._header)

    def data(self, index: QModelIndex, role: Qt.ItemDataRole = Qt.DisplayRole) -> Optional[str]:
        if index.isValid():
            if role == Qt.DisplayRole:
                value: np.float64 = self.item(index.row(), index.column())
                if self._header[index.column()].endswith(('(s)', '(secs)')):
                    return datetime.fromtimestamp(value).isoformat()
                if self._header[index.column()].endswith('(K)'):
                    return str(np.around(value, decimals=3))
                if self._header[index.column()].endswith('(Bar)'):
                    return np.format_float_positional(value, precision=3 + int(-np.log10(np.abs(value))))
                if value.is_integer():
                    return f'{value:.0f}'
                return str(np.around(value, decimals=12))
        return None

    def item(self, row_index: int, column_index: int) -> np.float64:
        return self._data[column_index + 1, row_index]

    def headerData(self, col, orientation, role: Qt.ItemDataRole = Qt.DisplayRole):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return self._header[col]
        if orientation == Qt.Vertical and role == Qt.DisplayRole:
            return f'{self._data[0, col]:.0f}'
        return None

    def setHeaderData(self, section: int, orientation: Qt.Orientation, value, role: int = ...) -> bool:
        if orientation == Qt.Horizontal and role == Qt.DisplayRole and 0 <= section < len(self._header):
            self._header[section] = value
            return True
        return False

    def set_data(self, new_data: Union[List[List[float]], np.ndarray], new_header: Optional[List[str]] = None):
        self.beginResetModel()
        self._data = np.array(new_data)
        good: np.ndarray = ~np.all(self._data == 0.0, axis=1)
        self._data = self._data[good]
        if new_header is not None:
            self._header = [str(s) for s, g in zip(new_header, good) if g][1:]
        self._rows_loaded = self.ROW_BATCH_COUNT
        self.endResetModel()

    def canFetchMore(self, index: QModelIndex = QModelIndex()):
        return self._data.shape[1] > self._rows_loaded

    def fetchMore(self, index: QModelIndex = QModelIndex()):
        # FIXME: if the 0th column is hidden, to data gets fetched despite it is available according to `canFetchMore`
        # https://sateeshkumarb.wordpress.com/2012/04/01/paginated-display-of-table-data-in-pyqt/
        reminder: int = self._data.shape[1] - self._rows_loaded
        items_to_fetch: int = min(reminder, self.ROW_BATCH_COUNT)
        self.beginInsertRows(QModelIndex(), self._rows_loaded, self._rows_loaded + items_to_fetch - 1)
        self._rows_loaded += items_to_fetch
        self.endInsertRows()


class MainWindow(QMainWindow):
    def __init__(self, parent: Optional[QWidget] = None,
                 flags: Union[Qt.WindowFlags, Qt.WindowType] = Qt.WindowFlags()):
        super().__init__(parent=parent, flags=flags)
        self.central_widget: QWidget = QWidget(self)
        self.main_layout: QGridLayout = QGridLayout(self.central_widget)
        self.table: QTableView = QTableView(self.central_widget)
        self.table_model: DataModel = DataModel(self)
        self.table.setModel(self.table_model)
        self.menu_bar: QMenuBar = QMenuBar(self)
        self.menu_file: QMenu = QMenu(self.menu_bar)
        self.menu_edit: QMenu = QMenu(self.menu_bar)
        self.menu_view: QMenu = QMenu(self.menu_bar)
        self.menu_about: QMenu = QMenu(self.menu_bar)
        self.action_open: QAction = QAction(self)
        self.action_reload: QAction = QAction(self)
        self.action_preferences: QAction = QAction(self)
        self.action_quit: QAction = QAction(self)
        self.action_copy: QAction = QAction(self)
        self.action_select_all: QAction = QAction(self)
        self.action_about: QAction = QAction(self)
        self.action_about_qt: QAction = QAction(self)
        self.status_bar: QStatusBar = QStatusBar(self)

        self._opened_file_name: str = ''
        self.settings: Settings = Settings('SavSoft', 'VeriCold data log viewer', self)
        self._visible_columns: List[str] = []

        self.setupUi()

    def setupUi(self):
        self.setObjectName('main_window')
        self.resize(640, 480)
        self.central_widget.setObjectName('central_widget')
        self.main_layout.setObjectName('main_layout')
        self.table.setAlternatingRowColors(True)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.table.setSelectionMode(QAbstractItemView.ContiguousSelection)
        self.table.setWordWrap(False)
        self.table.setObjectName('table')
        self.table.horizontalHeader().setStretchLastSection(True)
        self.main_layout.addWidget(self.table, 0, 0, 1, 1)
        self.setCentralWidget(self.central_widget)
        self.menu_bar.setGeometry(QRect(0, 0, 800, 29))
        self.menu_bar.setObjectName('menu_bar')
        self.menu_file.setObjectName('menu_file')
        self.menu_view.setObjectName('menu_view')
        self.menu_about.setObjectName('menu_about')
        self.menu_edit.setObjectName('menu_edit')
        self.setMenuBar(self.menu_bar)
        self.status_bar.setObjectName('status_bar')
        self.setStatusBar(self.status_bar)
        icon = QIcon.fromTheme('document-open')
        self.action_open.setIcon(icon)
        self.action_open.setObjectName('actionOpen')
        self.action_preferences.setMenuRole(QAction.PreferencesRole)
        self.action_preferences.setObjectName('action_preferences')
        icon = QIcon.fromTheme('view-refresh')
        self.action_reload.setIcon(icon)
        self.action_reload.setObjectName('action_reload')
        icon = QIcon.fromTheme('application-exit')
        self.action_quit.setIcon(icon)
        self.action_quit.setMenuRole(QAction.QuitRole)
        self.action_quit.setObjectName('action_quit')
        icon = QIcon.fromTheme('edit-copy')
        self.action_copy.setIcon(icon)
        self.action_copy.setObjectName('action_copy')
        icon = QIcon.fromTheme('edit-select-all')
        self.action_select_all.setIcon(icon)
        self.action_select_all.setObjectName('action_select_all')
        icon = QIcon.fromTheme('help-about')
        self.action_about.setIcon(icon)
        self.action_about.setMenuRole(QAction.AboutRole)
        self.action_about.setObjectName('action_about')
        icon = QIcon.fromTheme('help-about-qt')
        self.action_about_qt.setIcon(icon)
        self.action_about_qt.setMenuRole(QAction.AboutQtRole)
        self.action_about_qt.setObjectName('action_about_qt')
        self.menu_file.addAction(self.action_open)
        self.menu_file.addAction(self.action_reload)
        self.menu_file.addSeparator()
        self.menu_file.addAction(self.action_preferences)
        self.menu_file.addSeparator()
        self.menu_file.addAction(self.action_quit)
        self.menu_edit.addAction(self.action_copy)
        self.menu_edit.addAction(self.action_select_all)
        self.menu_about.addAction(self.action_about)
        self.menu_about.addAction(self.action_about_qt)
        self.menu_bar.addAction(self.menu_file.menuAction())
        self.menu_bar.addAction(self.menu_edit.menuAction())
        self.menu_bar.addAction(self.menu_view.menuAction())
        self.menu_bar.addAction(self.menu_about.menuAction())

        self.action_open.triggered.connect(self.on_action_open_triggered)
        self.action_reload.triggered.connect(self.on_action_reload_triggered)
        self.action_quit.triggered.connect(self.on_action_quit_triggered)
        self.action_copy.triggered.connect(self.on_action_copy_triggered)
        self.action_select_all.triggered.connect(self.on_action_select_all_triggered)
        self.action_about.triggered.connect(self.on_action_about_triggered)
        self.action_about_qt.triggered.connect(self.on_action_about_qt_triggered)

        self.translate()

        self.load_settings()

    def translate(self):
        _translate = QCoreApplication.translate
        self.setWindowTitle(_translate('main_window', 'VeriCold data log viewer'))
        self.menu_file.setTitle(_translate('main_window', 'File'))
        self.menu_view.setTitle(_translate('main_window', 'View'))
        self.menu_about.setTitle(_translate('main_window', 'About'))
        self.menu_edit.setTitle(_translate('main_window', 'Edit'))
        self.action_open.setText(_translate('main_window', 'Open...'))
        self.action_open.setShortcut(_translate('main_window', 'Ctrl+O'))
        self.action_reload.setText(_translate('main_window', 'Reload'))
        self.action_reload.setShortcut(_translate('main_window', 'Ctrl+R'))
        self.action_preferences.setText(_translate('main_window', 'Preferences...'))
        self.action_preferences.setShortcut(_translate('main_window', 'Ctrl+,'))
        self.action_quit.setText(_translate('main_window', 'Quit'))
        self.action_quit.setShortcut(_translate('main_window', 'Ctrl+Q'))
        self.action_copy.setText(_translate('main_window', 'Copy'))
        self.action_copy.setShortcut(_translate('main_window', 'Ctrl+C'))
        self.action_select_all.setText(_translate('main_window', 'Select All'))
        self.action_select_all.setShortcut(_translate('main_window', 'Ctrl+A'))
        self.action_about.setText(_translate('main_window', 'About'))
        self.action_about.setShortcut(_translate('main_window', 'F1'))
        self.action_about_qt.setText(_translate('main_window', 'About Qt'))

    def closeEvent(self, event: QCloseEvent) -> None:
        self.save_settings()
        event.accept()

    def load_settings(self) -> None:
        self.settings.beginGroup('columns')
        self._visible_columns = []
        i: int
        for i in range(self.settings.beginReadArray('visible')):
            self.settings.setArrayIndex(i)
            self._visible_columns.append(self.settings.value('name', '', str))
        self.settings.endArray()
        self.settings.endGroup()

        self.settings.beginGroup('window')
        desktop: QDesktopWidget = QApplication.desktop()
        self.move(round(0.5 * (desktop.width() - self.size().width())),
                  round(0.5 * (desktop.height() - self.size().height())))  # Fallback: Center the window
        window_settings = self.settings.value('geometry')
        if window_settings is not None:
            self.restoreGeometry(window_settings)
        window_settings = self.settings.value('state')
        if window_settings is not None:
            self.restoreState(window_settings)
        self.settings.endGroup()

    def save_settings(self) -> None:
        self.settings.beginGroup('columns')
        self.settings.beginWriteArray('visible')
        i: int
        n: str
        for i, n in enumerate(self._visible_columns):
            self.settings.setArrayIndex(i)
            self.settings.setValue('name', n)
        self.settings.endArray()
        self.settings.endGroup()

        self.settings.beginGroup('window')
        self.settings.setValue('geometry', self.saveGeometry())
        self.settings.setValue('state', self.saveState())
        self.settings.endGroup()
        self.settings.sync()

    def stringify_selection_plain_text(self) -> str:
        """
        Convert selected rows to string for copying as plain text
        :return: the plain text representation of the selected table lines
        """
        text: List[str] = []
        row: Optional[int] = None
        row_texts: List[str] = []
        si: QModelIndex
        for si in self.table.selectionModel().selectedIndexes():
            if row is None:
                row = si.row()
            if row != si.row():
                text.append(self.settings.csv_separator.join(row_texts))
                row_texts = []
            row_texts.append(self.table_model.data(si))
        return self.settings.line_end.join(text)

    def stringify_selection_html(self) -> str:
        """
        Convert selected rows to string for copying as rich text
        :return: the rich text representation of the selected table lines
        """
        text: List[str] = []
        row: Optional[int] = None
        row_texts: List[str] = []
        si: QModelIndex
        for si in self.table.selectionModel().selectedIndexes():
            if row is None:
                row = si.row()
            if row != si.row():
                text.append('<tr>' + self.settings.csv_separator.join(row_texts) + '</tr>' + self.settings.line_end)
                row_texts = []
            row_texts.append('<td>' + self.table_model.data(si) + '</td>')
        return '<table>' + self.settings.line_end + ''.join(text) + '</table>'

    def on_action_open_triggered(self):
        new_file_name, _ = QFileDialog.getOpenFileName(
            self, self.tr('Open'),
            self._opened_file_name,
            f'{self.tr("VeriCold data logfile")} (*.vcl);;{self.tr("All Files")} (*.*)')

        try:
            titles, data = parse(new_file_name)
        except (IOError, RuntimeError) as ex:
            self.status_bar.showMessage(' '.join(ex.args))
            return
        else:
            self._opened_file_name = new_file_name
            self.table_model.set_data(data, titles)
            self.menu_view.clear()
            index: int
            title: str
            for index, title in enumerate(self.table_model.header):
                action: QAction = self.menu_view.addAction(title)
                action.setCheckable(True)
                if not self._visible_columns or title in self._visible_columns:
                    action.setChecked(True)
                    self.table.showColumn(index)
                else:
                    action.setChecked(False)
                    self.table.hideColumn(index)
                action.triggered.connect(self.on_action_column_triggered)
            if not self._visible_columns:
                self._visible_columns = self.table_model.header
            self.status_bar.showMessage(self.tr('Ready'))

    def on_action_column_triggered(self):
        a: QAction
        i: int
        self._visible_columns = []
        for i, a in enumerate(self.menu_view.actions()):
            if a.isChecked():
                self.table.showColumn(i)
                self._visible_columns.append(a.text())
            else:
                self.table.hideColumn(i)

    def on_action_reload_triggered(self):
        try:
            titles, data = parse(self._opened_file_name)
        except (IOError, RuntimeError):
            return
        else:
            self.table_model.set_data(data, titles)

    def on_action_quit_triggered(self):
        self.close()

    def on_action_copy_triggered(self):
        copy_to_clipboard(self.stringify_selection_plain_text(), self.stringify_selection_html(), Qt.RichText)

    def on_action_select_all_triggered(self):
        self.table.selectAll()

    def on_action_about_triggered(self):
        QMessageBox.about(self,
                          self.tr("About VeriCold data log viewer"),
                          "<html><p>"
                          + self.tr("VeriCold data logfiles are created by Oxford Instruments plc.")
                          + "</p><br><p>"
                          + self.tr("VeriCold data log viewer is licensed under the {0}.")
                          .format("<a href='https://www.gnu.org/copyleft/lesser.html'>{0}</a>"
                                  .format(self.tr("GNU LGPL version 3")))
                          + "</p><p>"
                          + self.tr("The source code is available on {0}.").format(
                              "<a href='https://github.com/StSav012/VeriCold_log_parser'>GitHub</a>")
                          + "</p></html>")

    def on_action_about_qt_triggered(self):
        QMessageBox.aboutQt(self)


if __name__ == '__main__':
    import sys

    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
