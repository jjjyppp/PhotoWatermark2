from PySide6.QtGui import QPalette, QColor

LIGHT_QSS = """
QWidget { font-family: 'Segoe UI', 'Microsoft YaHei UI', sans-serif; font-size: 12pt; }
QMainWindow { background: #f5f6f7; }
QSplitter::handle { background: #e3e5e8; width: 6px; }
QListWidget { background: #ffffff; border: 1px solid #d8dbe0; }
QListWidget::item { padding: 6px; }
QListWidget::item:selected { background: #f0f0f0; color: #111; }
QPushButton { background: #2563eb; color: white; border: none; padding: 6px 10px; border-radius: 6px; min-height: 28px; }
QPushButton:hover { background: #1d4ed8; }
QPushButton:disabled { background: #93c5fd; }
QLabel { color: #111827; }
QFrame[frameShape="4"] { color: #d1d5db; }
QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox { background: #ffffff; border: 1px solid #d1d5db; border-radius: 6px; padding: 6px; }
QSlider::groove:horizontal { height: 6px; background: #e5e7eb; border-radius: 3px; }
QSlider::handle:horizontal { width: 16px; background: #2563eb; margin: -6px 0; border-radius: 8px; }
QMenu { background: #ffffff; border: 1px solid #e5e7eb; }
QMenu::item:selected { background: #f0f0f0; }
QToolTip { background: #111827; color: white; border: none; }
"""

DARK_QSS = """
QWidget { font-family: 'Segoe UI', 'Microsoft YaHei UI', sans-serif; font-size: 12pt; color: #e5e7eb; }
QMainWindow { background: #111827; }
QSplitter::handle { background: #374151; width: 6px; }
QListWidget { background: #1f2937; border: 1px solid #374151; }
QListWidget::item { padding: 6px; }
QListWidget::item:selected { background: #2b2b2b; color: #e5e7eb; }
QPushButton { background: #0ea5e9; color: #111827; border: none; padding: 6px 10px; border-radius: 6px; min-height: 28px; }
QPushButton:hover { background: #38bdf8; }
QPushButton:disabled { background: #334155; color: #9ca3af; }
QLabel { color: #e5e7eb; }
QFrame[frameShape="4"] { color: #374151; }
QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox { background: #111827; border: 1px solid #374151; border-radius: 6px; padding: 6px; }
QSlider::groove:horizontal { height: 6px; background: #374151; border-radius: 3px; }
QSlider::handle:horizontal { width: 16px; background: #0ea5e9; margin: -6px 0; border-radius: 8px; }
QMenu { background: #111827; border: 1px solid #374151; }
QMenu::item:selected { background: #2b2b2b; color: #e5e7eb; }
QToolTip { background: #0ea5e9; color: #111827; border: none; }
"""

BW_QSS = """
QWidget { font-family: 'Segoe UI', 'Microsoft YaHei UI', sans-serif; font-size: 12pt; color: #111; }
QMainWindow { background: #fff; }
QSplitter::handle { background: #ddd; width: 6px; }
QListWidget { background: #fff; border: 1px solid #000; }
QListWidget::item { padding: 6px; }
QListWidget::item:selected { background: #f0f0f0; color: #111; }
QPushButton { background: #000; color: #fff; border: 2px solid #000; padding: 6px 10px; border-radius: 4px; min-height: 28px; }
QPushButton:hover { background: #fff; color: #000; }
QPushButton:disabled { background: #888; color: #fff; border-color: #888; }
QLabel { color: #000; }
QFrame[frameShape="4"] { color: #000; }
QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox { background: #fff; border: 1px solid #000; border-radius: 4px; padding: 6px; color: #000; }
QSlider::groove:horizontal { height: 6px; background: #000; }
QSlider::handle:horizontal { width: 16px; background: #fff; border: 2px solid #000; margin: -6px 0; border-radius: 8px; }
QMenu { background: #fff; border: 1px solid #000; }
QMenu::item:selected { background: #f0f0f0; color: #111; }
QToolTip { background: #000; color: #fff; border: 1px solid #000; }
"""
