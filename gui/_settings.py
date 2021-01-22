# -*- coding: utf-8 -*-
import os
from typing import List, Type

from PyQt5.QtCore import QSettings

try:
    from typing import Final
except ImportError:
    class _Final:
        @staticmethod
        def __getitem__(item: Type):
            return item


    Final = _Final()


__all__ = ['Settings']


class Settings(QSettings):
    """ convenient internal representation of the application settings """
    LINE_ENDS: Final[List[str]] = [r'Line Feed (\n)', r'Carriage Return (\r)', r'CR+LF (\r\n)', r'LF+CR (\n\r)']
    _LINE_ENDS: Final[List[str]] = ['\n', '\r', '\r\n', '\n\r']
    CSV_SEPARATORS: Final[List[str]] = [r'comma (,)', r'tab (\t)', r'semicolon (;)', r'space ( )']
    _CSV_SEPARATORS: Final[List[str]] = [',', '\t', ';', ' ']

    DIALOG = {
        'Export': {
            'Line ending:': (LINE_ENDS, _LINE_ENDS, 'line_end'),
            'CSV separator:': (CSV_SEPARATORS, _CSV_SEPARATORS, 'csv_separator'),
        }
    }

    def __init__(self, *args):
        super().__init__(*args)

    @property
    def line_end(self) -> str:
        self.beginGroup('export')
        v: int = self.value('lineEnd', self._LINE_ENDS.index(os.linesep), int)
        self.endGroup()
        return self._LINE_ENDS[v]

    @line_end.setter
    def line_end(self, new_value: str):
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
    def csv_separator(self, new_value: str):
        self.beginGroup('export')
        self.setValue('csvSeparator', self._CSV_SEPARATORS.index(new_value))
        self.endGroup()
