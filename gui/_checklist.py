# -*- coding: utf-8 -*-
from typing import Any, Union

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import QCheckBox, QListWidget, QListWidgetItem, QVBoxLayout, QWidget

__all__ = ['CheckList']


class CheckList(QWidget):
    checkStateChanged: pyqtSignal = pyqtSignal(list, name='checkStateChanged')

    def __init__(self, *args: Any, show_all: str = '', **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)

        self._layout: QVBoxLayout = QVBoxLayout(self)
        self._all: QCheckBox = QCheckBox(self)
        self._list: QListWidget = QListWidget(self)

        if show_all:
            self._layout.addWidget(self._all, stretch=0)
            self._all.setText(show_all)
            self._all.stateChanged.connect(self.onCheckAllToggled)
        self._layout.addWidget(self._list, stretch=1)

        self._list.itemChanged.connect(self.onListItemChanged)

    def addItem(self, item: Union[str, QListWidgetItem], checked: Union[bool, Qt.CheckState] = Qt.Unchecked) -> None:
        if not isinstance(item, QListWidgetItem):
            item = QListWidgetItem(self.tr(item), self._list)
        if not isinstance(checked, Qt.CheckState):
            checked = Qt.Checked if checked else Qt.Unchecked
        item.setCheckState(checked)
        if not self._list.count():
            self._all.blockSignals(True)
            self._all.setCheckState(checked)
            self._all.blockSignals(False)

        self._list.addItem(item)

        self._all.blockSignals(True)
        if self._all.checkState() != checked:
            self._all.setCheckState(Qt.PartiallyChecked)
        self._all.blockSignals(False)

    def onCheckAllToggled(self, new_state: Qt.CheckState) -> None:
        r: int
        self._all.setTristate(False)
        self._list.blockSignals(True)
        for r in range(self._list.count()):
            self._list.item(r).setCheckState(new_state)
        self._list.blockSignals(False)
        self.checkStateChanged.emit([self._list.item(r).checkState() == Qt.Checked for r in range(self._list.count())])

    def onListItemChanged(self, _: QListWidgetItem) -> None:
        r: int
        self._all.blockSignals(True)
        if all([self._list.item(r).checkState() == Qt.Checked for r in range(self._list.count())]):
            self._all.setCheckState(Qt.Checked)
        elif all([self._list.item(r).checkState() == Qt.Unchecked for r in range(self._list.count())]):
            self._all.setCheckState(Qt.Unchecked)
        else:
            self._all.setCheckState(Qt.PartiallyChecked)
        self._all.blockSignals(False)
        self.checkStateChanged.emit([self._list.item(r).checkState() == Qt.Checked for r in range(self._list.count())])
