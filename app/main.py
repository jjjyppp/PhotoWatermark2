from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt
import sys
from PySide6.QtCore import QTimer

from app.ui.main_window import MainWindow
from app.ui.theme import LIGHT_QSS, DARK_QSS, BW_QSS
from app.core.templates import load_default_template
from app.core.models import WatermarkConfig


def main() -> int:
	app = QApplication(sys.argv)
	app.setApplicationName("Watermark Studio")
	# default to black & white theme
	app.setStyleSheet(BW_QSS)
	window = MainWindow()
	
	# 尝试加载默认模板
	default_template = load_default_template()
	if default_template:
		# 使用计时器异步设置默认模板，避免阻塞UI初始化
		QTimer.singleShot(0, lambda cfg=default_template: window.preview.updateConfig(cfg))
		QTimer.singleShot(0, lambda cfg=default_template: window.controls.setConfig(cfg))
	
	window.show()
	return app.exec()


if __name__ == "__main__":
	sys.exit(main())
