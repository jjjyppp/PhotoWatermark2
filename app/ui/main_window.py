from PySide6.QtWidgets import QMainWindow, QWidget, QHBoxLayout, QSplitter, QFileDialog, QMessageBox, QMenuBar, QDialog, QApplication
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QAction

import os
from copy import deepcopy

from .widgets.image_list import ImageListWidget
from .widgets.preview import PreviewWidget
from .widgets.controls_panel import ControlsPanel
from .export_dialog import ExportDialog
from app.core.templates import load_last_settings, load_template, save_session_state, load_session_state
from app.core.models import ExportOptions, WatermarkConfig
from app.core.watermark_engine import WatermarkEngine
from PySide6.QtGui import QImage
from app.ui.theme import LIGHT_QSS, DARK_QSS, BW_QSS


class MainWindow(QMainWindow):
	def __init__(self, load_session: bool = False) -> None:
		super().__init__()
		self.setWindowTitle("水印批量处理工具")
		self.resize(1440, 900)

		self.image_list = ImageListWidget(self)
		self.image_list.setMinimumWidth(200)
		self.preview = PreviewWidget(self)
		self.controls = ControlsPanel(self)
		# Fix controls panel width; allow collapse via splitter but not resizing width
		self.controls.setFixedWidth(460)
		self._engine = WatermarkEngine()

		self._per_image_cfg: dict[str, WatermarkConfig] = {}
		self._current_path: str | None = None
		self._dark = False

		splitter = QSplitter(Qt.Horizontal, self)
		splitter.addWidget(self.image_list)
		splitter.addWidget(self.preview)
		splitter.addWidget(self.controls)
		splitter.setStretchFactor(0, 0)
		splitter.setStretchFactor(1, 1)
		splitter.setStretchFactor(2, 0)
		# Allow the right controls panel to collapse/expand but keep a fixed width otherwise
		splitter.setCollapsible(2, True)
		splitter.setSizes([220, 760, 460])

		container = QWidget(self)
		layout = QHBoxLayout(container)
		layout.setContentsMargins(8, 8, 8, 8)
		layout.setSpacing(8)
		layout.addWidget(splitter)
		self.setCentralWidget(container)

		self._setup_menu()

		self.image_list.imageSelected.connect(self._on_image_selected)
		self.controls.requestOpenFiles.connect(self.image_list.openFiles)
		self.controls.requestOpenFolder.connect(self.image_list.openFolder)
		self.controls.configChanged.connect(self._on_controls_changed)
		self.controls.applyTemplateToSelected.connect(self._on_apply_template_to_selected)
		self.controls.applyTemplateToAll.connect(self._on_apply_template_to_all)
		self.preview.configChanged.connect(self._on_preview_changed)
		# dragTargetChanged no longer used; preview determines target by cursor

		# 根据参数决定是否加载保存的会话状态（图片列表和水印设置）
		if load_session:
			self._load_session_state()

	def _setup_menu(self) -> None:
		menu = self.menuBar() if self.menuBar() else QMenuBar(self)
		self.setMenuBar(menu)
		file_menu = menu.addMenu("文件")

		a_export = QAction("导出…", self)
		a_export.triggered.connect(self._export)
		file_menu.addAction(a_export)

		edit_menu = menu.addMenu("编辑")
		a_apply_sel = QAction("将当前设置应用到所选", self)
		a_apply_sel.triggered.connect(self._apply_to_selected)
		a_apply_all = QAction("将当前设置应用到全部", self)
		a_apply_all.triggered.connect(self._apply_to_all)
		edit_menu.addAction(a_apply_sel)
		edit_menu.addAction(a_apply_all)

		view_menu = menu.addMenu("视图")
		a_light = QAction("浅色主题", self); a_light.triggered.connect(lambda: self._set_theme("light"))
		a_dark = QAction("深色主题", self); a_dark.triggered.connect(lambda: self._set_theme("dark"))
		a_bw = QAction("黑白主题", self); a_bw.triggered.connect(lambda: self._set_theme("bw"))
		view_menu.addAction(a_light); view_menu.addAction(a_dark); view_menu.addAction(a_bw)

	def _set_theme(self, which: str) -> None:
		app = QApplication.instance()
		if not app:
			return
		if which == "dark":
			app.setStyleSheet(DARK_QSS)
			self._dark = True
		elif which == "light":
			app.setStyleSheet(LIGHT_QSS)
			self._dark = False
		else:
			app.setStyleSheet(BW_QSS)

	def _on_image_selected(self, path: str) -> None:
		self._current_path = path
		self.preview.onImageSelected(path)
		cfg = self._per_image_cfg.get(path)
		if cfg is None:
			# 创建全新的默认配置，而不是基于当前控件配置的副本
			cfg = WatermarkConfig()
			self._per_image_cfg[path] = cfg
		self.controls.setConfig(cfg)
		self.preview.updateConfig(cfg)

	def _on_apply_template_to_selected(self, template_path: str) -> None:
		cfg = load_template(template_path)
		if not cfg:
			return
		for p in self.image_list.get_selected_paths():
			self._per_image_cfg[p] = deepcopy(cfg)
		if self._current_path and self._current_path in self._per_image_cfg:
			self.controls.setConfig(deepcopy(self._per_image_cfg[self._current_path]))
			self.preview.updateConfig(self._per_image_cfg[self._current_path])

	def _on_apply_template_to_all(self, template_path: str) -> None:
		cfg = load_template(template_path)
		if not cfg:
			return
		for p in self.image_list.get_all_paths():
			self._per_image_cfg[p] = deepcopy(cfg)
		if self._current_path and self._current_path in self._per_image_cfg:
			self.controls.setConfig(deepcopy(self._per_image_cfg[self._current_path]))
			self.preview.updateConfig(self._per_image_cfg[self._current_path])

	def _on_controls_changed(self, cfg: WatermarkConfig) -> None:
		if self._current_path:
			self._per_image_cfg[self._current_path] = deepcopy(cfg)
			self.preview.updateConfig(cfg)

	def _on_preview_changed(self, cfg: WatermarkConfig) -> None:
		# Sync preview-side changes (drag/rotate) back into current per-image config and controls
		if self._current_path:
			self._per_image_cfg[self._current_path] = deepcopy(cfg)
			# Update controls without emitting
			self.controls.setConfig(deepcopy(cfg))

	def _apply_to_selected(self) -> None:
		paths = self.image_list.get_selected_paths()
		if not paths:
			QMessageBox.information(self, "应用设置", "请先在列表中多选图片。")
			return
		base = deepcopy(self.controls._cfg)
		for p in paths:
			self._per_image_cfg[p] = deepcopy(base)
		QMessageBox.information(self, "应用设置", f"已将当前设置应用到 {len(paths)} 张选中图片。")

	def _apply_to_all(self) -> None:
		paths = self.image_list.get_all_paths()
		if not paths:
			return
		base = deepcopy(self.controls._cfg)
		for p in paths:
			self._per_image_cfg[p] = deepcopy(base)
		QMessageBox.information(self, "应用设置", f"已将当前设置应用到全部 {len(paths)} 张图片。")

	def _export(self) -> None:
		paths = self.image_list.get_all_paths()
		if not paths:
			QMessageBox.warning(self, "导出", "请先导入图片。")
			return

		dlg = ExportDialog(self)
		if dlg.exec() != QDialog.Accepted:
			return
		opts = dlg.options()

		if not opts.output_dir or not os.path.isdir(opts.output_dir):
			QMessageBox.warning(self, "导出", "请选择有效的输出目录。")
			return

		first_dir = os.path.dirname(paths[0])
		if os.path.abspath(first_dir) == os.path.abspath(opts.output_dir):
			QMessageBox.warning(self, "导出", "为避免覆盖，禁止导出到原图目录，请选择其他目录。")
			return

		saved = 0
		overwrite_all = False
		skip_all = False
		for src_path in paths:
			img = QImage(src_path)
			if img.isNull():
				continue
			img = self._apply_scale(img, opts)
			cfg = self._per_image_cfg.get(src_path) or deepcopy(self.controls._cfg)
			composited = self._engine.render(img, cfg)

			name, ext = os.path.splitext(os.path.basename(src_path))
			if opts.name_rule == "original":
				out_name = name
			elif opts.name_rule == "prefix":
				out_name = f"{opts.name_affix}{name}"
			else:
				out_name = f"{name}{opts.name_affix}"
			fmt = opts.format.upper()
			out_ext = ".jpg" if fmt == "JPEG" else ".png"
			out_path = os.path.join(opts.output_dir, out_name + out_ext)

			if os.path.exists(out_path) and not overwrite_all and not skip_all:
				res = QMessageBox.question(
					self,
					"文件已存在",
					f"文件已存在：\n{out_path}\n选择操作：",
					QMessageBox.Yes | QMessageBox.No | QMessageBox.YesToAll | QMessageBox.NoToAll | QMessageBox.Cancel,
					QMessageBox.No
				)
				if res == QMessageBox.Cancel:
					break
				elif res == QMessageBox.No:
					continue
				elif res == QMessageBox.NoToAll:
					skip_all = True
					continue
				elif res == QMessageBox.YesToAll:
					overwrite_all = True
			# QMessageBox.Yes -> overwrite this one

			if fmt == "JPEG":
				composited = composited.convertToFormat(QImage.Format_RGB888)
				composited.save(out_path, "JPEG", opts.jpeg_quality)
			else:
				composited.save(out_path, "PNG")
			saved += 1

		QMessageBox.information(self, "导出完成", f"成功导出 {saved} 张图片到:\n{opts.output_dir}")

	def _apply_scale(self, img: QImage, opts: ExportOptions) -> QImage:
		if opts.scale_mode == "none":
			return img
		w = img.width(); h = img.height()
		if opts.scale_mode == "percent":
			s = max(1, int(min(10000, opts.scale_value))) / 100.0
			return img.scaled(int(w * s), int(h * s), Qt.KeepAspectRatio, Qt.SmoothTransformation)
		elif opts.scale_mode == "width":
			return img.scaled(int(opts.scale_value), int(h * (opts.scale_value / w)), Qt.KeepAspectRatio, Qt.SmoothTransformation)
		elif opts.scale_mode == "height":
			return img.scaled(int(w * (opts.scale_value / h)), int(opts.scale_value), Qt.KeepAspectRatio, Qt.SmoothTransformation)
		elif opts.scale_mode == "both":
			return img.scaled(int(opts.scale_value), int(opts.scale_height), Qt.IgnoreAspectRatio, Qt.SmoothTransformation)
		return img

	def closeEvent(self, event) -> None:
		"""程序关闭时保存会话状态"""
		# 保存图片列表和水印设置
		image_paths = self.image_list.get_all_paths()
		save_session_state(image_paths, self._per_image_cfg)
		super().closeEvent(event)

	def _load_session_state(self) -> None:
		"""加载会话状态（图片列表和水印设置）"""
		session_data = load_session_state()
		if not session_data:
			return

		# 加载图片列表
		image_paths = session_data.get("image_paths", [])
		if image_paths:
			for path in image_paths:
				if os.path.exists(path):
					self.image_list.add_image(path)

		# 加载每个图片的水印设置
		per_image_configs = session_data.get("per_image_configs", {})
		for path, config_data in per_image_configs.items():
			if os.path.exists(path) and path in self.image_list.get_all_paths():
				try:
					# 转换字典为 WatermarkConfig 对象
					from app.core.templates import _from_dict
					config = _from_dict(config_data)
					self._per_image_cfg[path] = config
				except Exception:
					continue

		# 如果有图片，自动选择第一张
		if self.image_list.get_all_paths():
			first_path = self.image_list.get_all_paths()[0]
			self.image_list.list.setCurrentRow(0)
