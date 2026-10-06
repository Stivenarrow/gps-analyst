from __future__ import annotations

import ctypes
import sys
from datetime import date
from pathlib import Path

from PySide6.QtCore import QPoint, Qt, QUrl
from PySide6.QtGui import QDesktopServices, QFont, QIcon
from PySide6.QtWidgets import (
    QApplication,
    QMenu,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSizePolicy,
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from gps_analyst.models.presentation import GpsDayView
from gps_analyst.services.workbook_session import GpsWorkbookSession


def resource_path(relative_path: str) -> Path:
    frozen_base = getattr(sys, "_MEIPASS", None)
    if frozen_base:
        return Path(frozen_base) / relative_path
    return Path(__file__).resolve().parent.parent / relative_path


APP_ICON_PATH = resource_path("assets/gps-analyst.ico")


APP_STYLE = """
QWidget {
    color: #172033;
    font-family: "Segoe UI";
    font-size: 13px;
}

QMainWindow,
QMainWindow > QWidget {
    background: #f5f7fb;
}

QLabel {
    background: transparent;
}

QMainWindow {
    background: #f5f7fb;
}

QFrame#sidebar {
    background: #ffffff;
    border-right: 1px solid #e2e7ef;
}

QFrame#headerCard,
QFrame#summaryCard,
QFrame#timelineCard {
    background: #ffffff;
    border: 1px solid #e3e8f0;
    border-radius: 10px;
}

QFrame.metricCard {
    background: #f8fafc;
    border: 1px solid #e6ebf2;
    border-radius: 8px;
}

QLabel#appTitle {
    font-size: 22px;
    font-weight: 700;
    color: #111827;
}

QLabel#sectionTitle {
    font-size: 16px;
    font-weight: 700;
    color: #111827;
}

QLabel#muted {
    color: #6b7280;
}

QLabel#metricLabel {
    color: #6b7280;
    font-size: 11px;
}

QLabel#metricValue {
    color: #111827;
    font-size: 18px;
    font-weight: 700;
}

QPushButton {
    background: #2563eb;
    color: white;
    border: none;
    border-radius: 7px;
    padding: 8px 14px;
    font-weight: 600;
}

QPushButton:hover {
    background: #1d4ed8;
}

QPushButton:pressed {
    background: #1e40af;
}

QPushButton#secondaryButton {
    background: #eef2ff;
    color: #1e3a8a;
}

QPushButton#secondaryButton:hover {
    background: #e0e7ff;
}

QLineEdit {
    background: #ffffff;
    border: 1px solid #d7dde7;
    border-radius: 8px;
    padding: 8px 10px;
    min-height: 22px;
    color: #172033;
    selection-background-color: #dbeafe;
}

QLineEdit:focus {
    border: 1px solid #2563eb;
}

QFrame#dateSelector {
    background: #ffffff;
    border: 1px solid #d7dde7;
    border-radius: 8px;
    min-height: 38px;
}

QFrame#dateSelector:hover {
    border: 1px solid #9eabc0;
}

QFrame#dateSelector:focus {
    border: 1px solid #2563eb;
}

QFrame#dateSelector QLabel {
    background: transparent;
    border: none;
}

QLabel#dateSelectorText {
    color: #172033;
    font-weight: 500;
}

QLabel#dateSelectorArrow {
    color: #64748b;
    font-size: 11px;
    font-weight: 700;
}

QMenu {
    background: #ffffff;
    color: #172033;
    border: 1px solid #d7dde7;
    padding: 5px;
}

QMenu::item {
    background: transparent;
    border-radius: 6px;
    padding: 8px 18px 8px 10px;
    min-width: 150px;
}

QMenu::item:selected {
    background: #e8efff;
    color: #1d4ed8;
}

QMenu::separator {
    height: 1px;
    background: #e5e9f0;
    margin: 4px 6px;
}

QListWidget {
    background: white;
    border: 1px solid #e3e8f0;
    border-radius: 8px;
    padding: 4px;
    outline: none;
}

QListWidget::item {
    padding: 8px;
    border-radius: 6px;
}

QListWidget::item:selected {
    background: #e8efff;
    color: #1d4ed8;
}

QTableWidget {
    background: white;
    border: none;
    gridline-color: #edf0f5;
    selection-background-color: #e8efff;
    selection-color: #172033;
}

QHeaderView::section {
    background: #f8fafc;
    color: #64748b;
    border: none;
    border-bottom: 1px solid #e5e9f0;
    padding: 9px;
    font-weight: 600;
}

QTableWidget::item {
    padding: 6px;
    border-bottom: 1px solid #f0f2f6;
}
"""


def apply_windows_titlebar(window: QMainWindow) -> None:
    if sys.platform != "win32":
        return

    try:
        hwnd = int(window.winId())

        dwm = ctypes.windll.dwmapi

        use_dark_mode = ctypes.c_int(0)

        for attribute in (20, 19):
            result = dwm.DwmSetWindowAttribute(
                hwnd,
                attribute,
                ctypes.byref(use_dark_mode),
                ctypes.sizeof(use_dark_mode),
            )

            if result == 0:
                break

        def colorref(red: int, green: int, blue: int) -> int:
            return red | (green << 8) | (blue << 16)

        caption_color = ctypes.c_uint(
            colorref(245, 247, 251)
        )
        text_color = ctypes.c_uint(
            colorref(23, 32, 51)
        )
        border_color = ctypes.c_uint(
            colorref(226, 231, 239)
        )

        dwm.DwmSetWindowAttribute(
            hwnd,
            35,
            ctypes.byref(caption_color),
            ctypes.sizeof(caption_color),
        )

        dwm.DwmSetWindowAttribute(
            hwnd,
            36,
            ctypes.byref(text_color),
            ctypes.sizeof(text_color),
        )

        dwm.DwmSetWindowAttribute(
            hwnd,
            34,
            ctypes.byref(border_color),
            ctypes.sizeof(border_color),
        )

    except Exception:
        # El aspecto de la barra no debe impedir abrir la aplicación.
        pass


class DateSelector(QFrame):
    def __init__(self, text: str) -> None:
        super().__init__()

        self._menu: QMenu | None = None

        self.setObjectName("dateSelector")
        self.setCursor(Qt.PointingHandCursor)
        self.setFocusPolicy(Qt.StrongFocus)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(11, 0, 11, 0)
        layout.setSpacing(8)

        self.text_label = QLabel(text)
        self.text_label.setObjectName(
            "dateSelectorText"
        )

        self.arrow_label = QLabel("▾")
        self.arrow_label.setObjectName(
            "dateSelectorArrow"
        )
        self.arrow_label.setAlignment(
            Qt.AlignCenter
        )

        self.text_label.setAttribute(
            Qt.WA_TransparentForMouseEvents
        )
        self.arrow_label.setAttribute(
            Qt.WA_TransparentForMouseEvents
        )

        layout.addWidget(self.text_label, 1)
        layout.addWidget(self.arrow_label)

    def setText(self, text: str) -> None:
        self.text_label.setText(
            text.replace("    ▾", "")
        )

    def setMenu(self, menu: QMenu) -> None:
        self._menu = menu

    def mousePressEvent(self, event) -> None:
        if (
            event.button() == Qt.LeftButton
            and self._menu is not None
        ):
            self.setFocus()

            self._menu.setMinimumWidth(
                self.width()
            )

            self._menu.exec(
                self.mapToGlobal(
                    QPoint(0, self.height() + 2)
                )
            )

            event.accept()
            return

        super().mousePressEvent(event)


class MetricCard(QFrame):
    def __init__(self, label: str) -> None:
        super().__init__()

        self.setProperty("class", "metricCard")
        self.setObjectName("metricCard")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(4)

        self.label = QLabel(label)
        self.label.setObjectName("metricLabel")

        self.value = QLabel("—")
        self.value.setObjectName("metricValue")

        layout.addWidget(self.label)
        layout.addWidget(self.value)


def _preferred_date_text(
    preferred: str | None,
    date_map: dict[str, object],
) -> str | None:
    if preferred is not None and preferred in date_map:
        return preferred

    return next(iter(date_map), None)


def _qualities_by_vehicle_for_date(
    views,
    block_date,
) -> dict[str, set[str]]:
    result: dict[str, set[str]] = {}

    if block_date is None:
        return result

    for view in views:
        if (
            view.block_date == block_date
            and view.quality != "normal"
        ):
            result.setdefault(
                view.vehicle,
                set(),
            ).add(view.quality)

    return result


class GpsAnalystWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()

        self.session = GpsWorkbookSession()
        self.current_vehicle: str | None = None
        self.current_date_text: str | None = None
        self.date_map: dict[str, date] = {}
        self.map_targets: dict[int, str] = {}

        self.setWindowTitle("GPS Analyst")
        if APP_ICON_PATH.exists():
            self.setWindowIcon(QIcon(str(APP_ICON_PATH)))
        self.resize(1440, 880)
        self.setMinimumSize(1120, 700)

        self._build_ui()
        self._set_empty_state()

    def _build_ui(self) -> None:
        central = QWidget()
        self.setCentralWidget(central)

        root = QHBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        splitter = QSplitter(Qt.Horizontal)
        splitter.setChildrenCollapsible(False)

        splitter.addWidget(self._build_sidebar())
        splitter.addWidget(self._build_main_panel())

        splitter.setSizes([300, 1140])

        root.addWidget(splitter)

    def _build_sidebar(self) -> QWidget:
        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setMinimumWidth(260)
        sidebar.setMaximumWidth(380)

        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(20, 22, 20, 20)
        layout.setSpacing(14)

        title = QLabel("GPS Analyst")
        title.setObjectName("appTitle")

        subtitle = QLabel("Análisis de jornadas GPS")
        subtitle.setObjectName("muted")

        self.open_button = QPushButton("Abrir Excel")
        self.open_button.clicked.connect(self._open_file)

        self.file_label = QLabel("Ningún archivo cargado")
        self.file_label.setObjectName("muted")
        self.file_label.setWordWrap(True)

        vehicle_title = QLabel("Vehículos")
        vehicle_title.setObjectName("sectionTitle")

        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("Buscar vehículo...")
        self.search_box.textChanged.connect(
            self._filter_vehicles
        )

        self.vehicle_list = QListWidget()
        self.vehicle_list.currentItemChanged.connect(
            self._vehicle_changed
        )

        date_title = QLabel("Fecha")
        date_title.setObjectName("sectionTitle")

        self.date_button = DateSelector(
            "Selecciona una fecha"
        )

        self.date_menu = QMenu(
            self.date_button
        )
        self.date_button.setMenu(
            self.date_menu
        )

        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addSpacing(4)
        layout.addWidget(self.open_button)
        layout.addWidget(self.file_label)
        layout.addSpacing(8)
        layout.addWidget(vehicle_title)
        layout.addWidget(self.search_box)
        layout.addWidget(self.vehicle_list, 1)
        layout.addWidget(date_title)
        layout.addWidget(self.date_button)

        return sidebar

    def _build_main_panel(self) -> QWidget:
        panel = QWidget()

        layout = QVBoxLayout(panel)
        layout.setContentsMargins(24, 22, 24, 20)
        layout.setSpacing(16)

        layout.addWidget(self._build_header())
        layout.addWidget(self._build_quality_panel())
        layout.addWidget(self._build_metrics())
        layout.addWidget(self._build_timeline(), 1)

        return panel

    def _build_header(self) -> QWidget:
        frame = QFrame()
        frame.setObjectName("headerCard")

        layout = QHBoxLayout(frame)
        layout.setContentsMargins(18, 15, 18, 15)

        left = QVBoxLayout()
        left.setSpacing(3)

        self.day_title = QLabel("Sin jornada seleccionada")
        self.day_title.setObjectName("sectionTitle")

        self.day_subtitle = QLabel(
            "Abre un Excel para comenzar"
        )
        self.day_subtitle.setObjectName("muted")

        left.addWidget(self.day_title)
        left.addWidget(self.day_subtitle)

        layout.addLayout(left)
        layout.addStretch()

        self.status_badge = QLabel("Sin datos")
        self.status_badge.setStyleSheet(
            "background:#f1f5f9;"
            "color:#64748b;"
            "padding:6px 10px;"
            "border-radius:8px;"
            "font-weight:600;"
        )

        layout.addWidget(self.status_badge)

        return frame

    def _build_quality_panel(self) -> QWidget:
        self.quality_frame = QFrame()
        self.quality_frame.setObjectName("qualityCard")

        layout = QVBoxLayout(self.quality_frame)
        layout.setContentsMargins(18, 14, 18, 14)
        layout.setSpacing(7)

        self.quality_title = QLabel("")
        self.quality_title.setWordWrap(True)

        self.quality_text = QLabel("")
        self.quality_text.setWordWrap(True)

        layout.addWidget(self.quality_title)
        layout.addWidget(self.quality_text)

        self.quality_frame.hide()

        return self.quality_frame

    def _build_metrics(self) -> QWidget:
        frame = QFrame()
        frame.setObjectName("summaryCard")

        layout = QHBoxLayout(frame)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(10)

        self.metrics = {
            "Inicio": MetricCard("Inicio"),
            "Fin": MetricCard("Fin"),
            "Jornada": MetricCard("Jornada"),
            "Conducción": MetricCard("Conducción"),
            "Tiempo parado": MetricCard("Tiempo parado"),
            "Kilómetros": MetricCard("Kilómetros"),
            "Velocidad punta": MetricCard(
                "Velocidad punta"
            ),
        }

        for card in self.metrics.values():
            layout.addWidget(card)

        return frame

    def _build_timeline(self) -> QWidget:
        frame = QFrame()
        frame.setObjectName("timelineCard")

        layout = QVBoxLayout(frame)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(10)

        top = QHBoxLayout()

        title = QLabel("Cronología")
        title.setObjectName("sectionTitle")

        self.event_count = QLabel("0 eventos")
        self.event_count.setObjectName("muted")

        self.map_button = QPushButton(
            "Abrir ubicación"
        )
        self.map_button.setObjectName(
            "secondaryButton"
        )
        self.map_button.clicked.connect(
            self._open_selected_map
        )

        top.addWidget(title)
        top.addWidget(self.event_count)
        top.addStretch()
        top.addWidget(self.map_button)

        self.table = QTableWidget()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels(
            [
                "Tipo",
                "Inicio",
                "Fin",
                "Duración",
                "Km",
                "Velocidad",
                "Origen",
                "Destino / ubicación de parada",
            ]
        )

        self.table.setSelectionBehavior(
            QTableWidget.SelectRows
        )
        self.table.setSelectionMode(
            QTableWidget.SingleSelection
        )
        self.table.setEditTriggers(
            QTableWidget.NoEditTriggers
        )
        self.table.setAlternatingRowColors(False)
        self.table.verticalHeader().setVisible(False)

        header = self.table.horizontalHeader()
        header.setSectionResizeMode(
            0,
            QHeaderView.ResizeToContents,
        )
        header.setSectionResizeMode(
            1,
            QHeaderView.ResizeToContents,
        )
        header.setSectionResizeMode(
            2,
            QHeaderView.ResizeToContents,
        )
        header.setSectionResizeMode(
            3,
            QHeaderView.ResizeToContents,
        )
        header.setSectionResizeMode(
            4,
            QHeaderView.ResizeToContents,
        )
        header.setSectionResizeMode(
            5,
            QHeaderView.ResizeToContents,
        )
        header.setSectionResizeMode(
            6,
            QHeaderView.Stretch,
        )
        header.setSectionResizeMode(
            7,
            QHeaderView.Stretch,
        )

        self.table.doubleClicked.connect(
            self._open_selected_map
        )

        layout.addLayout(top)
        layout.addWidget(self.table)

        return frame

    def _open_file(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Abrir exportación Automatica PLUS",
            "",
            "Excel (*.xlsx);;Todos los archivos (*)",
        )

        if not path:
            return

        try:
            self.session.load(path)
        except Exception as exc:
            QMessageBox.critical(
                self,
                "No se ha podido abrir el Excel",
                str(exc),
            )
            return

        self.file_label.setText(
            Path(path).name
        )

        # A newly loaded workbook starts with its own date context.
        self.current_date_text = None
        self._populate_vehicles()

        if self.session.warnings:
            count = len(self.session.warnings)

            if count == 1:
                review_text = (
                    "Se ha detectado 1 jornada que requiere revisión.\n\n"
                    "La jornada permanece disponible para su análisis."
                )
            else:
                review_text = (
                    f"Se han detectado {count} jornadas que requieren revisión.\n\n"
                    "Todas permanecen disponibles para su análisis."
                )

            QMessageBox.information(
                self,
                "Excel cargado con avisos",
                "Archivo cargado correctamente.\n\n"
                f"{review_text}\n\n"
                "Selecciona la jornada para consultar el motivo "
                "y los datos disponibles.",
            )

    def _populate_vehicles(self) -> None:
        self.vehicle_list.clear()
        self.search_box.clear()

        for vehicle in self.session.vehicles:
            item = QListWidgetItem(vehicle)
            item.setData(Qt.UserRole, vehicle)
            self.vehicle_list.addItem(item)

        if self.vehicle_list.count():
            self.vehicle_list.setCurrentRow(0)

    def _filter_vehicles(self, text: str) -> None:
        query = text.casefold().strip()

        for row in range(
            self.vehicle_list.count()
        ):
            item = self.vehicle_list.item(row)

            item.setHidden(
                query not in item.text().casefold()
            )

    def _vehicle_changed(
        self,
        current: QListWidgetItem | None,
        _previous: QListWidgetItem | None,
    ) -> None:
        if current is None:
            return

        preferred_date_text = self.current_date_text

        self.current_vehicle = (
            current.data(Qt.UserRole)
            or current.text()
        )

        dates = self.session.dates_for_vehicle(
            self.current_vehicle
        )

        self.date_map = {
            value.strftime("%d/%m/%Y"): value
            for value in dates
        }

        self.date_menu.clear()

        for date_text in self.date_map:
            action = self.date_menu.addAction(
                date_text
            )

            action.triggered.connect(
                lambda checked=False, value=date_text:
                self._select_date(value)
            )

        selected_date_text = _preferred_date_text(
            preferred_date_text,
            self.date_map,
        )

        if selected_date_text is not None:
            self._select_date(selected_date_text)
        else:
            self.current_date_text = None
            self.date_button.setText(
                "Sin fechas disponibles    ▾"
            )
            self._refresh_vehicle_quality_markers()

    def _select_date(
        self,
        date_text: str,
    ) -> None:
        if date_text not in self.date_map:
            return

        self.current_date_text = date_text

        self.date_button.setText(
            f"{date_text}    ▾"
        )

        self._refresh_vehicle_quality_markers()
        self._show_current_day()

    def _refresh_vehicle_quality_markers(self) -> None:
        selected_date = self.date_map.get(
            self.current_date_text or ""
        )

        quality_by_vehicle = _qualities_by_vehicle_for_date(
            self.session.views,
            selected_date,
        )

        for row in range(self.vehicle_list.count()):
            item = self.vehicle_list.item(row)
            vehicle = (
                item.data(Qt.UserRole)
                or item.text().removeprefix("⚠ ")
            )
            qualities = quality_by_vehicle.get(
                vehicle,
                set(),
            )

            item.setText(
                f"{'⚠ ' if qualities else ''}{vehicle}"
            )

            if "incoherent" in qualities:
                item.setToolTip(
                    "Requiere revisión en la fecha seleccionada: "
                    "datos GPS incoherentes."
                )
            elif "partial" in qualities:
                item.setToolTip(
                    "Requiere revisión en la fecha seleccionada: "
                    "jornada parcial."
                )
            else:
                item.setToolTip("")

        self._filter_vehicles(
            self.search_box.text()
        )

    def _show_current_day(self) -> None:
        if self.current_vehicle is None:
            return

        block_date = self.date_map.get(
            self.current_date_text or ""
        )

        if block_date is None:
            return

        view = self.session.view_for(
            self.current_vehicle,
            block_date,
        )

        self._render_view(view)

    def _show_quality_panel(
        self,
        *,
        title: str,
        intro: str,
        details: tuple[str, ...],
        tone: str,
    ) -> None:
        if tone == "incoherent":
            background = "#fff7ed"
            border = "#fdba74"
            title_color = "#9a3412"
            text_color = "#7c2d12"
        else:
            background = "#fffbeb"
            border = "#fcd34d"
            title_color = "#92400e"
            text_color = "#78350f"

        self.quality_frame.setStyleSheet(
            "QFrame#qualityCard {"
            f"background:{background};"
            f"border:1px solid {border};"
            "border-radius:10px;"
            "}"
        )
        self.quality_title.setStyleSheet(
            f"color:{title_color};font-weight:700;font-size:14px;"
        )
        self.quality_text.setStyleSheet(
            f"color:{text_color};"
        )

        detail_text = "\n".join(
            f"• {detail}"
            for detail in details
        )
        body = intro
        if detail_text:
            body += f"\n\nMotivos detectados:\n{detail_text}"

        self.quality_title.setText(title)
        self.quality_text.setText(body)
        self.quality_frame.show()

    def _render_view(
        self,
        view: GpsDayView,
    ) -> None:
        self.day_title.setText(view.vehicle)
        self.day_subtitle.setText(
            f"Jornada · {view.date_text}"
        )

        if view.quality == "incoherent":
            self.status_badge.setText(
                "⚠ Datos incoherentes"
            )
            self.status_badge.setStyleSheet(
                "background:#ffedd5;"
                "color:#9a3412;"
                "padding:6px 10px;"
                "border-radius:8px;"
                "font-weight:600;"
            )
            self._show_quality_panel(
                title="Datos GPS incoherentes",
                intro=(
                    "Hay actividad GPS, pero los datos de Automatica PLUS "
                    "no son compatibles entre sí. Las métricas superiores muestran los valores del resumen original."
                ),
                details=view.quality_details,
                tone="incoherent",
            )
        elif view.quality == "partial":
            self.status_badge.setText(
                "⚠ Jornada parcial"
            )
            self.status_badge.setStyleSheet(
                "background:#fef3c7;"
                "color:#92400e;"
                "padding:6px 10px;"
                "border-radius:8px;"
                "font-weight:600;"
            )
            self._show_quality_panel(
                title="Jornada parcial",
                intro=(
                    "Hay actividad GPS, pero faltan datos necesarios para "
                    "reconstruir la jornada completa. Se muestra únicamente "
                    "lo que puede interpretarse sin inventar información."
                ),
                details=view.quality_details,
                tone="partial",
            )
        else:
            self.quality_frame.hide()

            if view.active:
                self.status_badge.setText(
                    "Con actividad"
                )
                self.status_badge.setStyleSheet(
                    "background:#dcfce7;"
                    "color:#166534;"
                    "padding:6px 10px;"
                    "border-radius:8px;"
                    "font-weight:600;"
                )
            else:
                self.status_badge.setText(
                    "Sin actividad"
                )
                self.status_badge.setStyleSheet(
                    "background:#f1f5f9;"
                    "color:#64748b;"
                    "padding:6px 10px;"
                    "border-radius:8px;"
                    "font-weight:600;"
                )

        values = {
            "Inicio": view.start_text,
            "Fin": view.end_text,
            "Jornada": view.jornada_text,
            "Conducción": view.driving_text,
            "Tiempo parado": view.stop_text,
            "Kilómetros": view.distance_text,
            "Velocidad punta": view.max_speed_text,
        }

        for name, value in values.items():
            self.metrics[name].value.setText(
                value
            )

        self.table.setRowCount(0)
        self.map_targets.clear()

        for row, item in enumerate(
            view.timeline
        ):
            self.table.insertRow(row)

            if item.kind == "trip":
                origin_text = (
                    item.origin_text
                    or "Origen no disponible"
                )
                destination_text = (
                    item.destination_text
                    or "Destino no disponible"
                )
            else:
                origin_text = "—"
                destination_text = item.location_text

            values = (
                item.label,
                item.start_text,
                item.end_text,
                item.duration_text,
                item.distance_text or "—",
                item.speed_text or "—",
                origin_text,
                destination_text,
            )

            for column, value in enumerate(
                values
            ):
                cell = QTableWidgetItem(
                    str(value)
                )

                if column not in {0, 6, 7}:
                    cell.setTextAlignment(
                        Qt.AlignCenter
                    )

                if column in {6, 7} and str(value) != "—":
                    cell.setToolTip(str(value))

                self.table.setItem(
                    row,
                    column,
                    cell,
                )

            if item.map_target:
                self.map_targets[row] = (
                    item.map_target
                )

        self.event_count.setText(
            f"{len(view.timeline)} eventos"
        )

        if self.table.rowCount():
            self.table.selectRow(0)

    def _open_selected_map(self) -> None:
        row = self.table.currentRow()

        if row < 0:
            QMessageBox.information(
                self,
                "Ubicación",
                "Selecciona primero un evento.",
            )
            return

        target = self.map_targets.get(row)

        if not target:
            QMessageBox.information(
                self,
                "Ubicación",
                "Este evento no contiene un enlace de mapa.",
            )
            return

        QDesktopServices.openUrl(
            QUrl(target)
        )

    def _set_empty_state(self) -> None:
        self.day_title.setText(
            "Sin jornada seleccionada"
        )
        self.day_subtitle.setText(
            "Abre un Excel de Automatica PLUS"
        )

        for card in self.metrics.values():
            card.value.setText("—")

        self.table.setRowCount(0)
        self.event_count.setText("0 eventos")

        self.current_date_text = None
        self.date_button.setText(
            "Selecciona una fecha    ▾"
        )


def main() -> None:
    if sys.platform == "win32":
        try:
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("Stivenarrow.GPSAnalyst")
        except Exception:
            pass

    app = QApplication(sys.argv)

    app.setApplicationName("GPS Analyst")
    app.setApplicationDisplayName("GPS Analyst")
    app.setOrganizationName("Stivenarrow")
    if APP_ICON_PATH.exists():
        app.setWindowIcon(QIcon(str(APP_ICON_PATH)))
    app.setStyle("Fusion")
    app.setStyleSheet(APP_STYLE)

    font = QFont("Segoe UI", 10)
    app.setFont(font)

    window = GpsAnalystWindow()
    window.showMaximized()

    apply_windows_titlebar(window)

    sys.exit(app.exec())


if __name__ == "__main__":
    main()