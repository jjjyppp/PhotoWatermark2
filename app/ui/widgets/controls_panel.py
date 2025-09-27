from PySide6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QLabel, QFrame, QLineEdit, QHBoxLayout, QSlider, QFileDialog, QComboBox, QCheckBox, QFontComboBox, QListWidget, QListWidgetItem, QColorDialog, QMenu, QInputDialog, QGridLayout, QDoubleSpinBox, QScrollArea, QSizePolicy
from PySide6.QtCore import Qt, Signal, QPoint

import os
import math

from app.core.models import WatermarkConfig
from app.core.templates import save_template, list_templates, load_template, save_last_settings, delete_template, rename_template
from PySide6.QtGui import QFont, QColor
from .auto_fit_button import AutoFitButton
from shiboken6 import isValid


class ControlsPanel(QWidget):
	requestOpenFiles = Signal()
	requestOpenFolder = Signal()
	configChanged = Signal(WatermarkConfig)
	applyTemplateToSelected = Signal(str)
	applyTemplateToAll = Signal(str)
	dragTargetChanged = Signal(str)  # 'text' or 'image'
	exportClicked = Signal()  # 新增导出按钮点击信号

	def __init__(self, parent=None) -> None:
		super().__init__(parent)
		# Wider panel to avoid cramped rows
		self.setMinimumWidth(420)
		# 创建配置对象并设置默认值
		self._cfg = WatermarkConfig()
		# 确保不启用文字和图片水印
		self._cfg.layout.enabled_text = False
		self._cfg.layout.enabled_image = False
		# 确保字号为16
		self._cfg.text.size_px = 16
		# 确保图片缩放为30%
		self._cfg.image.scale = 0.3
		# 确保位置为正中
		self._cfg.layout.text_position = (0.5, 0.5)
		self._cfg.layout.image_position = (0.5, 0.5)
		self._ready = True

		scroll = QScrollArea(self)
		scroll.setWidgetResizable(True)
		content = QWidget()
		layout = QVBoxLayout(content)
		layout.setContentsMargins(6, 6, 6, 6)
		layout.setSpacing(4)

		title = QLabel("导入与设置")
		layout.addWidget(title)

		def small(btn: AutoFitButton) -> AutoFitButton:
			btn.setMinimumHeight(26)
			return btn

		btn_files = small(AutoFitButton("导入图片"))
		btn_files.clicked.connect(self.requestOpenFiles.emit)
		layout.addWidget(btn_files)

		btn_folder = small(AutoFitButton("导入文件夹"))
		btn_folder.clicked.connect(self.requestOpenFolder.emit)
		layout.addWidget(btn_folder)

		line = QFrame(); line.setFrameShape(QFrame.HLine); layout.addWidget(line)

		# Text watermark
		self.chk_text = QCheckBox("启用文本水印")
		self.chk_text.setChecked(self._cfg.layout.enabled_text)
		self.chk_text.stateChanged.connect(lambda s: self._set_enabled_text(bool(s)))
		layout.addWidget(self.chk_text)

		self.txt_input = QLineEdit(self._cfg.text.text)
		self.txt_input.setPlaceholderText("输入水印文本")
		self.txt_input.textChanged.connect(self._on_text)
		layout.addWidget(self.txt_input)

		font_row = QHBoxLayout()
		self.font_combo = QFontComboBox(); self.font_combo.setFontFilters(QFontComboBox.ScalableFonts)
		self.font_combo.setCurrentFont(QFont(self._cfg.text.family))
		self.font_combo.currentFontChanged.connect(self._on_font_family)
		self.font_combo.setMinimumWidth(180)
		font_row.addWidget(self.font_combo)
		self.chk_bold = QCheckBox("粗体"); self.chk_bold.stateChanged.connect(self._on_bold)
		self.chk_italic = QCheckBox("斜体"); self.chk_italic.stateChanged.connect(self._on_italic)
		font_row.addWidget(self.chk_bold); font_row.addWidget(self.chk_italic)
		layout.addLayout(font_row)

		hbox_font = QHBoxLayout()
		hbox_font.setSpacing(4)
		hbox_font.addWidget(QLabel("字号"))
		self.slider_fs = QSlider(Qt.Horizontal); self.slider_fs.setRange(8, 128); self.slider_fs.setValue(getattr(self._cfg.text, "size_px", 16))
		self.spin_fs = QDoubleSpinBox(); self.spin_fs.setRange(8, 128); self.spin_fs.setDecimals(0); self.spin_fs.setValue(getattr(self._cfg.text, "size_px", 16)); self.spin_fs.setFixedWidth(80)
		self.slider_fs.valueChanged.connect(lambda v: (self.spin_fs.setValue(v), self._on_font_size(int(v))))
		self.spin_fs.valueChanged.connect(lambda v: (self.slider_fs.setValue(int(v)), self._on_font_size(int(v))))
		hbox_font.addWidget(self.slider_fs, 1); hbox_font.addWidget(self.spin_fs)
		layout.addLayout(hbox_font)

		row_color = QHBoxLayout(); row_color.setSpacing(4)
		color_label = QLabel("颜色")
		# 添加颜色显示标签
		self.color_preview = QLabel()
		self.color_preview.setFixedSize(20, 20)
		self.color_preview.setFrameStyle(QFrame.Panel | QFrame.Sunken)
		self.color_preview.setStyleSheet("background-color: black")  # 默认黑色
		self.color_preview.setCursor(Qt.PointingHandCursor)  # 设置鼠标指针为手形
		self.color_preview.mousePressEvent = lambda event: self._pick_color()
		row_color.addWidget(color_label)
		row_color.addWidget(self.color_preview)
		# 颜色下拉框添加自定义选项
		self.cmb_color = QComboBox(); self.cmb_color.addItems(["白", "黑", "红", "绿", "蓝", "自定义"]) ; self.cmb_color.currentIndexChanged.connect(self._on_color)
		# 默认改为黑色
		self.cmb_color.setCurrentIndex(1)
		row_color.addWidget(self.cmb_color)
		layout.addLayout(row_color)

		row_text_op = QHBoxLayout(); row_text_op.setSpacing(4); row_text_op.addWidget(QLabel("文本透明度(%)"))
		self.slider_text_op = QSlider(Qt.Horizontal); self.slider_text_op.setRange(0, 100); self.slider_text_op.setValue(int(self._cfg.text.color[3]*100/255))
		self.spin_text_op = QDoubleSpinBox(); self.spin_text_op.setRange(0, 100); self.spin_text_op.setDecimals(0); self.spin_text_op.setValue(int(self._cfg.text.color[3]*100/255)); self.spin_text_op.setFixedWidth(80)
		self.slider_text_op.valueChanged.connect(lambda v: (self.spin_text_op.setValue(v), self._on_text_opacity(int(v))))
		self.spin_text_op.valueChanged.connect(lambda v: (self.slider_text_op.setValue(int(v)), self._on_text_opacity(int(v))))
		row_text_op.addWidget(self.slider_text_op, 1); row_text_op.addWidget(self.spin_text_op)
		layout.addLayout(row_text_op)

		# 文本旋转控制
		row_rot_text = QHBoxLayout(); row_rot_text.setSpacing(4); row_rot_text.addWidget(QLabel("文本旋转(°)"))
		self.slider_rot_text = QSlider(Qt.Horizontal); self.slider_rot_text.setRange(0, 360); self.slider_rot_text.setValue(int(getattr(self._cfg.layout, "text_rotation_deg", 0.0) or getattr(self._cfg.layout, "rotation_deg", 0.0)))
		self.spin_rot_text = QDoubleSpinBox(); self.spin_rot_text.setRange(0.0, 360.0); self.spin_rot_text.setDecimals(0); self.spin_rot_text.setValue(float(getattr(self._cfg.layout, "text_rotation_deg", 0.0) or getattr(self._cfg.layout, "rotation_deg", 0.0))); self.spin_rot_text.setFixedWidth(80)
		self.slider_rot_text.valueChanged.connect(lambda v: (self.spin_rot_text.setValue(v), self._on_rotation_text(int(v))))
		self.spin_rot_text.valueChanged.connect(lambda v: (self.slider_rot_text.setValue(int(v)), self._on_rotation_text(int(v))))
		row_rot_text.addWidget(self.slider_rot_text, 1); row_rot_text.addWidget(self.spin_rot_text)
		layout.addLayout(row_rot_text)

		row_effects = QHBoxLayout(); row_effects.setSpacing(4)
		self.chk_shadow = QCheckBox("阴影"); self.chk_shadow.stateChanged.connect(self._on_shadow)
		self.chk_outline = QCheckBox("描边"); self.chk_outline.stateChanged.connect(self._on_outline)
		row_effects.addWidget(self.chk_shadow); row_effects.addWidget(self.chk_outline)
		layout.addLayout(row_effects)

		line2 = QFrame(); line2.setFrameShape(QFrame.HLine); layout.addWidget(line2)

		# Image watermark
		self.chk_img = QCheckBox("启用图片水印")
		self.chk_img.setChecked(self._cfg.layout.enabled_image)
		self.chk_img.stateChanged.connect(lambda s: self._set_enabled_image(bool(s)))
		layout.addWidget(self.chk_img)

		btn_logo = AutoFitButton("选择图片水印"); btn_logo.clicked.connect(self._pick_logo)
		layout.addWidget(btn_logo)

		row_logo_scale = QHBoxLayout(); row_logo_scale.setSpacing(4); row_logo_scale.addWidget(QLabel("图片缩放(%)"))
		self.slider_scale = QSlider(Qt.Horizontal); self.slider_scale.setRange(5, 300); self.slider_scale.setValue(int(self._cfg.image.scale*100))
		self.spin_scale = QDoubleSpinBox(); self.spin_scale.setRange(5.0, 300.0); self.spin_scale.setDecimals(0); self.spin_scale.setSingleStep(1.0); self.spin_scale.setValue(self._cfg.image.scale*100); self.spin_scale.setFixedWidth(80)
		self.slider_scale.valueChanged.connect(lambda v: (self.spin_scale.setValue(v), self._on_logo_scale(int(v))))
		self.spin_scale.valueChanged.connect(lambda v: (self.slider_scale.setValue(int(v)), self._on_logo_scale(int(v))))

		# Note: non-uniform scaling is done on-canvas via handles; UI shows uniform percent only
		row_logo_scale.addWidget(self.slider_scale, 1); row_logo_scale.addWidget(self.spin_scale)
		layout.addLayout(row_logo_scale)

		row_logo_op = QHBoxLayout(); row_logo_op.setSpacing(4); row_logo_op.addWidget(QLabel("图片透明度(%)"))
		self.slider_logo_op = QSlider(Qt.Horizontal); self.slider_logo_op.setRange(0, 100); self.slider_logo_op.setValue(int(self._cfg.image.opacity*100))
		self.spin_logo_op = QDoubleSpinBox(); self.spin_logo_op.setRange(0, 100); self.spin_logo_op.setDecimals(0); self.spin_logo_op.setValue(int(self._cfg.image.opacity*100)); self.spin_logo_op.setFixedWidth(80)
		self.slider_logo_op.valueChanged.connect(lambda v: (self.spin_logo_op.setValue(v), self._on_logo_opacity(int(v))))
		self.spin_logo_op.valueChanged.connect(lambda v: (self.slider_logo_op.setValue(int(v)), self._on_logo_opacity(int(v))))
		row_logo_op.addWidget(self.slider_logo_op, 1); row_logo_op.addWidget(self.spin_logo_op)
		layout.addLayout(row_logo_op)

		# 图片旋转控制
		row_rot_img = QHBoxLayout(); row_rot_img.setSpacing(4); row_rot_img.addWidget(QLabel("图片旋转(°)"))
		self.slider_rot_img = QSlider(Qt.Horizontal); self.slider_rot_img.setRange(0, 360); self.slider_rot_img.setValue(int(getattr(self._cfg.layout, "image_rotation_deg", 0.0) or getattr(self._cfg.layout, "rotation_deg", 0.0)))
		self.spin_rot_img = QDoubleSpinBox(); self.spin_rot_img.setRange(0.0, 360.0); self.spin_rot_img.setDecimals(0); self.spin_rot_img.setValue(float(getattr(self._cfg.layout, "image_rotation_deg", 0.0) or getattr(self._cfg.layout, "rotation_deg", 0.0))); self.spin_rot_img.setFixedWidth(80)
		self.slider_rot_img.valueChanged.connect(lambda v: (self.spin_rot_img.setValue(v), self._on_rotation_image(int(v))))
		self.spin_rot_img.valueChanged.connect(lambda v: (self.slider_rot_img.setValue(int(v)), self._on_rotation_image(int(v))))
		row_rot_img.addWidget(self.slider_rot_img, 1); row_rot_img.addWidget(self.spin_rot_img)
		layout.addLayout(row_rot_img)

		line3 = QFrame(); line3.setFrameShape(QFrame.HLine); layout.addWidget(line3)

		# Drag target selector removed: now drag directly on canvas without selection



		# Position dropdowns (separate)
		row_pos_t = QHBoxLayout(); row_pos_t.setSpacing(4); row_pos_t.addWidget(QLabel("文本位置"))
		self.pos_combo_text = QComboBox(); self.pos_combo_text.addItems(["左上","中上","右上","左中","正中","右中","左下","中下","右下"]) ; self.pos_combo_text.currentIndexChanged.connect(self._on_pos_text)
		row_pos_t.addWidget(self.pos_combo_text)
		layout.addLayout(row_pos_t)

		row_pos_i = QHBoxLayout(); row_pos_i.setSpacing(4); row_pos_i.addWidget(QLabel("图片位置"))
		self.pos_combo_img = QComboBox(); self.pos_combo_img.addItems(["左上","中上","右上","左中","正中","右中","左下","中下","右下"]) ; self.pos_combo_img.currentIndexChanged.connect(self._on_pos_image)
		# 设置默认位置为正中
		self.pos_combo_text.setCurrentIndex(4)
		self.pos_combo_img.setCurrentIndex(4)
		row_pos_i.addWidget(self.pos_combo_img)
		layout.addLayout(row_pos_i)

		line4 = QFrame(); line4.setFrameShape(QFrame.HLine); layout.addWidget(line4)

		# Templates with apply buttons
		row_tpl_head = QHBoxLayout(); row_tpl_head.setSpacing(4)
		self.btn_save_tpl = AutoFitButton("保存模板"); self.btn_save_tpl.clicked.connect(self._save_template)
		self.btn_load_tpl = AutoFitButton("加载模板"); self.btn_load_tpl.clicked.connect(self._load_template)
		row_tpl_head.addWidget(self.btn_save_tpl); row_tpl_head.addWidget(self.btn_load_tpl)
		layout.addLayout(row_tpl_head)

		self.list_tpls = QListWidget(); self.list_tpls.itemDoubleClicked.connect(self._apply_selected_template)
		self.list_tpls.setContextMenuPolicy(Qt.CustomContextMenu)
		self.list_tpls.customContextMenuRequested.connect(self._on_tpl_context)
		# 增加模板列表高度，显示更多模板
		self.list_tpls.setMinimumHeight(300)
		layout.addWidget(self.list_tpls)

		row_tpl_apply = QHBoxLayout(); row_tpl_apply.setSpacing(4)
		btn_apply_sel = AutoFitButton("应用到所选"); btn_apply_sel.clicked.connect(self._apply_template_to_selected)
		btn_apply_all = AutoFitButton("应用到全部"); btn_apply_all.clicked.connect(self._apply_template_to_all)
		row_tpl_apply.addWidget(btn_apply_sel); row_tpl_apply.addWidget(btn_apply_all)
		layout.addLayout(row_tpl_apply)

		line = QFrame(); line.setFrameShape(QFrame.HLine); layout.addWidget(line)

		# 添加导出按钮
		btn_export = AutoFitButton("导出图片")
		btn_export.setMinimumHeight(36)
		btn_export.clicked.connect(self.exportClicked.emit)
		layout.addWidget(btn_export)

		self._reload_templates()
		layout.addStretch(1)

		scroll.setWidget(content)

		root = QVBoxLayout(self)
		root.setContentsMargins(0, 0, 0, 0)
		root.addWidget(scroll)

	def setConfig(self, cfg: WatermarkConfig) -> None:
		if not hasattr(self, "_ready") or not self._ready:
			return
		# guard widgets validity
		for w in [getattr(self, n, None) for n in ["txt_input","font_combo","chk_bold","chk_italic","slider_fs","slider_text_op","slider_scale","spin_scale","slider_logo_op","slider_rot_text","slider_rot_img","pos_combo_text","pos_combo_img","chk_text","chk_img","chk_shadow","chk_outline"]]:
			if w is None or not isValid(w):
				return
		self._cfg = cfg
		# 更新文本水印复选框状态
		self.chk_text.setChecked(cfg.layout.enabled_text)
		# 更新图片水印复选框状态
		self.chk_img.setChecked(cfg.layout.enabled_image)
		
		self.txt_input.setText(cfg.text.text)
		self.font_combo.setCurrentFont(QFont(cfg.text.family))
		self.chk_bold.setChecked(cfg.text.bold)
		self.chk_italic.setChecked(cfg.text.italic)
		self.chk_shadow.setChecked(cfg.text.shadow)
		self.chk_outline.setChecked(cfg.text.outline)
		self.slider_fs.setValue(getattr(cfg.text, "size_px", 16))
		self.spin_fs.setValue(getattr(cfg.text, "size_px", 16))
		self.slider_text_op.setValue(int(cfg.text.color[3]*100/255))
		self.spin_text_op.setValue(int(cfg.text.color[3]*100/255))
		# 同步颜色下拉默认值：黑色(1)或白(0)
		try:
			if tuple(cfg.text.color) == (0, 0, 0, 255):
				self.cmb_color.setCurrentIndex(1)
			elif tuple(cfg.text.color) == (255, 255, 255, 191):
				self.cmb_color.setCurrentIndex(0)
		except Exception:
			pass
		# 更新颜色预览
		self._update_color_preview()
		self.slider_scale.setValue(int(cfg.image.scale*100))
		self.spin_scale.setValue(cfg.image.scale*100)
		self.slider_logo_op.setValue(int(cfg.image.opacity*100))
		self.spin_logo_op.setValue(int(cfg.image.opacity*100))
		# Separate rotation sync with legacy fallback
		self.slider_rot_text.setValue(int(getattr(cfg.layout, "text_rotation_deg", 0.0) if getattr(cfg.layout, "text_rotation_deg", 0.0) != 0.0 else getattr(cfg.layout, "rotation_deg", 0.0)))
		self.spin_rot_text.setValue(float(getattr(cfg.layout, "text_rotation_deg", 0.0) if getattr(cfg.layout, "text_rotation_deg", 0.0) != 0.0 else getattr(cfg.layout, "rotation_deg", 0.0)))
		self.slider_rot_img.setValue(int(getattr(cfg.layout, "image_rotation_deg", 0.0) if getattr(cfg.layout, "image_rotation_deg", 0.0) != 0.0 else getattr(cfg.layout, "rotation_deg", 0.0)))
		self.spin_rot_img.setValue(float(getattr(cfg.layout, "image_rotation_deg", 0.0) if getattr(cfg.layout, "image_rotation_deg", 0.0) != 0.0 else getattr(cfg.layout, "rotation_deg", 0.0)))
		# 不再强制将位置映射到最近的九宫格点，允许自由拖拽到任意位置
		# 仅在位置确实匹配九宫格点时才更新下拉框，否则保持当前选择不变
		presets = [
			(0.1,0.1),(0.5,0.1),(0.9,0.1),
			(0.1,0.5),(0.5,0.5),(0.9,0.5),
			(0.1,0.9),(0.5,0.9),(0.9,0.9),
		]
		def find_exact_match(pos):
			try:
				pos_t = tuple(pos)
			except Exception:
				pos_t = (0.5, 0.5)
			# 只在位置与预设点完全匹配时才返回索引
			for i, (x, y) in enumerate(presets):
				if abs(x - pos_t[0]) < 0.01 and abs(y - pos_t[1]) < 0.01:
					return i
			# 否则不改变当前选择
			return -1
		
		# 仅在找到完全匹配的预设点时才更新下拉框
		text_idx = find_exact_match(cfg.layout.text_position or cfg.layout.position)
		if text_idx != -1:
			self.pos_combo_text.setCurrentIndex(text_idx)
		
		img_idx = find_exact_match(cfg.layout.image_position or cfg.layout.position)
		if img_idx != -1:
			self.pos_combo_img.setCurrentIndex(img_idx)
		# Do not emit here to avoid re-entrant updates during initialization

	def _emit(self) -> None:
		save_last_settings(self._cfg)
		self.configChanged.emit(self._cfg)

	# text controls
	def _set_enabled_text(self, enabled: bool) -> None:
		self._cfg.layout.enabled_text = enabled
		self._emit()

	def _on_text(self, s: str) -> None:
		self._cfg.text.text = s
		self._emit()

	def _on_font_family(self, f) -> None:
		family = f.family() or "Segoe UI"
		self._cfg.text.family = family
		self._emit()

	def _on_bold(self, s: int) -> None:
		self._cfg.text.bold = bool(s)
		self._emit()

	def _on_italic(self, s: int) -> None:
		self._cfg.text.italic = bool(s)
		self._emit()

	def _on_font_size(self, v: int) -> None:
		self._cfg.text.size_px = v
		self._emit()

	def _on_color(self, idx: int) -> None:
		# 如果选择的是自定义，触发颜色选择器
		if idx == 5:
			self._pick_color()
			# 选择颜色后不保持在自定义选项
			return
		
		mapping = {
			0: (255, 255, 255, 191),
			1: (0, 0, 0, 255),
			2: (220, 20, 60, 255),
			3: (34, 139, 34, 255),
			4: (30, 144, 255, 255),
		}
		self._cfg.text.color = mapping.get(idx, (255, 255, 255, 191))
		self._update_color_preview()
		self._emit()

	def _pick_color(self) -> None:
		initial = QColor(*self._cfg.text.color)
		color = QColorDialog.getColor(initial, self, "选择颜色", QColorDialog.ShowAlphaChannel)
		if color.isValid():
			self._cfg.text.color = (color.red(), color.green(), color.blue(), color.alpha())
			self.slider_text_op.setValue(int(color.alpha() * 100 / 255))
			self._update_color_preview()
			self._emit()
		
	def _update_color_preview(self) -> None:
		"""更新颜色预览框"""
		if hasattr(self, 'color_preview'):
			r, g, b, a = self._cfg.text.color
			self.color_preview.setStyleSheet(f"background-color: rgba({r}, {g}, {b}, {a});")

	def _on_text_opacity(self, v: int) -> None:
		r = list(self._cfg.text.color)
		r[3] = int(v * 255 / 100)
		self._cfg.text.color = tuple(r)  # type: ignore[assignment]
		self._emit()

	def _on_shadow(self, s: int) -> None:
		self._cfg.text.shadow = bool(s)
		self._emit()

	def _on_outline(self, s: int) -> None:
		self._cfg.text.outline = bool(s)
		self._emit()

	# image controls
	def _set_enabled_image(self, enabled: bool) -> None:
		self._cfg.layout.enabled_image = enabled
		# 当第一次勾选启用图片水印时，触发选择图片对话框
		if enabled and not self._cfg.image.path:
			self._pick_logo()
		self._emit()

	def _pick_logo(self) -> None:
		path, _ = QFileDialog.getOpenFileName(self, "选择水印图片", "", "Images (*.png *.jpg *.jpeg *.bmp *.tif *.tiff)")
		if path:
			self._cfg.image.path = path
			self._cfg.layout.enabled_image = True
			# Reflect in UI checkbox
			if hasattr(self, "chk_img") and isValid(self.chk_img):
				self.chk_img.setChecked(True)
			self._emit()

	def _on_logo_scale(self, v: int) -> None:
		self._cfg.image.scale = max(0.01, v / 100.0)
		self._emit()

	def _on_logo_opacity(self, v: int) -> None:
		self._cfg.image.opacity = max(0.0, min(1.0, v / 100.0))
		self._emit()

	# presets / rotation
	def _preset(self, idx: int) -> None:
		positions = [
			(0.1, 0.1),(0.5, 0.1),(0.9, 0.1),
			(0.1, 0.5),(0.5, 0.5),(0.9, 0.5),
			(0.1, 0.9),(0.5, 0.9),(0.9, 0.9),
		]
		self._cfg.layout.position = positions[idx]
		self._emit()

	def _on_rotation_text(self, v: int) -> None:
		self._cfg.layout.text_rotation_deg = float(v)
		self._emit()

	def _on_rotation_image(self, v: int) -> None:
		self._cfg.layout.image_rotation_deg = float(v)
		self._emit()

	# templates
	def _save_template(self) -> None:
		name, _ = QFileDialog.getSaveFileName(self, "保存模板为", "", "Template (*.json)")
		if not name:
			return
		if not name.lower().endswith(".json"):
			name = name + ".json"
		template_name = os.path.splitext(os.path.basename(name))[0]
		template_path = save_template(template_name, self._cfg)
		
		# 询问是否设为默认模板
		from PySide6.QtWidgets import QMessageBox
		result = QMessageBox.question(self, "设为默认模板", "是否将此模板设为默认模板？程序启动时将自动加载。")
		if result == QMessageBox.Yes:
			from app.core.templates import set_default_template
			set_default_template(template_path)
		
		self._reload_templates()
		
	def _load_template(self) -> None:
		from PySide6.QtWidgets import QFileDialog
		from app.core.templates import get_templates_dir
		path, _ = QFileDialog.getOpenFileName(self, "选择模板文件", get_templates_dir(), "Template (*.json)")
		if not path:
			return
		
		from app.core.templates import load_template
		cfg = load_template(path)
		if cfg:
			self._cfg = cfg
			self._emit()

	def _reload_templates(self) -> None:
		self.list_tpls.clear()
		# 获取默认模板路径
		from app.core.templates import get_default_template_path, load_template
		from dataclasses import asdict
		default_path = get_default_template_path()
		
		# 读取默认模板内容（如果存在），用于后续对比
		default_template_content = None
		if os.path.exists(default_path):
			default_template = load_template(default_path)
			if default_template:
				default_template_content = asdict(default_template)
		
		# 遍历所有模板
		for p in list_templates():
			# 获取文件名（不含扩展名）作为模板名称
			name = os.path.splitext(os.path.basename(p))[0]
			
			# 检查当前模板是否与默认模板内容相同
			if default_template_content:
				current_template = load_template(p)
				if current_template and asdict(current_template) == default_template_content:
					name = f"{name} (default)"
			
			# 创建列表项并存储完整路径
			item = QListWidgetItem(name)
			item.setData(Qt.UserRole, p)  # 存储完整路径在UserData中
			self.list_tpls.addItem(item)
		
	def _get_templates_dir(self) -> str:
		from app.core.templates import get_templates_dir
		return get_templates_dir()

	def _apply_selected_template(self, item) -> None:
		# 从UserData获取完整路径
		path = item.data(Qt.UserRole)
		cfg = load_template(path)
		if cfg:
			self._cfg = cfg
			self.setConfig(cfg)  # 调用setConfig方法更新所有UI控件
			self._emit()

	def _on_tpl_context(self, pos: QPoint) -> None:
		item = self.list_tpls.itemAt(pos)
		if not item:
			return
		menu = QMenu(self)
		a_apply = menu.addAction("应用模板")
		a_rename = menu.addAction("重命名")
		a_delete = menu.addAction("删除")
		a = menu.exec(self.list_tpls.mapToGlobal(pos))
		if not a:
			return
		# 从UserData获取完整路径
		path = item.data(Qt.UserRole)
		if a == a_apply:
			self._apply_selected_template(item)
		elif a == a_rename:
			new_name, ok = QInputDialog.getText(self, "重命名模板", "新名称：")
			if ok and new_name.strip():
				new_path = rename_template(path, new_name.strip())
				if new_path:
					self._reload_templates()
		elif a == a_delete:
			if delete_template(path):
				self._reload_templates()

	def _on_pos_text(self, idx: int) -> None:
		positions = [
			(0.1, 0.1),(0.5, 0.1),(0.9, 0.1),
			(0.1, 0.5),(0.5, 0.5),(0.9, 0.5),
			(0.1, 0.9),(0.5, 0.9),(0.9, 0.9),
		]
		self._cfg.layout.text_position = positions[idx]
		self._emit()

	def _on_pos_image(self, idx: int) -> None:
		positions = [
			(0.1, 0.1),(0.5, 0.1),(0.9, 0.1),
			(0.1, 0.5),(0.5, 0.5),(0.9, 0.5),
			(0.1, 0.9),(0.5, 0.9),(0.9, 0.9),
		]
		self._cfg.layout.image_position = positions[idx]
		self._emit()

	def _apply_template_to_selected(self) -> None:
		item = self.list_tpls.currentItem()
		if not item:
			return
		# 从UserData获取完整路径
		path = item.data(Qt.UserRole)
		self.applyTemplateToSelected.emit(path)

	def _apply_template_to_all(self) -> None:
		item = self.list_tpls.currentItem()
		if not item:
			return
		# 从UserData获取完整路径
		path = item.data(Qt.UserRole)
		self.applyTemplateToAll.emit(path)
