# -*- coding: utf-8 -*-
import os
from typing import Any, Dict, Final, List, Set, Tuple, Union

from PyQt5.QtCore import QSettings

__all__ = ['Settings']


class Settings(QSettings):
    """ convenient internal representation of the application settings """
    LINE_ENDS: Final[List[str]] = [r'Line Feed (\n)', r'Carriage Return (\r)', r'CR+LF (\r\n)', r'LF+CR (\n\r)']
    _LINE_ENDS: Final[List[str]] = ['\n', '\r', '\r\n', '\n\r']
    CSV_SEPARATORS: Final[List[str]] = [r'comma (,)', r'tab (\t)', r'semicolon (;)', r'space ( )']
    _CSV_SEPARATORS: Final[List[str]] = [',', '\t', ';', ' ']

    def __init__(self, *args: Any) -> None:
        super().__init__(*args)
        self.check_items_names: List[str] = []
        self.check_items_values: List[bool] = []

        self.beginGroup('columns')
        self._visible_column_names: Set[str] = set()
        i: int
        for i in range(self.beginReadArray('visible')):
            self.setArrayIndex(i)
            self._visible_column_names.add(self.value('name', '', str))
        self.endArray()
        self.endGroup()

    def sync(self) -> None:
        self.beginGroup('columns')
        self.beginWriteArray('visible')
        i: int
        n: str
        for i, n in enumerate(self._visible_column_names):
            self.setArrayIndex(i)
            self.setValue('name', n)
        self.endArray()
        self.endGroup()

        super().sync()

    @property
    def dialog(self) -> Dict[str,
                             Union[Dict[str, Tuple[List[str], List[bool], str, str]],
                                   Dict[str, Tuple[List[str], List[str], str]]]]:
        return {
            'View': {
                'Visible columns:': (self.check_items_names, self.check_items_values, 'All', 'visible_columns')
            },
            'Export': {
                'Line ending:': (self.LINE_ENDS, self._LINE_ENDS, 'line_end'),
                'CSV separator:': (self.CSV_SEPARATORS, self._CSV_SEPARATORS, 'csv_separator'),
            }
        }

    @property
    def line_end(self) -> str:
        self.beginGroup('export')
        v: int = self.value('lineEnd', self._LINE_ENDS.index(os.linesep), int)
        self.endGroup()
        return self._LINE_ENDS[v]

    @line_end.setter
    def line_end(self, new_value: str) -> None:
        self.beginGroup('export')
        self.setValue('lineEnd', self._LINE_ENDS.index(new_value))
        self.endGroup()

    @property
    def csv_separator(self) -> str:
        self.beginGroup('export')
        v: int = self.value('csvSeparator', self._CSV_SEPARATORS.index('\t'), int)
        self.endGroup()
        return self._CSV_SEPARATORS[v]

    @csv_separator.setter
    def csv_separator(self, new_value: str) -> None:
        self.beginGroup('export')
        self.setValue('csvSeparator', self._CSV_SEPARATORS.index(new_value))
        self.endGroup()

    @property
    def visible_columns(self) -> List[bool]:
        return self.check_items_values

    @visible_columns.setter
    def visible_columns(self, new_values: List[bool]) -> None:
        self.check_items_values = new_values[:]
        self._visible_column_names = set(s for s, v in zip(self.check_items_names, self.check_items_values) if v)

    @property
    def columns(self) -> Tuple[List[str], List[bool]]:
        return self.check_items_names, self.check_items_values

    @columns.setter
    def columns(self, new: Tuple[List[str], List[bool]]) -> None:
        self.check_items_names = new[0][:]
        self.check_items_values = new[1][:]
        self._visible_column_names = set(s for s, v in zip(self.check_items_names, self.check_items_values) if v)

    def is_visible(self, title: str) -> bool:
        return not self._visible_column_names or title in self._visible_column_names
