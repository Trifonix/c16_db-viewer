from __future__ import annotations

import sqlite3
import sys
from pathlib import Path
from typing import Any

from PyQt6.QtCore import QEasingCurve, QPropertyAnimation, Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QColor, QFont, QPalette
from PyQt6.QtWidgets import (
    QApplication,
    QFileDialog,
    QFormLayout,
    QFrame,
    QGraphicsOpacityEffect,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QSpinBox,
    QStackedWidget,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

PAGE_SIZE = 25
MAX_COL_WIDTH = 280
MIN_COL_WIDTH = 48

# ── Neon palette ──────────────────────────────────────────────────────────────
BG_DARK = "#0a0e17"
BG_CARD = "#111827"
BG_ELEVATED = "#1a2235"
NEON_CYAN = "#00f5ff"
NEON_MAGENTA = "#ff00aa"
NEON_PURPLE = "#a855f7"
NEON_GREEN = "#39ff14"
TEXT_PRIMARY = "#e2e8f0"
TEXT_MUTED = "#94a3b8"
BORDER = "#1e293b"
GLOW = "rgba(0, 245, 255, 0.35)"


def neon_stylesheet() -> str:
    return f"""
    QMainWindow, QWidget {{
        background-color: {BG_DARK};
        color: {TEXT_PRIMARY};
        font-family: "Segoe UI", "Inter", sans-serif;
        font-size: 13px;
    }}
    QFrame#card {{
        background-color: {BG_CARD};
        border: 1px solid {BORDER};
        border-radius: 14px;
    }}
    QFrame#card:hover {{
        border-color: {NEON_CYAN};
    }}
    QLabel#title {{
        font-size: 26px;
        font-weight: 700;
        color: {NEON_CYAN};
        letter-spacing: 1px;
    }}
    QLabel#subtitle {{
        color: {TEXT_MUTED};
        font-size: 13px;
    }}
    QLabel#pageInfo {{
        color: {TEXT_MUTED};
        padding: 0 12px;
    }}
    QPushButton {{
        background-color: {BG_ELEVATED};
        color: {TEXT_PRIMARY};
        border: 1px solid {BORDER};
        border-radius: 10px;
        padding: 10px 18px;
        font-weight: 600;
        min-height: 20px;
    }}
    QPushButton:hover {{
        border-color: {NEON_CYAN};
        color: {NEON_CYAN};
        background-color: #1f2a40;
    }}
    QPushButton:pressed {{
        background-color: #0d1525;
    }}
    QPushButton#primary {{
        background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
            stop:0 #0ea5e9, stop:1 {NEON_CYAN});
        color: #0a0e17;
        border: none;
        font-weight: 700;
    }}
    QPushButton#primary:hover {{
        background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
            stop:0 {NEON_CYAN}, stop:1 #67e8f9);
        color: #0a0e17;
    }}
    QPushButton#accent {{
        border-color: {NEON_MAGENTA};
        color: {NEON_MAGENTA};
    }}
    QPushButton#accent:hover {{
        background-color: rgba(255, 0, 170, 0.12);
    }}
    QPushButton#danger {{
        border-color: #f43f5e;
        color: #fb7185;
    }}
    QPushButton#danger:hover {{
        background-color: rgba(244, 63, 94, 0.15);
    }}
    QPushButton#success {{
        border-color: {NEON_GREEN};
        color: {NEON_GREEN};
    }}
    QPushButton#success:hover {{
        background-color: rgba(57, 255, 20, 0.1);
    }}
    QPushButton#ghost {{
        background: transparent;
        border: 1px dashed {BORDER};
    }}
    QPushButton#openBtn {{
        background: transparent;
        border: 1px solid {NEON_PURPLE};
        color: {NEON_PURPLE};
        padding: 8px 16px;
        border-radius: 8px;
    }}
    QPushButton#openBtn:hover {{
        background-color: rgba(168, 85, 247, 0.15);
        color: #c084fc;
    }}
    QTableWidget {{
        background-color: {BG_CARD};
        alternate-background-color: {BG_ELEVATED};
        gridline-color: {BORDER};
        border: 1px solid {BORDER};
        border-radius: 12px;
        selection-background-color: rgba(0, 245, 255, 0.18);
        selection-color: {NEON_CYAN};
    }}
    QTableWidget::item {{
        padding: 8px;
        border: none;
    }}
    QHeaderView::section {{
        background-color: {BG_ELEVATED};
        color: {NEON_CYAN};
        padding: 10px;
        border: none;
        border-bottom: 2px solid {NEON_CYAN};
        font-weight: 700;
    }}
    QScrollArea {{
        border: none;
        background: transparent;
    }}
    QScrollBar:vertical {{
        background: {BG_DARK};
        width: 10px;
        border-radius: 5px;
    }}
    QScrollBar::handle:vertical {{
        background: {NEON_PURPLE};
        border-radius: 5px;
        min-height: 30px;
    }}
    QLineEdit, QSpinBox {{
        background-color: {BG_ELEVATED};
        border: 1px solid {BORDER};
        border-radius: 8px;
        padding: 8px 12px;
        color: {TEXT_PRIMARY};
        selection-background-color: {NEON_CYAN};
        selection-color: {BG_DARK};
    }}
    QLineEdit:focus, QSpinBox:focus {{
        border-color: {NEON_CYAN};
    }}
    QDialog {{
        background-color: {BG_CARD};
    }}
    """


class AnimatedButton(QPushButton):
    """Button with brief opacity pulse on click."""

    def __init__(self, text: str = "", parent: QWidget | None = None) -> None:
        super().__init__(text, parent)
        self._anim: QPropertyAnimation | None = None
        self.clicked.connect(self._pulse)

    def _pulse(self) -> None:
        effect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(effect)
        effect.setOpacity(1.0)

        if self._anim is not None:
            self._anim.stop()

        self._anim = QPropertyAnimation(effect, b"opacity", self)
        self._anim.setDuration(180)
        self._anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._anim.setKeyValueAt(0, 1.0)
        self._anim.setKeyValueAt(0.45, 0.55)
        self._anim.setKeyValueAt(1, 1.0)

        def cleanup() -> None:
            self.setGraphicsEffect(None)
            self._anim = None

        self._anim.finished.connect(cleanup)
        self._anim.start()


class FadeStack(QStackedWidget):
    """Stacked widget with cross-fade transitions."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._anim_out: QPropertyAnimation | None = None
        self._anim_in: QPropertyAnimation | None = None

    def _ensure_visible(self, widget: QWidget | None) -> None:
        if widget is None:
            return
        widget.setGraphicsEffect(None)
        widget.show()

    def setCurrentIndexAnimated(self, index: int) -> None:
        if index < 0 or index >= self.count():
            return

        incoming = self.widget(index)
        if incoming is None:
            return

        if index == self.currentIndex():
            self._ensure_visible(incoming)
            return

        outgoing = self.currentWidget()

        if outgoing is None:
            self.setCurrentIndex(index)
            self._ensure_visible(incoming)
            return

        if self._anim_out is not None:
            self._anim_out.stop()
        if self._anim_in is not None:
            self._anim_in.stop()

        self._ensure_visible(outgoing)
        self._ensure_visible(incoming)

        out_effect = QGraphicsOpacityEffect(outgoing)
        outgoing.setGraphicsEffect(out_effect)
        out_effect.setOpacity(1.0)

        in_effect = QGraphicsOpacityEffect(incoming)
        incoming.setGraphicsEffect(in_effect)
        in_effect.setOpacity(0.0)

        self.setCurrentIndex(index)

        self._anim_out = QPropertyAnimation(out_effect, b"opacity", self)
        self._anim_out.setDuration(220)
        self._anim_out.setStartValue(1.0)
        self._anim_out.setEndValue(0.0)
        self._anim_out.setEasingCurve(QEasingCurve.Type.InOutQuad)

        self._anim_in = QPropertyAnimation(in_effect, b"opacity", self)
        self._anim_in.setDuration(280)
        self._anim_in.setStartValue(0.0)
        self._anim_in.setEndValue(1.0)
        self._anim_in.setEasingCurve(QEasingCurve.Type.InOutQuad)

        def cleanup() -> None:
            self._ensure_visible(outgoing)
            self._ensure_visible(incoming)
            self._anim_out = None
            self._anim_in = None

        self._anim_in.finished.connect(cleanup)
        self._anim_out.start()
        self._anim_in.start()


class RecordEditorPanel(QFrame):
    """Inline scrollable form for insert / update (embedded in the data view)."""

    saved = pyqtSignal()
    cancelled = pyqtSignal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("card")
        self.columns: list[str] = []
        self.pk_columns: list[str] = []
        self.edit_mode = False
        self.fields: dict[str, QLineEdit] = {}

        outer = QVBoxLayout(self)
        outer.setContentsMargins(16, 14, 16, 14)
        outer.setSpacing(10)

        self.title_label = QLabel("")
        self.title_label.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        self.title_label.setStyleSheet(f"color: {NEON_MAGENTA};")
        outer.addWidget(self.title_label)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setMinimumHeight(120)
        scroll.setMaximumHeight(320)

        self._form_host = QWidget()
        self._form_layout = QFormLayout(self._form_host)
        self._form_layout.setSpacing(10)
        self._form_layout.setContentsMargins(4, 4, 12, 4)
        scroll.setWidget(self._form_host)
        outer.addWidget(scroll, stretch=1)

        buttons = QHBoxLayout()
        buttons.addStretch()
        save_btn = AnimatedButton("Сохранить")
        save_btn.setObjectName("success")
        save_btn.clicked.connect(self.saved.emit)
        cancel_btn = AnimatedButton("Отмена")
        cancel_btn.setObjectName("ghost")
        cancel_btn.clicked.connect(self.cancelled.emit)
        buttons.addWidget(cancel_btn)
        buttons.addWidget(save_btn)
        outer.addLayout(buttons)

        self.hide()

    def _clear_fields(self) -> None:
        while self._form_layout.count():
            item = self._form_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
        self.fields.clear()

    def open_form(
        self,
        columns: list[str],
        pk_columns: list[str],
        values: dict[str, Any] | None = None,
        edit_mode: bool = False,
    ) -> None:
        self.columns = columns
        self.pk_columns = pk_columns
        self.edit_mode = edit_mode
        self._clear_fields()

        self.title_label.setText(
            "Редактировать запись" if edit_mode else "Новая запись"
        )

        for col in columns:
            field = QLineEdit()
            if edit_mode and col in pk_columns:
                field.setReadOnly(True)
                field.setStyleSheet(f"color: {TEXT_MUTED};")
            if values and col in values and values[col] is not None:
                field.setText(str(values[col]))
            self.fields[col] = field
            self._form_layout.addRow(col, field)

        self.show()

    def close_form(self) -> None:
        self.hide()
        self._clear_fields()

    def get_values(self) -> dict[str, str]:
        return {col: field.text() for col, field in self.fields.items()}


class TableCard(QFrame):
    """Single table row in the list view."""

    def __init__(self, table_name: str, row_count: int, on_open, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("card")
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 16, 20, 16)

        info = QVBoxLayout()
        name_label = QLabel(table_name)
        name_label.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        name_label.setStyleSheet(f"color: {TEXT_PRIMARY};")
        count_label = QLabel(f"{row_count:,} строк".replace(",", " "))
        count_label.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 12px;")
        info.addWidget(name_label)
        info.addWidget(count_label)

        open_btn = AnimatedButton("Открыть")
        open_btn.setObjectName("openBtn")
        open_btn.setFixedWidth(120)
        open_btn.clicked.connect(lambda: on_open(table_name))

        layout.addLayout(info, stretch=1)
        layout.addWidget(open_btn)


class DatabaseBrowser(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.db_path: Path | None = None
        self.conn: sqlite3.Connection | None = None
        self.current_table: str | None = None
        self.columns: list[str] = []
        self.pk_columns: list[str] = []
        self.current_page = 0
        self.total_rows = 0

        self.setWindowTitle("test-db — SQLite Browser")
        self.setMinimumSize(960, 640)
        self.resize(1100, 720)
        self.setStyleSheet(neon_stylesheet())

        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(28, 24, 28, 24)
        root.setSpacing(20)

        # Header
        header = QHBoxLayout()
        title_block = QVBoxLayout()
        title = QLabel("test-db")
        title.setObjectName("title")
        subtitle = QLabel("Просмотр SQLite с неоновым интерфейсом")
        subtitle.setObjectName("subtitle")
        title_block.addWidget(title)
        title_block.addWidget(subtitle)

        self.file_label = QLabel("Файл не выбран")
        self.file_label.setObjectName("subtitle")
        self.file_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

        open_file_btn = AnimatedButton("Выбрать .db")
        open_file_btn.setObjectName("primary")
        open_file_btn.clicked.connect(self.open_database)

        header.addLayout(title_block, stretch=1)
        header.addWidget(self.file_label, stretch=2)
        header.addWidget(open_file_btn)
        root.addLayout(header)

        # Stacked views
        self.stack = FadeStack()
        root.addWidget(self.stack, stretch=1)

        self.tables_page = self._build_tables_page()
        self.data_page = self._build_data_page()
        self.stack.addWidget(self.tables_page)
        self.stack.addWidget(self.data_page)

        self._show_empty_state()

    def _build_tables_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)

        self.tables_header = QLabel("Таблицы")
        self.tables_header.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        self.tables_header.setStyleSheet(f"color: {NEON_MAGENTA};")
        layout.addWidget(self.tables_header)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self.tables_container = QWidget()
        self.tables_layout = QVBoxLayout(self.tables_container)
        self.tables_layout.setSpacing(12)
        self.tables_layout.addStretch()

        scroll.setWidget(self.tables_container)
        layout.addWidget(scroll, 1)
        return page

    def _build_data_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)

        nav = QHBoxLayout()
        back_btn = AnimatedButton("← Назад")
        back_btn.setObjectName("ghost")
        back_btn.clicked.connect(self._go_back_to_tables)

        self.table_title = QLabel("")
        self.table_title.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        self.table_title.setStyleSheet(f"color: {NEON_CYAN};")

        nav.addWidget(back_btn)
        nav.addWidget(self.table_title)
        nav.addStretch()
        layout.addLayout(nav)

        # CRUD toolbar
        crud = QHBoxLayout()
        crud.setSpacing(10)

        add_btn = AnimatedButton("+ Добавить")
        add_btn.setObjectName("success")
        add_btn.clicked.connect(self.add_record)

        edit_btn = AnimatedButton("✎ Изменить")
        edit_btn.setObjectName("accent")
        edit_btn.clicked.connect(self.edit_record)

        del_btn = AnimatedButton("✕ Удалить")
        del_btn.setObjectName("danger")
        del_btn.clicked.connect(self.delete_record)

        refresh_btn = AnimatedButton("↻ Обновить")
        refresh_btn.clicked.connect(self.refresh_table)

        crud.addWidget(add_btn)
        crud.addWidget(edit_btn)
        crud.addWidget(del_btn)
        crud.addStretch()
        crud.addWidget(refresh_btn)
        layout.addLayout(crud)

        self.record_panel = RecordEditorPanel()
        self.record_panel.saved.connect(self._save_record_panel)
        self.record_panel.cancelled.connect(self.record_panel.close_form)
        layout.addWidget(self.record_panel)

        self.data_table = QTableWidget()
        self.data_table.setAlternatingRowColors(True)
        self.data_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.data_table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.data_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.data_table.setWordWrap(True)
        self.data_table.setHorizontalScrollMode(QTableWidget.ScrollMode.ScrollPerPixel)
        self.data_table.setVerticalScrollMode(QTableWidget.ScrollMode.ScrollPerPixel)
        header = self.data_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        header.setStretchLastSection(False)
        header.setMinimumSectionSize(MIN_COL_WIDTH)
        self.data_table.verticalHeader().setVisible(False)
        layout.addWidget(self.data_table)

        # Pagination
        pag = QHBoxLayout()
        pag.addStretch()

        self.prev_btn = AnimatedButton("◀ Назад")
        self.prev_btn.clicked.connect(self.prev_page)

        self.page_info = QLabel("")
        self.page_info.setObjectName("pageInfo")

        self.next_btn = AnimatedButton("Вперёд ▶")
        self.next_btn.clicked.connect(self.next_page)

        self.page_spin = QSpinBox()
        self.page_spin.setMinimum(1)
        self.page_spin.setPrefix("Стр. ")
        self.page_spin.valueChanged.connect(self._goto_page)

        pag.addWidget(self.prev_btn)
        pag.addWidget(self.page_info)
        pag.addWidget(self.page_spin)
        pag.addWidget(self.next_btn)
        layout.addLayout(pag)

        return page

    def _go_back_to_tables(self) -> None:
        self.record_panel.close_form()
        self.stack.setCurrentIndexAnimated(0)

    def _show_empty_state(self) -> None:
        self._clear_layout(self.tables_layout)
        placeholder = QFrame()
        placeholder.setObjectName("card")
        pl = QVBoxLayout(placeholder)
        pl.setContentsMargins(40, 48, 40, 48)
        msg = QLabel("Выберите файл SQLite (.db, .sqlite, .sqlite3)")
        msg.setAlignment(Qt.AlignmentFlag.AlignCenter)
        msg.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 15px;")
        pl.addWidget(msg)
        self.tables_layout.insertWidget(0, placeholder)

    def _clear_layout(self, layout: QVBoxLayout) -> None:
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

    def open_database(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Открыть SQLite",
            str(Path.home()),
            "SQLite (*.db *.sqlite *.sqlite3);;All (*.*)",
        )
        if not path:
            return

        if self.conn:
            self.conn.close()

        try:
            self.conn = sqlite3.connect(path)
            self.conn.row_factory = sqlite3.Row
            self.db_path = Path(path)
        except sqlite3.Error as exc:
            QMessageBox.critical(self, "Ошибка", f"Не удалось открыть базу:\n{exc}")
            return

        self.file_label.setText(self.db_path.name)
        self.file_label.setStyleSheet(f"color: {NEON_GREEN}; font-weight: 600;")
        self.load_tables()

    def load_tables(self) -> None:
        if not self.conn:
            return

        try:
            tables = self.conn.execute(
                "SELECT name FROM sqlite_master "
                "WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name"
            ).fetchall()
        except sqlite3.Error as exc:
            QMessageBox.warning(self, "Ошибка", f"Не удалось прочитать таблицы:\n{exc}")
            return

        cards: list[QWidget] = []
        try:
            for row in tables:
                name = row["name"] if hasattr(row, "keys") else row[0]
                count = self.conn.execute(
                    f'SELECT COUNT(*) AS c FROM "{name}"'
                ).fetchone()[0]
                cards.append(TableCard(name, count, self.open_table))
        except (sqlite3.Error, TypeError, IndexError) as exc:
            QMessageBox.warning(self, "Ошибка", f"Не удалось загрузить таблицы:\n{exc}")
            return

        self._clear_layout(self.tables_layout)

        if not cards:
            empty = QLabel("В базе нет пользовательских таблиц")
            empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
            empty.setStyleSheet(f"color: {TEXT_MUTED}; padding: 40px;")
            self.tables_layout.addWidget(empty)
        else:
            for card in cards:
                self.tables_layout.addWidget(card)

        self.tables_layout.addStretch()
        self.stack.setCurrentIndexAnimated(0)
        self.tables_container.adjustSize()

    def open_table(self, table_name: str) -> None:
        if not self.conn:
            return

        self.current_table = table_name
        self.current_page = 0
        self.record_panel.close_form()

        info = self.conn.execute(f'PRAGMA table_info("{table_name}")').fetchall()
        self.columns = [r["name"] for r in info]
        self.pk_columns = [r["name"] for r in info if r["pk"]]

        self.table_title.setText(f"📋 {table_name}")
        self.refresh_table()
        self.stack.setCurrentIndexAnimated(1)

    def refresh_table(self) -> None:
        if not self.conn or not self.current_table:
            return

        table = self.current_table
        self.total_rows = self.conn.execute(
            f'SELECT COUNT(*) AS c FROM "{table}"'
        ).fetchone()["c"]

        total_pages = max(1, (self.total_rows + PAGE_SIZE - 1) // PAGE_SIZE)
        self.current_page = min(self.current_page, total_pages - 1)

        offset = self.current_page * PAGE_SIZE
        col_list = ", ".join(f'"{c}"' for c in self.columns)
        rows = self.conn.execute(
            f'SELECT {col_list} FROM "{table}" LIMIT ? OFFSET ?',
            (PAGE_SIZE, offset),
        ).fetchall()

        self.data_table.setColumnCount(len(self.columns))
        self.data_table.setHorizontalHeaderLabels(self.columns)
        self.data_table.setRowCount(len(rows))

        for r_idx, row in enumerate(rows):
            for c_idx, col in enumerate(self.columns):
                val = row[col]
                text = "" if val is None else str(val)
                item = QTableWidgetItem(text)
                item.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
                item.setToolTip(text)
                self.data_table.setItem(r_idx, c_idx, item)

        self._fit_table_columns()

        start = offset + 1 if self.total_rows else 0
        end = min(offset + PAGE_SIZE, self.total_rows)
        self.page_info.setText(
            f"Записи {start}–{end} из {self.total_rows:,}".replace(",", " ")
        )

        self.page_spin.blockSignals(True)
        self.page_spin.setMaximum(total_pages)
        self.page_spin.setValue(self.current_page + 1)
        self.page_spin.blockSignals(False)

        self.prev_btn.setEnabled(self.current_page > 0)
        self.next_btn.setEnabled(self.current_page < total_pages - 1)

    def _fit_table_columns(self) -> None:
        """Size columns to content with compact min/max bounds."""
        header = self.data_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        self.data_table.resizeColumnsToContents()

        for col in range(len(self.columns)):
            width = header.sectionSize(col)
            if width > MAX_COL_WIDTH:
                header.resizeSection(col, MAX_COL_WIDTH)
            elif width < MIN_COL_WIDTH:
                header.resizeSection(col, MIN_COL_WIDTH)

        header.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self.data_table.resizeRowsToContents()

    def prev_page(self) -> None:
        if self.current_page > 0:
            self.current_page -= 1
            self.refresh_table()

    def next_page(self) -> None:
        total_pages = max(1, (self.total_rows + PAGE_SIZE - 1) // PAGE_SIZE)
        if self.current_page < total_pages - 1:
            self.current_page += 1
            self.refresh_table()

    def _goto_page(self, page: int) -> None:
        self.current_page = page - 1
        self.refresh_table()

    def _selected_row_values(self) -> dict[str, Any] | None:
        row_idx = self.data_table.currentRow()
        if row_idx < 0:
            return None
        return {
            self.columns[c]: self.data_table.item(row_idx, c).text()
            for c in range(len(self.columns))
        }

    def add_record(self) -> None:
        if not self.conn or not self.current_table:
            return

        self.record_panel.open_form(self.columns, self.pk_columns)

    def edit_record(self) -> None:
        if not self.conn or not self.current_table:
            return

        current = self._selected_row_values()
        if not current:
            QMessageBox.information(self, "Выбор", "Выберите строку для редактирования.")
            return

        self.record_panel.open_form(
            self.columns,
            self.pk_columns,
            values=current,
            edit_mode=True,
        )

    def _save_record_panel(self) -> None:
        if not self.conn or not self.current_table:
            return

        panel = self.record_panel
        if panel.edit_mode:
            self._commit_edit(panel)
        else:
            self._commit_insert(panel)

    def _commit_insert(self, panel: RecordEditorPanel) -> None:
        values = panel.get_values()
        placeholders = ", ".join("?" for _ in self.columns)
        col_names = ", ".join(f'"{c}"' for c in self.columns)
        sql = f'INSERT INTO "{self.current_table}" ({col_names}) VALUES ({placeholders})'

        try:
            self.conn.execute(sql, [values[c] for c in self.columns])
            self.conn.commit()
            panel.close_form()
            self.refresh_table()
            self.load_tables()
        except sqlite3.Error as exc:
            QMessageBox.warning(self, "Ошибка", f"Не удалось добавить запись:\n{exc}")

    def _commit_edit(self, panel: RecordEditorPanel) -> None:
        row_idx = self.data_table.currentRow()
        if row_idx < 0:
            return

        current = {
            self.columns[c]: self.data_table.item(row_idx, c).text()
            for c in range(len(self.columns))
        }

        if not self.pk_columns:
            QMessageBox.warning(
                self,
                "Первичный ключ",
                "У таблицы нет первичного ключа — редактирование небезопасно.",
            )
            return

        new_values = panel.get_values()
        set_clause = ", ".join(f'"{c}" = ?' for c in self.columns if c not in self.pk_columns)
        where_clause = " AND ".join(f'"{c}" = ?' for c in self.pk_columns)
        params = [new_values[c] for c in self.columns if c not in self.pk_columns]
        params += [current[c] for c in self.pk_columns]

        sql = f'UPDATE "{self.current_table}" SET {set_clause} WHERE {where_clause}'

        try:
            self.conn.execute(sql, params)
            self.conn.commit()
            panel.close_form()
            self.refresh_table()
        except sqlite3.Error as exc:
            QMessageBox.warning(self, "Ошибка", f"Не удалось обновить запись:\n{exc}")

    def delete_record(self) -> None:
        if not self.conn or not self.current_table:
            return

        current = self._selected_row_values()
        if not current:
            QMessageBox.information(self, "Выбор", "Выберите строку для удаления.")
            return

        if not self.pk_columns:
            QMessageBox.warning(
                self,
                "Первичный ключ",
                "У таблицы нет первичного ключа — удаление небезопасно.",
            )
            return

        answer = QMessageBox.question(
            self,
            "Подтверждение",
            "Удалить выбранную запись?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if answer != QMessageBox.StandardButton.Yes:
            return

        where_clause = " AND ".join(f'"{c}" = ?' for c in self.pk_columns)
        params = [current[c] for c in self.pk_columns]
        sql = f'DELETE FROM "{self.current_table}" WHERE {where_clause}'

        try:
            self.conn.execute(sql, params)
            self.conn.commit()
            self.refresh_table()
            self.load_tables()
        except sqlite3.Error as exc:
            QMessageBox.warning(self, "Ошибка", f"Не удалось удалить запись:\n{exc}")

    def closeEvent(self, event) -> None:
        if self.conn:
            self.conn.close()
        super().closeEvent(event)


def create_sample_db(path: Path) -> None:
    """Create a demo database if launched with --sample."""
    conn = sqlite3.connect(path)
    conn.executescript(
        """
        CREATE TABLE users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE,
            role TEXT DEFAULT 'user'
        );
        CREATE TABLE products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            price REAL,
            in_stock INTEGER DEFAULT 1
        );
        INSERT INTO users (name, email, role) VALUES
            ('Алиса', 'alice@example.com', 'admin'),
            ('Боб', 'bob@example.com', 'user'),
            ('Вика', 'vika@example.com', 'user');
        INSERT INTO products (title, price, in_stock) VALUES
            ('Neon Keyboard', 149.99, 1),
            ('Glow Mouse', 59.50, 1),
            ('RGB Monitor', 399.00, 0);
        """
    )
    conn.commit()
    conn.close()


def main() -> None:
    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window, QColor(BG_DARK))
    palette.setColor(QPalette.ColorRole.WindowText, QColor(TEXT_PRIMARY))
    app.setPalette(palette)

    if len(sys.argv) > 1 and sys.argv[1] == "--sample":
        sample = Path(__file__).parent / "sample.db"
        create_sample_db(sample)
        print(f"Sample database created: {sample}")

    window = DatabaseBrowser()

    if len(sys.argv) > 1 and sys.argv[1] != "--sample":
        db_arg = Path(sys.argv[1])
        if db_arg.exists():
            QTimer.singleShot(100, lambda: _auto_open(window, db_arg))

    window.showMaximized()
    sys.exit(app.exec())


def _auto_open(window: DatabaseBrowser, path: Path) -> None:
    if window.conn:
        window.conn.close()
    window.conn = sqlite3.connect(str(path))
    window.conn.row_factory = sqlite3.Row
    window.db_path = path
    window.file_label.setText(path.name)
    window.file_label.setStyleSheet(f"color: {NEON_GREEN}; font-weight: 600;")
    window.load_tables()


if __name__ == "__main__":
    main()
