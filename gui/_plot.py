# -*- coding: utf-8 -*-
from datetime import datetime
from typing import Any, List, Optional, Tuple

import numpy as np
import pyqtgraph as pg
from PyQt5.QtCore import QPointF, QRectF
from PyQt5.QtGui import QCloseEvent, QColor
from PyQt5.QtWidgets import QDialog, QFormLayout, QHBoxLayout, QWidget

from gui._data_model import DataModel
from gui._settings import Settings

__all__ = ['Plot']


class Plot(QDialog):
    def __init__(self, settings: Settings, data_model: DataModel, parent: Optional[QWidget] = None, *args: Any) -> None:
        super().__init__(parent, *args)

        self.setObjectName('plot_dialog')

        self.settings: Settings = settings
        self.setModal(True)
        self.setWindowTitle(self.tr('Plot'))
        if parent is not None:
            self.setWindowIcon(parent.windowIcon())

        layout: QHBoxLayout = QHBoxLayout(self)

        controls_panel: QWidget = QWidget(self)
        layout.addWidget(controls_panel)
        controls_layout: QFormLayout = QFormLayout(controls_panel)

        plot: pg.PlotWidget = pg.PlotWidget(self)
        canvas: pg.PlotItem = plot.getPlotItem()
        canvas.setAxisItems({'bottom': pg.DateAxisItem()})
        layout.addWidget(plot)
        layout.setStretch(0, 0)
        cursor_balloon: pg.TextItem = pg.TextItem()
        plot.addItem(cursor_balloon, True)  # ignore bounds

        def on_mouse_moved(event: Tuple[QPointF]) -> None:
            pos: QPointF = event[0]
            if plot.sceneBoundingRect().contains(pos):
                point: QPointF = canvas.vb.mapSceneToView(pos)
                if plot.visibleRange().contains(point):
                    cursor_balloon.setPos(point)
                    cursor_balloon.setText(f'{datetime.fromtimestamp(round(point.x()))}\n{point.y()}')
                    balloon_border: QRectF = cursor_balloon.boundingRect()
                    sx: float
                    sy: float
                    sx, sy = canvas.vb.viewPixelSize()
                    balloon_width: float = balloon_border.width() * sx
                    balloon_height: float = balloon_border.height() * sy
                    anchor_x: float = 0.0 if point.x() - plot.visibleRange().left() < balloon_width else 1.0
                    anchor_y: float = 0.0 if plot.visibleRange().bottom() - point.y() < balloon_height else 1.0
                    cursor_balloon.setAnchor((anchor_x, anchor_y))
                    cursor_balloon.setVisible(True)
                else:
                    cursor_balloon.setVisible(False)
            else:
                cursor_balloon.setVisible(False)

        self._mouse_moved_signal_proxy: pg.SignalProxy = pg.SignalProxy(plot.scene().sigMouseMoved,
                                                                        rateLimit=10, slot=on_mouse_moved)

        header: str
        column: np.ndarray
        visibility: bool
        self.lines: List[pg.PlotDataItem] = []
        self.color_buttons: List[pg.ColorButton] = []
        visible_columns_count: int = 0
        visible_headers: List[str] = []
        for header, column, visibility in zip(data_model.header, data_model.all_data, self.settings.check_items_values):
            if not (visibility and (self.settings.show_all_zero_columns
                                    or not np.alltrue((column == 0.0) | np.isnan(column)))) \
                    or header.endswith(('(s)', '(sec)', '(secs)')):
                continue
            else:
                visible_columns_count += 1
                visible_headers.append(header)

        def set_line_color(sender: pg.ColorButton) -> None:
            index: int = self.color_buttons.index(sender)
            self.lines[index].setPen(sender.color())
            self.settings.line_colors[visible_headers[index]] = sender.color()

        for header, column, visibility in zip(data_model.header, data_model.all_data, self.settings.check_items_values):
            if not (visibility and (self.settings.show_all_zero_columns
                                    or not np.alltrue((column == 0.0) | np.isnan(column)))) \
                    or header.endswith(('(s)', '(sec)', '(secs)')):
                continue
            color: QColor = self.settings.line_colors.get(header,
                                                          pg.intColor(len(self.lines),
                                                                      hues=visible_columns_count))
            self.color_buttons.append(pg.ColorButton(controls_panel, color))
            controls_layout.addRow(header, self.color_buttons[-1])
            self.lines.append(canvas.plot(np.column_stack((data_model.all_data[0], column)), name=header, pen=color))
            self.color_buttons[-1].sigColorChanged.connect(set_line_color)

        self.settings.beginGroup('plot')
        window_settings: bytes = self.settings.value('geometry')
        if window_settings is not None:
            self.restoreGeometry(window_settings)
        self.settings.endGroup()

    def closeEvent(self, event: QCloseEvent) -> None:
        self.settings.beginGroup('plot')
        self.settings.setValue('geometry', self.saveGeometry())
        self.settings.endGroup()
        event.accept()
