# -*- coding: utf-8 -*-

from PyQt5.QtWidgets import QCheckBox, QComboBox, \
    QDialog, QDialogButtonBox, QDoubleSpinBox, QFormLayout, QGroupBox, \
    QSpinBox, QVBoxLayout, QWidget

from gui._checklist import CheckList
from gui._settings import Settings

__all__ = ['Preferences']


class Preferences(QDialog):
    """ GUI preferences dialog """

    def __init__(self, settings: Settings, parent: QWidget = None, *args):
        super().__init__(parent, *args)

        self.settings: Settings = settings
        self.setModal(True)
        self.setWindowTitle(self.tr('Preferences'))
        if parent is not None:
            self.setWindowIcon(parent.windowIcon())

        layout: QVBoxLayout = QVBoxLayout(self)
        for key, value in self.settings.dialog.items():
            if isinstance(value, dict):
                box: QGroupBox = QGroupBox(key, self)
                box_layout: QFormLayout = QFormLayout(box)
                for key2, value2 in value.items():
                    if isinstance(value2, tuple) and isinstance(value2[-1], str) and value2[-1]:
                        if len(value2) == 1:
                            widget: QCheckBox = QCheckBox(self.tr(key2), box)
                            setattr(widget, 'callback', value2[-1])
                            widget.setChecked(getattr(self.settings, value2[-1]))
                            widget.toggled.connect(
                                lambda x: setattr(self.settings, getattr(self.sender(), 'callback'), x))
                            box_layout.addWidget(widget)
                        elif len(value2) == 2:
                            value3 = value2[0]
                            if isinstance(value3, (list, tuple)):
                                widget: QComboBox = QComboBox(box)
                                setattr(widget, 'callback', value2[-1])
                                for item in value3:
                                    widget.addItem(self.tr(item))
                                widget.setCurrentIndex(getattr(self.settings, value2[-1]))
                                widget.currentIndexChanged.connect(
                                    lambda x: setattr(self.settings, getattr(self.sender(), 'callback'), x))
                                box_layout.addRow(self.tr(key2), widget)
                            # no else
                        elif len(value2) == 3:
                            value3a = value2[0]
                            value3b = value2[1]
                            if isinstance(value3a, (list, tuple)) and isinstance(value3b, (list, tuple)):
                                widget: QComboBox = QComboBox(box)
                                setattr(widget, 'callback', value2[-1])
                                for index, item in enumerate(value3a):
                                    widget.addItem(self.tr(item), value3b[index])
                                widget.setCurrentIndex(value3b.index(getattr(self.settings, value2[-1])))
                                widget.currentIndexChanged.connect(
                                    lambda _: setattr(self.settings, getattr(self.sender(), 'callback'),
                                                      self.sender().currentData()))
                                box_layout.addRow(self.tr(key2), widget)
                            elif (isinstance(value3a, slice)
                                  and isinstance(getattr(self.settings, value2[-1]), (int, float))
                                  and isinstance(value3b, tuple)):
                                if ((value3a.start is None or isinstance(value3a.start, int))
                                        and (value3a.stop is None or isinstance(value3a.stop, int))
                                        and (value3a.step is None or isinstance(value3a.step, int))
                                        and isinstance(getattr(self.settings, value2[-1]), int)):
                                    widget: QSpinBox = QSpinBox(box)
                                else:
                                    widget: QDoubleSpinBox = QDoubleSpinBox(box)
                                setattr(widget, 'callback', value2[-1])
                                if value3a.start is not None:
                                    widget.setMinimum(value3a.start)
                                if value3a.stop is not None:
                                    widget.setMaximum(value3a.stop)
                                if value3a.step is not None:
                                    widget.setSingleStep(value3a.step)
                                widget.setValue(getattr(self.settings, value2[-1]))
                                if len(value3b) == 2:
                                    widget.setPrefix(str(value3b[0]))
                                    widget.setSuffix(str(value3b[1]))
                                elif len(value3b) == 1:
                                    widget.setSuffix(str(value3b[0]))
                                # no else
                                widget.valueChanged.connect(
                                    lambda _: setattr(self.settings, getattr(self.sender(), 'callback'),
                                                      self.sender().value()))
                                box_layout.addRow(self.tr(key2), widget)
                            # no else
                        elif len(value2) == 4:
                            value3a = value2[0]
                            value3b = value2[1]
                            value3c = value2[2]
                            if isinstance(value3a, (list, tuple)) and isinstance(value3b, (list, tuple)) \
                                    and isinstance(value3c, str):
                                widget: CheckList = CheckList(box, show_all=value3c)
                                setattr(widget, 'callback', value2[-1])
                                for index, item in enumerate(value3a):
                                    widget.addItem(self.tr(item), value3b[index])
                                widget.checkStateChanged.connect(
                                    lambda visibility: setattr(self.settings, getattr(self.sender(), 'callback'),
                                                               visibility))
                                box_layout.addRow(self.tr(key2), widget)
                            # no else
                        # no else
                    # no else
                layout.addWidget(box)
            # no else
        buttons: QDialogButtonBox = QDialogButtonBox(QDialogButtonBox.Close, self)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
