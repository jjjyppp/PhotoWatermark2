from PySide6.QtWidgets import QApplication, QMessageBox
from PySide6.QtCore import Qt
import sys
from PySide6.QtCore import QTimer

from app.ui.main_window import MainWindow
from app.ui.theme import LIGHT_QSS, DARK_QSS, BW_QSS
from app.core.templates import load_session_state
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
		# 不加载会话状态，设置默认配置
		# 创建一个新的默认配置对象
		default_cfg = WatermarkConfig()
		# 确保不启用文字和图片水印
		default_cfg.layout.enabled_text = False
		default_cfg.layout.enabled_image = False
		# 确保文本水印内容为"Sample Watermark"
		default_cfg.text.text = "Sample Watermark"
		# 确保文本水印颜色为黑色
		default_cfg.text.color = (0, 0, 0, 255)
		# 确保字号为16
		default_cfg.text.size_px = 16
		# 确保图片缩放为30%
		default_cfg.image.scale = 0.3
		# 确保图片透明度为75%
		default_cfg.image.opacity = 0.75
		# 确保图片旋转为0度
		default_cfg.layout.image_rotation_deg = 0.0
		# 确保位置为正中
		default_cfg.layout.text_position = (0.5, 0.5)
		default_cfg.layout.image_position = (0.5, 0.5)
		
		# 使用基本默认配置（移除默认模板功能）
		cfg_to_use = default_cfg
		
		# 使用计时器异步设置配置，避免阻塞UI初始化
		QTimer.singleShot(0, lambda cfg=cfg_to_use: window.preview.updateConfig(cfg))
		QTimer.singleShot(0, lambda cfg=cfg_to_use: window.controls.setConfig(cfg))
	else:
		# 加载会话状态（由MainWindow的初始化方法自动处理）
		pass
	
	window.show()
	return app.exec()


if __name__ == "__main__":
	sys.exit(main())
