from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt
import sys

from app.ui.main_window import MainWindow
from app.ui.theme import LIGHT_QSS, DARK_QSS, BW_QSS


def main() -> int:
	app = QApplication(sys.argv)
	app.setApplicationName("Watermark Studio")
	# default to black & white theme
	app.setStyleSheet(BW_QSS)
	window = MainWindow()
	window.show()
	return app.exec()


if __name__ == "__main__":
	sys.exit(main())
