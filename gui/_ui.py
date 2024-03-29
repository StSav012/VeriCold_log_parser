# -*- coding: utf-8 -*-
from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Callable, Optional, cast

import numpy as np
from pyqtgraph.Qt import QtCore, QtGui, QtWidgets

from gui._data_model import DataModel
from gui._plot import Plot
from gui._preferences import Preferences
from gui._settings import Settings
from log_parser import parse


def copy_to_clipboard(plain_text: str, rich_text: str = '',
                      text_type: QtCore.Qt.TextFormat | str = QtCore.Qt.TextFormat.PlainText) -> None:
    clipboard: QtGui.QClipboard = QtWidgets.QApplication.clipboard()
    mime_data: QtCore.QMimeData = QtCore.QMimeData()
    if isinstance(text_type, str):
        mime_data.setData(text_type, plain_text.encode())
    elif text_type == QtCore.Qt.TextFormat.RichText:
        mime_data.setHtml(rich_text)
        mime_data.setText(plain_text)
    else:
        mime_data.setText(plain_text)
    clipboard.setMimeData(mime_data, QtGui.QClipboard.Clipboard)


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, application: Optional[QtWidgets.QApplication] = None,
                 parent: Optional[QtWidgets.QWidget] = None) -> None:
        super().__init__(parent=parent)
        self.central_widget: QtWidgets.QWidget = QtWidgets.QWidget(self)
        self.main_layout: QtWidgets.QGridLayout = QtWidgets.QGridLayout(self.central_widget)
        self.table: QtWidgets.QTableView = QtWidgets.QTableView(self.central_widget)
        self.table_model: DataModel = DataModel(self)
        self.table.setModel(self.table_model)
        self.menu_bar: QtWidgets.QMenuBar = QtWidgets.QMenuBar(self)
        self.menu_file: QtWidgets.QMenu = QtWidgets.QMenu(self.menu_bar)
        self.menu_edit: QtWidgets.QMenu = QtWidgets.QMenu(self.menu_bar)
        self.menu_view: QtWidgets.QMenu = QtWidgets.QMenu(self.menu_bar)
        self.menu_plot: QtWidgets.QMenu = QtWidgets.QMenu(self.menu_bar)
        self.menu_about: QtWidgets.QMenu = QtWidgets.QMenu(self.menu_bar)
        self.action_open: QtGui.QAction = QtGui.QAction(self)
        self.action_export: QtGui.QAction = QtGui.QAction(self)
        self.action_reload: QtGui.QAction = QtGui.QAction(self)
        self.action_preferences: QtGui.QAction = QtGui.QAction(self)
        self.action_quit: QtGui.QAction = QtGui.QAction(self)
        self.action_copy: QtGui.QAction = QtGui.QAction(self)
        self.action_copy_all: QtGui.QAction = QtGui.QAction(self)
        self.action_select_all: QtGui.QAction = QtGui.QAction(self)
        self.action_show_plot: QtGui.QAction = QtGui.QAction(self)
        self.action_about: QtGui.QAction = QtGui.QAction(self)
        self.action_about_qt: QtGui.QAction = QtGui.QAction(self)
        self.status_bar: QtWidgets.QStatusBar = QtWidgets.QStatusBar(self)

        self._opened_file_name: str = ''
        self._exported_file_name: str = ''
        self.settings: Settings = Settings('SavSoft', 'VeriCold data log viewer', self)
        if application is not None and self.settings.translation_path is not None:
            translator: QtCore.QTranslator = QtCore.QTranslator(self)
            translator.load(str(self.settings.translation_path))
            application.installTranslator(translator)

        self.setup_ui()

    def setup_ui(self) -> None:
        # https://ru.stackoverflow.com/a/1032610
        window_icon: QtGui.QPixmap = QtGui.QPixmap()
        window_icon.loadFromData(b'''\
                    <svg version="1.1" viewBox="0 0 135 135" xmlns="http://www.w3.org/2000/svg">\
                    <path d="m0 0h135v135h-135v-135" fill="#282e70"/>\
                    <path d="m23 51c3.4-8.7 9.4-16 17-22s17-8.2 26-8.2c9.3 0 19 2.9 26 8.2 7.7 5.3 14 13 17 22 4.1 11 \
                    4.1 23 0 33-3.4 8.7-9.4 16-17 22-7.7 5.3-17 8.2-26 8.2-9.3 0-19-2.9-26-8.2s-14-13-17-22" \
                    fill="none" stroke="#fff" stroke-linecap="round" stroke-width="19"/>\
                    <path d="m50 31c-.58-1.1 6.3-7.5 21-7.8 6.5-.15 14 1.3 22 5.7 6.3 3.6 12 9.1 16 16 3.8 6.6 6 14 \
                    6.1 23v4e-6c-.003 8.2-2.3 16-6.1 23-4.2 7.3-10 13-16 16-7.7 4.4-16 5.8-22 \
                    5.7l-5e-6-1e-5c-14-.33-21-6.7-21-7.8.58-1.1 8.3 2.5 20 1.2 0-1e-5 4e-6-1e-5 \
                    4e-6-1e-5 5.5-.62 12-2.5 18-6.5 4.9-3.2 9.4-7.9 13-14 2.8-5.2 4.5-11 \
                    4.5-18v-2e-6c.003-6.4-1.7-13-4.5-18-3.1-5.8-7.7-11-13-14-5.9-4-12-5.8-18-6.5-12-1.4-20 \
                    2.3-20 1.2z" fill="#282e70"/></svg>\
                    ''', 'SVG')
        self.setWindowIcon(QtGui.QIcon(QtGui.QPixmap(window_icon)))

        self.setObjectName('main_window')
        self.resize(640, 480)
        self.central_widget.setObjectName('central_widget')
        self.main_layout.setObjectName('main_layout')
        self.table.setAlternatingRowColors(True)
        self.table.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.ResizeToContents)
        self.table.setWordWrap(False)
        self.table.setObjectName('table')
        self.table.horizontalHeader().setStretchLastSection(True)
        self.main_layout.addWidget(self.table, 0, 0, 1, 1)
        self.setCentralWidget(self.central_widget)
        self.menu_bar.setGeometry(QtCore.QRect(0, 0, 800, 29))
        self.menu_bar.setObjectName('menu_bar')
        self.menu_file.setObjectName('menu_file')
        self.menu_edit.setObjectName('menu_edit')
        self.menu_view.setObjectName('menu_view')
        self.menu_plot.setObjectName('menu_plot')
        self.menu_about.setObjectName('menu_about')
        self.setMenuBar(self.menu_bar)
        self.status_bar.setObjectName('status_bar')
        self.setStatusBar(self.status_bar)
        self.action_open.setIcon(QtGui.QIcon.fromTheme('document-open'))
        self.action_open.setObjectName('action_open')
        self.action_export.setIcon(QtGui.QIcon.fromTheme('document-save-as'))
        self.action_export.setObjectName('action_export')
        self.action_reload.setIcon(QtGui.QIcon.fromTheme('view-refresh'))
        self.action_reload.setObjectName('action_reload')
        self.action_preferences.setMenuRole(QtGui.QAction.MenuRole.PreferencesRole)
        self.action_preferences.setObjectName('action_preferences')
        self.action_quit.setIcon(QtGui.QIcon.fromTheme('application-exit'))
        self.action_quit.setMenuRole(QtGui.QAction.MenuRole.QuitRole)
        self.action_quit.setObjectName('action_quit')
        self.action_copy.setIcon(QtGui.QIcon.fromTheme('edit-copy'))
        self.action_copy.setObjectName('action_copy')
        self.action_copy_all.setIcon(QtGui.QIcon.fromTheme('edit-copy'))
        self.action_copy_all.setObjectName('action_copy')
        self.action_select_all.setIcon(QtGui.QIcon.fromTheme('edit-select-all'))
        self.action_select_all.setObjectName('action_select_all')
        self.action_show_plot.setMenuRole(QtGui.QAction.MenuRole.ApplicationSpecificRole)
        self.action_show_plot.setObjectName('action_show_about')
        self.action_about.setIcon(QtGui.QIcon.fromTheme('help-about'))
        self.action_about.setMenuRole(QtGui.QAction.MenuRole.AboutRole)
        self.action_about.setObjectName('action_about')
        self.action_about_qt.setIcon(QtGui.QIcon.fromTheme('help-about-qt'))
        self.action_about_qt.setMenuRole(QtGui.QAction.MenuRole.AboutQtRole)
        self.action_about_qt.setObjectName('action_about_qt')
        self.menu_file.addAction(self.action_open)
        self.menu_file.addAction(self.action_export)
        self.menu_file.addAction(self.action_reload)
        self.menu_file.addSeparator()
        self.menu_file.addAction(self.action_preferences)
        self.menu_file.addSeparator()
        self.menu_file.addAction(self.action_quit)
        self.menu_edit.addAction(self.action_copy)
        self.menu_edit.addAction(self.action_copy_all)
        self.menu_edit.addAction(self.action_select_all)
        self.menu_plot.addAction(self.action_show_plot)
        self.menu_about.addAction(self.action_about)
        self.menu_about.addAction(self.action_about_qt)
        self.menu_bar.addAction(self.menu_file.menuAction())
        self.menu_bar.addAction(self.menu_edit.menuAction())
        self.menu_bar.addAction(self.menu_view.menuAction())
        self.menu_bar.addAction(self.menu_plot.menuAction())
        self.menu_bar.addAction(self.menu_about.menuAction())

        self.menu_view.setEnabled(False)
        self.menu_plot.setEnabled(False)
        self.action_export.setEnabled(False)
        self.action_reload.setEnabled(False)

        self.action_open.setShortcut('Ctrl+O')
        self.action_export.setShortcuts(('Ctrl+S', 'Ctrl+E'))
        self.action_reload.setShortcuts(('Ctrl+R', 'F5'))
        self.action_preferences.setShortcut('Ctrl+,')
        self.action_quit.setShortcuts(('Ctrl+Q', 'Ctrl+X'))
        self.action_copy.setShortcut('Ctrl+C')
        self.action_copy_all.setShortcut('Ctrl+Shift+C')
        self.action_select_all.setShortcut('Ctrl+A')
        self.action_about.setShortcut('F1')

        self.action_open.triggered.connect(self.on_action_open_triggered)
        self.action_export.triggered.connect(self.on_action_export_triggered)
        self.action_reload.triggered.connect(self.on_action_reload_triggered)
        self.action_preferences.triggered.connect(self.on_action_preferences_triggered)
        self.action_quit.triggered.connect(self.on_action_quit_triggered)
        self.action_copy.triggered.connect(self.on_action_copy_triggered)
        self.action_copy_all.triggered.connect(self.on_action_copy_all_triggered)
        self.action_select_all.triggered.connect(self.on_action_select_all_triggered)
        self.action_show_plot.triggered.connect(self.on_action_show_plot_triggered)
        self.action_about.triggered.connect(self.on_action_about_triggered)
        self.action_about_qt.triggered.connect(self.on_action_about_qt_triggered)

        self.translate()

        self.load_settings()

    def translate(self) -> None:
        _translate = QtCore.QCoreApplication.translate
        self.setWindowTitle(_translate('main_window', 'VeriCold data log viewer'))
        setattr(self, 'initial_window_title', self.windowTitle())
        self.menu_file.setTitle(_translate('main_window', 'File'))
        self.menu_edit.setTitle(_translate('main_window', 'Edit'))
        self.menu_view.setTitle(_translate('main_window', 'View'))
        self.menu_plot.setTitle(_translate('main_window', 'Plot'))
        self.menu_about.setTitle(_translate('main_window', 'About'))
        self.action_open.setText(_translate('main_window', 'Open...'))
        self.action_export.setText(_translate('main_window', 'Export...'))
        self.action_reload.setText(_translate('main_window', 'Reload'))
        self.action_preferences.setText(_translate('main_window', 'Preferences...'))
        self.action_quit.setText(_translate('main_window', 'Quit'))
        self.action_copy.setText(_translate('main_window', 'Copy'))
        self.action_copy_all.setText(_translate('main_window', 'Copy All from Visible Columns'))
        self.action_select_all.setText(_translate('main_window', 'Select All'))
        self.action_show_plot.setText(_translate('main_window', 'Show'))
        self.action_about.setText(_translate('main_window', 'About'))
        self.action_about_qt.setText(_translate('main_window', 'About Qt'))

    def closeEvent(self, event: QtGui.QCloseEvent) -> None:
        self.save_settings()
        event.accept()

    def load_settings(self) -> None:
        self.settings.beginGroup('location')
        self._opened_file_name = self.settings.value('open', str(Path.cwd()), str)
        self._exported_file_name = self.settings.value('export', str(Path.cwd()), str)
        self.settings.endGroup()

        self.settings.beginGroup('window')
        # Fallback: Center the window
        desktop: QtGui.QScreen = QtWidgets.QApplication.screens()[0]
        window_frame: QtCore.QRect = self.frameGeometry()
        desktop_center: QtCore.QPoint = desktop.availableGeometry().center()
        window_frame.moveCenter(desktop_center)
        self.move(window_frame.topLeft())

        self.restoreGeometry(cast(QtCore.QByteArray, self.settings.value('geometry', QtCore.QByteArray())))
        self.restoreState(cast(QtCore.QByteArray, self.settings.value('state', QtCore.QByteArray())))
        self.settings.endGroup()

    def save_settings(self) -> None:
        self.settings.beginGroup('location')
        self.settings.setValue('open', self._opened_file_name)
        self.settings.setValue('export', self._exported_file_name)
        self.settings.endGroup()

        self.settings.beginGroup('window')
        self.settings.setValue('geometry', self.saveGeometry())
        self.settings.setValue('state', self.saveState())
        self.settings.endGroup()
        self.settings.sync()

    def stringify_selection_plain_text(self, whole_table: bool = False) -> str:
        """
        Convert selected cells to string for copying as plain text
        :return: the plain text representation of the selected table lines
        """
        text_matrix: list[list[str]]
        if whole_table:
            text_matrix = [[self.table_model.formatted_item(row, column)
                            for column in range(self.table_model.columnCount())
                            if self.settings.visible_columns[column]]
                           for row in range(self.table_model.rowCount(available_count=True))]
        else:
            si: QtCore.QModelIndex
            rows: list[int] = sorted(list(set(si.row() for si in self.table.selectedIndexes())))
            cols: list[int] = sorted(list(set(si.column() for si in self.table.selectedIndexes())))
            text_matrix = [['' for _ in range(len(cols))]
                           for _ in range(len(rows))]
            for si in self.table.selectedIndexes():
                text_matrix[rows.index(si.row())][cols.index(si.column())] = self.table_model.data(si) or ''
        row_texts: list[str]
        text: list[str] = [self.settings.csv_separator.join(row_texts) for row_texts in text_matrix]
        return self.settings.line_end.join(text)

    def stringify_selection_html(self, whole_table: bool = False) -> str:
        """
        Convert selected cells to string for copying as rich text
        :return: the rich text representation of the selected table lines
        """
        text_matrix: list[list[str]]
        if whole_table:
            text_matrix = [[('<td>' + self.table_model.formatted_item(row, column) + '</td>')
                            for column in range(self.table_model.columnCount())
                            if self.settings.visible_columns[column]]
                           for row in range(self.table_model.rowCount(available_count=True))]
        else:
            si: QtCore.QModelIndex
            rows: list[int] = sorted(list(set(si.row() for si in self.table.selectedIndexes())))
            cols: list[int] = sorted(list(set(si.column() for si in self.table.selectedIndexes())))
            text_matrix = [['' for _ in range(len(cols))]
                           for _ in range(len(rows))]
            for si in self.table.selectedIndexes():
                text_matrix[rows.index(si.row())][cols.index(si.column())] = \
                    '<td>' + (self.table_model.data(si) or '') + '</td>'
        row_texts: list[str]
        text: list[str] = [('<tr>' + self.settings.csv_separator.join(row_texts) + '</tr>')
                           for row_texts in text_matrix]
        text.insert(0, '<table>')
        text.append('</table>')
        return self.settings.line_end.join(text)

    def load_file(self, file_name: str) -> bool:
        if not file_name:
            return False
        try:
            titles, data = parse(file_name)
        except (IOError, RuntimeError) as ex:
            self.status_bar.showMessage(' '.join(repr(a) for a in ex.args))
            return False
        else:
            self._opened_file_name = file_name
            self.table_model.set_data(data, titles)
            self.menu_view.clear()
            self.settings.columns = self.table_model.header, [self.settings.is_visible(title)
                                                              for title in self.table_model.header]
            index: int
            title: str
            for index, title in enumerate(self.table_model.header):
                action: QtGui.QAction = self.menu_view.addAction(title)
                action.setCheckable(True)
                if (self.settings.is_visible(title)
                        and (self.settings.show_all_zero_columns
                             or not np.alltrue((self.table_model.all_data[index] == 0.0)
                                               | np.isnan(self.table_model.all_data[index])))):
                    action.setChecked(True)
                    self.table.showColumn(index)
                else:
                    action.setChecked(False)
                    self.table.hideColumn(index)
                action.triggered.connect(self.on_action_column_triggered)
            self.menu_view.setEnabled(True)
            self.menu_plot.setEnabled(True)
            self.action_export.setEnabled(True)
            self.action_reload.setEnabled(True)
            self.status_bar.showMessage(self.tr('Ready'))
            return True

    def save_csv(self, filename: str) -> bool:
        visible_column_indices: np.ndarray = np.array([index for index, title in enumerate(self.table_model.header)
                                                       if self.settings.is_visible(title)])
        visible_column_names: list[str] = list(filter(self.settings.is_visible, self.table_model.header))
        try:
            np.savetxt(filename, self.table_model.all_data[visible_column_indices].T, fmt='%s',
                       delimiter=self.settings.csv_separator, newline=self.settings.line_end,
                       header=self.settings.csv_separator.join(visible_column_names))
        except IOError as ex:
            self.status_bar.showMessage(' '.join(ex.args))
            return False
        else:
            self._exported_file_name = filename
            self.status_bar.showMessage(self.tr('Saved to {0}').format(filename))
            return True

    def save_xlsx(self, filename: str) -> bool:
        try:
            import xlsxwriter
            from xlsxwriter import Workbook
            from xlsxwriter.format import Format
            from xlsxwriter.worksheet import Worksheet
        except ImportError as ex:
            self.status_bar.showMessage(' '.join(repr(a) for a in ex.args))
            return False

        visible_column_indices: list[int] = [index for index, title in enumerate(self.table_model.header)
                                             if self.settings.is_visible(title)]
        visible_column_names: list[str] = list(filter(self.settings.is_visible, self.table_model.header))
        try:
            workbook: Workbook = Workbook(filename,
                                          {'default_date_format': 'dd.mm.yyyy hh:mm:ss',
                                           'nan_inf_to_errors': True})
            header_format: Format = workbook.add_format({'bold': True})
            worksheet: Worksheet = workbook.add_worksheet(str(Path(self._opened_file_name).with_suffix('').name))
            worksheet.freeze_panes(1, 0)  # freeze first row
            col: int = 0
            _col: int
            row: int
            for _col in range(self.table_model.columnCount()):
                if _col not in visible_column_indices:
                    continue
                worksheet.write_string(0, col, visible_column_names[col], header_format)
                if visible_column_names[col].endswith(('(s)', '(secs)')):
                    for row in range(self.table_model.rowCount(available_count=True)):
                        worksheet.write_datetime(row + 1, col, datetime.fromtimestamp(self.table_model.item(row, _col)))
                else:
                    for row in range(self.table_model.rowCount(available_count=True)):
                        worksheet.write_number(row + 1, col, self.table_model.item(row, _col))
                col += 1
            workbook.close()
        except IOError as ex:
            self.status_bar.showMessage(' '.join(ex.args))
            return False
        else:
            self._exported_file_name = filename
            self.status_bar.showMessage(self.tr('Saved to {0}').format(filename))
            return True

    def on_action_open_triggered(self) -> None:
        new_file_name: str
        new_file_name, _ = QtWidgets.QFileDialog.getOpenFileName(
            self, self.tr('Open'),
            self._opened_file_name,
            f'{self.tr("VeriCold data logfile")} (*.vcl);;{self.tr("All Files")} (*.*)')
        if self.load_file(new_file_name):
            self.setWindowTitle(f'{new_file_name} — {getattr(self, "initial_window_title")}')

    def on_action_export_triggered(self) -> None:
        supported_formats: dict[str, str] = {'.csv': f'{self.tr("Text with separators")} (*.csv)'}
        supported_formats_callbacks: dict[str, Callable[[str], bool]] = {'.csv': self.save_csv}
        try:
            import xlsxwriter
        except ImportError:
            pass
        else:
            supported_formats['.xlsx'] = f'{self.tr("Microsoft Excel")} (*.xlsx)'
            supported_formats_callbacks['.xlsx'] = self.save_xlsx
        initial_filter: str = ''
        if self._exported_file_name:
            exported_file_name_ext: str = Path(self._exported_file_name).suffix
            if exported_file_name_ext in supported_formats:
                initial_filter = supported_formats[exported_file_name_ext]
        new_file_name: str
        new_file_name_filter: str  # BUG: it's empty when a native dialog is used
        new_file_name, new_file_name_filter = QtWidgets.QFileDialog.getSaveFileName(
            self, self.tr('Export'),
            str(Path(self._exported_file_name or self._opened_file_name)
                .with_name(Path(self._opened_file_name).name)),
            ';;'.join(supported_formats.values()),
            initial_filter,  # BUG: it is not taken into account when a native dialog is used
        )
        if not new_file_name:
            return
        new_file_name_ext: str = Path(new_file_name).suffix
        if new_file_name_ext in supported_formats_callbacks:
            supported_formats_callbacks[new_file_name_ext](new_file_name)

    def on_action_column_triggered(self) -> None:
        a: QtGui.QAction
        i: int
        for i, a in enumerate(self.menu_view.actions()):
            if a.isChecked() and (self.settings.show_all_zero_columns
                                  or not np.alltrue((self.table_model.all_data[i] == 0.0)
                                                    | np.isnan(self.table_model.all_data[i]))):
                self.table.showColumn(i)
            else:
                self.table.hideColumn(i)
        self.settings.visible_columns = [a.isChecked() for a in self.menu_view.actions()]

    def on_action_reload_triggered(self) -> None:
        try:
            titles, data = parse(self._opened_file_name)
        except (IOError, RuntimeError):
            return
        else:
            self.table_model.set_data(data, titles)

    def on_action_preferences_triggered(self) -> None:
        preferences_dialog: Preferences = Preferences(self.settings, self)
        preferences_dialog.exec()

        title: str
        visibility: bool
        action: QtGui.QAction
        column: int
        for column, (visibility, action) in enumerate(zip(self.settings.visible_columns, self.menu_view.actions())):
            if action.isChecked() != visibility:
                action.blockSignals(True)
                action.setChecked(visibility)
                action.blockSignals(False)
            if visibility and (self.settings.show_all_zero_columns
                               or not np.alltrue((self.table_model.all_data[column] == 0.0)
                                                 | np.isnan(self.table_model.all_data[column]))):
                self.table.showColumn(column)
            else:
                self.table.hideColumn(column)

    def on_action_quit_triggered(self) -> None:
        self.close()

    def on_action_copy_triggered(self) -> None:
        copy_to_clipboard(self.stringify_selection_plain_text(),
                          self.stringify_selection_html(), QtCore.Qt.TextFormat.RichText)

    def on_action_copy_all_triggered(self) -> None:
        copy_to_clipboard(self.stringify_selection_plain_text(whole_table=True),
                          self.stringify_selection_html(whole_table=True), QtCore.Qt.TextFormat.RichText)

    def on_action_select_all_triggered(self) -> None:
        self.table.selectAll()

    def on_action_show_plot_triggered(self) -> None:
        plot: Plot = Plot(self.settings, self.table_model, self)
        plot.exec()

    def on_action_about_triggered(self) -> None:
        QtWidgets.QMessageBox.about(self,
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

    def on_action_about_qt_triggered(self) -> None:
        QtWidgets.QMessageBox.aboutQt(self)
