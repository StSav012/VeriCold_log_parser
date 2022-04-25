# -*- coding: utf-8 -*-
from datetime import datetime
from typing import Final, List, Optional, Union, cast

import numpy as np
from numpy.typing import NDArray
from pyqtgraph.Qt import QtCore


class DataModel(QtCore.QAbstractTableModel):
    ROW_BATCH_COUNT: Final[int] = 96

    def __init__(self, parent: Optional[QtCore.QObject] = None) -> None:
        super().__init__(parent)
        self._data: NDArray[np.float64] = np.empty((0, 0), dtype=np.float64)
        self._rows_loaded: int = self.ROW_BATCH_COUNT

        self._header: List[str] = []

    @property
    def header(self) -> List[str]:
        return self._header

    @property
    def all_data(self) -> NDArray[np.float64]:
        return self._data[1:]

    def rowCount(self, parent: Optional[QtCore.QObject] = None, *, available_count: bool = False) -> int:
        if available_count:
            return cast(int, self._data.shape[1])
        return min(cast(int, self._data.shape[1]), self._rows_loaded)

    def columnCount(self, parent: Optional[QtCore.QObject] = None) -> int:
        return len(self._header)

    def formatted_item(self, row: int, column: int) -> str:
        value: np.float64 = self.item(row, column)
        if np.isnan(value):
            return ''
        if self._header[column].endswith(('(s)', '(sec)', '(secs)')):
            return datetime.fromtimestamp(value).isoformat()
        if self._header[column].endswith('(K)'):
            return str(np.around(value, decimals=3))
        if self._header[column].endswith('(Bar)'):
            return cast(str, np.format_float_positional(value, precision=3 + int(-np.log10(np.abs(value)))))
        if value.is_integer():
            return f'{value:.0f}'
        return str(np.around(value, decimals=12))

    def data(self, index: QtCore.QModelIndex,
             role: QtCore.Qt.ItemDataRole = QtCore.Qt.ItemDataRole.DisplayRole) -> Optional[str]:
        if index.isValid():
            if role == QtCore.Qt.ItemDataRole.DisplayRole:
                return self.formatted_item(index.row(), index.column())
        return None

    def item(self, row_index: int, column_index: int) -> np.float64:
        return self._data[column_index + 1, row_index]

    def headerData(self, col: int, orientation: QtCore.Qt.Orientation,
                   role: QtCore.Qt.ItemDataRole = QtCore.Qt.ItemDataRole.DisplayRole) -> Optional[str]:
        if orientation == QtCore.Qt.Orientation.Horizontal and role == QtCore.Qt.ItemDataRole.DisplayRole:
            return self._header[col]
        if (orientation == QtCore.Qt.Orientation.Vertical
                and role == QtCore.Qt.ItemDataRole.DisplayRole
                and not np.isnan(self._data[0, col])):
            return f'{self._data[0, col]:.0f}'
        return None

    def setHeaderData(self, section: int, orientation: QtCore.Qt.Orientation,
                      value: str, role: int = QtCore.Qt.ItemDataRole()) -> bool:
        if (orientation == QtCore.Qt.Orientation.Horizontal
                and role == QtCore.Qt.ItemDataRole.DisplayRole
                and 0 <= section < len(self._header)):
            self._header[section] = value
            return True
        return False

    def set_data(self, new_data: Union[List[List[float]], NDArray[np.float]],
                 new_header: Optional[List[str]] = None) -> None:
        self.beginResetModel()
        self._data = np.array(new_data)
        good: NDArray[np.bool] = ~np.all(self._data == 0.0, axis=1)
        self._data = self._data[good]
        if new_header is not None:
            self._header = [str(s) for s, g in zip(new_header, good) if g][1:]
        self._rows_loaded = self.ROW_BATCH_COUNT
        self.endResetModel()

    def canFetchMore(self, index: QtCore.QModelIndex = QtCore.QModelIndex()) -> bool:
        return bool(self._data.shape[1] > self._rows_loaded)

    def fetchMore(self, index: QtCore.QModelIndex = QtCore.QModelIndex()) -> None:
        # FIXME: if the 0th column is hidden, no data gets fetched despite it is available according to `canFetchMore`
        #  For now, the only solution is to load more than one screen can display. If the table is scrolled, data loads.
        # https://sateeshkumarb.wordpress.com/2012/04/01/paginated-display-of-table-data-in-pyqt/
        reminder: int = self._data.shape[1] - self._rows_loaded
        items_to_fetch: int = min(reminder, self.ROW_BATCH_COUNT)
        self.beginInsertRows(QtCore.QModelIndex(), self._rows_loaded, self._rows_loaded + items_to_fetch - 1)
        self._rows_loaded += items_to_fetch
        self.endInsertRows()
