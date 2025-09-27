from PySide6.QtWidgets import QApplication, QMessageBox
from PySide6.QtCore import Qt
import sys
from PySide6.QtCore import QTimer

from app.ui.main_window import MainWindow
from app.ui.theme import LIGHT_QSS, DARK_QSS, BW_QSS
from app.core.templates import load_default_template, load_session_state
from app.core.models import WatermarkConfig


def main() -> int:
	app = QApplication(sys.argv)
	app.setApplicationName("Watermark Studio")
	# default to black & white theme
	app.setStyleSheet(BW_QSS)
	
	# 检查是否有保存的会话状态
	session_data = load_session_state()
	should_load_session = False
	
	if session_data:
		# 显示弹窗让用户选择是否加载上一次的设置
		reply = QMessageBox.question(
			None,
			"加载上一次设置",
			"是否加载上一次关闭时的设置？",
			QMessageBox.Yes | QMessageBox.No,
			QMessageBox.Yes
		)
		should_load_session = (reply == QMessageBox.Yes)
	else:
		# 如果没有保存的会话状态，直接加载默认模板
		should_load_session = False
	
	# 根据用户选择创建主窗口
	window = MainWindow(load_session=should_load_session)
	
	if not should_load_session:
		# 不加载会话状态，尝试加载默认模板
		default_template = load_default_template()
		if default_template:
			# 使用计时器异步设置默认模板，避免阻塞UI初始化
			QTimer.singleShot(0, lambda cfg=default_template: window.preview.updateConfig(cfg))
			QTimer.singleShot(0, lambda cfg=default_template: window.controls.setConfig(cfg))
	else:
		# 加载会话状态（由MainWindow的初始化方法自动处理）
		pass
	
	window.show()
	return app.exec()


if __name__ == "__main__":
	sys.exit(main())
