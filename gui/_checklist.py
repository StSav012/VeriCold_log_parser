# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Any

from pyqtgraph.Qt import QtCore, QtWidgets

__all__ = ['CheckList']


class CheckList(QtWidgets.QWidget):
    checkStateChanged: QtCore.Signal = QtCore.Signal(list, name='checkStateChanged')

    def __init__(self, *args: Any, show_all: str = '', **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)

        self._layout: QtWidgets.QVBoxLayout = QtWidgets.QVBoxLayout(self)
        self._all: QtWidgets.QCheckBox = QtWidgets.QCheckBox(self)
        self._list: QtWidgets.QListWidget = QtWidgets.QListWidget(self)

        if show_all:
            self._layout.addWidget(self._all, stretch=0)
            self._all.setText(show_all)
            self._all.stateChanged.connect(self.onCheckAllToggled)
        self._layout.addWidget(self._list, stretch=1)

        self._list.itemChanged.connect(self.onListItemChanged)

    def addItem(self, item: str | QtWidgets.QListWidgetItem,
                checked: bool | QtCore.Qt.CheckState = QtCore.Qt.CheckState.Unchecked) -> None:
        if not isinstance(item, QtWidgets.QListWidgetItem):
            item = QtWidgets.QListWidgetItem(self.tr(item), self._list)
        if not isinstance(checked, QtCore.Qt.CheckState):
            checked = QtCore.Qt.CheckState.Checked if checked else QtCore.Qt.CheckState.Unchecked
        item.setCheckState(checked)
        if not self._list.count():
            self._all.blockSignals(True)
            self._all.setCheckState(checked)
            self._all.blockSignals(False)

        self._list.addItem(item)

        self._all.blockSignals(True)
        if self._all.checkState() != checked:
            self._all.setCheckState(QtCore.Qt.CheckState.PartiallyChecked)
        self._all.blockSignals(False)

    def onCheckAllToggled(self, new_state: QtCore.Qt.CheckState | int) -> None:
        r: int
        self._all.setTristate(False)
        self._list.blockSignals(True)

        if isinstance(new_state, int):  # fix for PySide6.3
            new_state = {
                0: QtCore.Qt.CheckState.Unchecked,
                1: QtCore.Qt.CheckState.PartiallyChecked,
                2: QtCore.Qt.CheckState.Checked
            }[new_state]

        for r in range(self._list.count()):
            self._list.item(r).setCheckState(new_state)
        self._list.blockSignals(False)
        self.checkStateChanged.emit([self._list.item(r).checkState() == QtCore.Qt.CheckState.Checked
                                     for r in range(self._list.count())])

    def onListItemChanged(self, _: QtWidgets.QListWidgetItem) -> None:
        r: int
        self._all.blockSignals(True)
        if all([self._list.item(r).checkState() == QtCore.Qt.CheckState.Checked
                for r in range(self._list.count())]):
            self._all.setCheckState(QtCore.Qt.CheckState.Checked)
        elif all([self._list.item(r).checkState() == QtCore.Qt.CheckState.Unchecked
                  for r in range(self._list.count())]):
            self._all.setCheckState(QtCore.Qt.CheckState.Unchecked)
        else:
            self._all.setCheckState(QtCore.Qt.CheckState.PartiallyChecked)
        self._all.blockSignals(False)
        self.checkStateChanged.emit([self._list.item(r).checkState() == QtCore.Qt.CheckState.Checked
                                     for r in range(self._list.count())])
