# -*- coding: utf-8 -*-
from typing import Any, Dict, List, Optional, Sequence, Tuple, Union

from PyQt5.QtWidgets import QCheckBox, QComboBox, QDialog, QDialogButtonBox, QDoubleSpinBox, QFormLayout, QGroupBox, \
    QSpinBox, QVBoxLayout, QWidget

from gui._checklist import CheckList
from gui._settings import Settings

__all__ = ['Preferences']


class Preferences(QDialog):
    """ GUI preferences dialog """

    def __init__(self, settings: Settings, parent: Optional[QWidget] = None, *args: Any) -> None:
        super().__init__(parent, *args)

        self.settings: Settings = settings
        self.setModal(True)
        self.setWindowTitle(self.tr('Preferences'))
        if parent is not None:
            self.setWindowIcon(parent.windowIcon())

        layout: QVBoxLayout = QVBoxLayout(self)
        combo_box: QComboBox
        check_box: QCheckBox
        spin_box: Union[QSpinBox, QDoubleSpinBox]
        check_list: CheckList
        key: str
        value: Union[Dict[str, Tuple[List[str], List[bool], str, str]],
                     Dict[str, Tuple[List[str], List[str], str]]]
        for key, value in self.settings.dialog.items():
            if isinstance(value, dict):
                box: QGroupBox = QGroupBox(key, self)
                box_layout: QFormLayout = QFormLayout(box)
                key2: str
                value2: Union[Tuple[List[str], List[bool], str, str], Tuple[List[str], List[str], str]]
                value3: Sequence[str]
                value3a: Union[Sequence[str], slice]
                value3b: Union[Sequence[Any], Tuple[str]]
                value3c: str
                index: int
                item: str
                for key2, value2 in value.items():
                    if isinstance(value2, tuple) and isinstance(value2[-1], str) and value2[-1]:
                        if len(value2) == 1:
                            check_box = QCheckBox(self.tr(key2), box)
                            setattr(check_box, 'callback', value2[-1])
                            check_box.setChecked(getattr(self.settings, value2[-1]))
                            check_box.toggled.connect(
                                lambda x: setattr(self.settings, getattr(self.sender(), 'callback'), x))
                            box_layout.addWidget(check_box)
                        elif len(value2) == 2:
                            value3 = value2[0]
                            if isinstance(value3, Sequence):
                                combo_box = QComboBox(box)
                                setattr(combo_box, 'callback', value2[-1])
                                for item in value3:
                                    combo_box.addItem(self.tr(item))
                                combo_box.setCurrentIndex(getattr(self.settings, value2[-1]))
                                combo_box.currentIndexChanged.connect(
                                    lambda x: setattr(self.settings, getattr(self.sender(), 'callback'), x))
                                box_layout.addRow(self.tr(key2), combo_box)
                            # no else
                        elif len(value2) == 3:
                            value3a = value2[0]
                            value3b = value2[1]
                            if isinstance(value3a, Sequence) and isinstance(value3b, Sequence):
                                combo_box = QComboBox(box)
                                setattr(combo_box, 'callback', value2[-1])
                                for index, item in enumerate(value3a):
                                    combo_box.addItem(self.tr(item), value3b[index])
                                combo_box.setCurrentIndex(value3b.index(getattr(self.settings, value2[-1])))
                                combo_box.currentIndexChanged.connect(
                                    lambda _: setattr(self.settings, getattr(self.sender(), 'callback'),
                                                      self.sender().currentData()))
                                box_layout.addRow(self.tr(key2), combo_box)
                            elif (isinstance(value3a, slice)
                                  and isinstance(getattr(self.settings, value2[-1]), (int, float))
                                  and isinstance(value3b, tuple)):
                                if ((value3a.start is None or isinstance(value3a.start, int))
                                        and (value3a.stop is None or isinstance(value3a.stop, int))
                                        and (value3a.step is None or isinstance(value3a.step, int))
                                        and isinstance(getattr(self.settings, value2[-1]), int)):
                                    spin_box = QSpinBox(box)
                                else:
                                    spin_box = QDoubleSpinBox(box)
                                setattr(spin_box, 'callback', value2[-1])
                                if value3a.start is not None:
                                    spin_box.setMinimum(value3a.start)
                                if value3a.stop is not None:
                                    spin_box.setMaximum(value3a.stop)
                                if value3a.step is not None:
                                    spin_box.setSingleStep(value3a.step)
                                spin_box.setValue(getattr(self.settings, value2[-1]))
                                if len(value3b) == 2:
                                    spin_box.setPrefix(str(value3b[0]))
                                    spin_box.setSuffix(str(value3b[1]))
                                elif len(value3b) == 1:
                                    spin_box.setSuffix(str(value3b[0]))
                                # no else
                                spin_box.valueChanged.connect(
                                    lambda _: setattr(self.settings, getattr(self.sender(), 'callback'),
                                                      self.sender().value()))
                                box_layout.addRow(self.tr(key2), spin_box)
                            # no else
                        elif len(value2) == 4:
                            value3a = value2[0]
                            value3b = value2[1]
                            value3c = value2[2]
                            if isinstance(value3a, Sequence) and isinstance(value3b, Sequence) \
                                    and isinstance(value3c, str):
                                check_list = CheckList(box, show_all=value3c)
                                setattr(check_list, 'callback', value2[-1])
                                for index, item in enumerate(value3a):
                                    check_list.addItem(self.tr(item), value3b[index])
                                check_list.checkStateChanged.connect(
                                    lambda visibility: setattr(self.settings, getattr(self.sender(), 'callback'),
                                                               visibility))
                                box_layout.addRow(self.tr(key2), check_list)
                            # no else
                        # no else
                    # no else
                layout.addWidget(box)
            # no else
        buttons: QDialogButtonBox = QDialogButtonBox(QDialogButtonBox.Close, self)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
