from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QFileDialog, QComboBox, QSlider, QSpinBox, QCheckBox
from PySide6.QtCore import Qt
from PySide6.QtGui import QIntValidator

from app.core.models import ExportOptions


class ExportDialog(QDialog):
	def __init__(self, parent=None, original_file_paths=None) -> None:
		super().__init__(parent)
		self.setWindowTitle("导出设置")
		self.resize(384, 400)  # 再次调整对话框宽度为当前的80%
		self._opts = ExportOptions()
		self._opts.name_affix = "_watermarked"
		self._original_dirs = set()
		if original_file_paths:
			import os
			for path in original_file_paths:
				if path:
					self._original_dirs.add(os.path.dirname(os.path.abspath(path)))

		layout = QVBoxLayout(self)

		# Output folder
		row_dir = QHBoxLayout()
		row_dir.addWidget(QLabel("输出目录"))
		self.edit_dir = QLineEdit()
		btn_dir = QPushButton("选择"); btn_dir.clicked.connect(self._pick_dir)
		row_dir.addWidget(self.edit_dir); row_dir.addWidget(btn_dir)
		layout.addLayout(row_dir)

		# Format
		row_fmt = QHBoxLayout()
		row_fmt.addWidget(QLabel("格式"))
		self.cmb_fmt = QComboBox(); self.cmb_fmt.addItems(["PNG", "JPEG"]) ; self.cmb_fmt.currentTextChanged.connect(self._on_format)
		row_fmt.addWidget(self.cmb_fmt)
		layout.addLayout(row_fmt)

		# JPEG quality (label + slider + value display in one row, hide when PNG)
		row_q = QHBoxLayout()
		self.lbl_q = QLabel("JPEG质量")
		row_q.addWidget(self.lbl_q)
		self.slider_q = QSlider(Qt.Horizontal); self.slider_q.setRange(0, 100); self.slider_q.setValue(self._opts.jpeg_quality)
		self.slider_q.valueChanged.connect(self._on_quality_change)
		row_q.addWidget(self.slider_q, 1)
		self.lbl_q_value = QLabel(f"{self._opts.jpeg_quality}%")
		row_q.addWidget(self.lbl_q_value)
		layout.addLayout(row_q)

		# 缩放设置
		scale_group_layout = QVBoxLayout()
		scale_group_layout.addWidget(QLabel("缩放"))
		
		# 高度和宽度输入
		scale_input_layout = QHBoxLayout()
		scale_input_layout.addWidget(QLabel("高度:"))
		self.spin_h = QSpinBox(); self.spin_h.setRange(1, 1000); self.spin_h.setSuffix(" %"); self.spin_h.setValue(100); self.spin_h.setMinimumWidth(120)
		self.spin_h.valueChanged.connect(self._on_scale_change)
		scale_input_layout.addWidget(self.spin_h)
		scale_input_layout.addStretch(1)
		
		scale_input_layout.addWidget(QLabel("宽度:"))
		self.spin_w = QSpinBox(); self.spin_w.setRange(1, 1000); self.spin_w.setSuffix(" %"); self.spin_w.setValue(100); self.spin_w.setMinimumWidth(120)
		self.spin_w.valueChanged.connect(self._on_scale_change)
		scale_input_layout.addWidget(self.spin_w)
		
		scale_group_layout.addLayout(scale_input_layout)
		
		# 锁定纵横比复选框
		lock_aspect_layout = QHBoxLayout()
		self.chk_lock_aspect = QCheckBox("锁定纵横比")
		self.chk_lock_aspect.setChecked(True)
		self.chk_lock_aspect.stateChanged.connect(self._on_lock_aspect_changed)
		lock_aspect_layout.addWidget(self.chk_lock_aspect)
		lock_aspect_layout.addStretch(1)
		scale_group_layout.addLayout(lock_aspect_layout)
		
		layout.addLayout(scale_group_layout)

		# Naming
		row_name = QHBoxLayout(); row_name.addWidget(QLabel("命名规则"))
		self.cmb_rule = QComboBox(); 
		self.cmb_rule.addItems(["保留原文件名","添加自定义前缀","添加自定义后缀"]) 
		self.cmb_rule.setItemData(0, "original")
		self.cmb_rule.setItemData(1, "prefix")
		self.cmb_rule.setItemData(2, "suffix")
		self.cmb_rule.currentIndexChanged.connect(self._on_rule_index_changed)
		self.edit_affix = QLineEdit("wm_")
		row_name.addWidget(self.cmb_rule); row_name.addWidget(self.edit_affix)
		layout.addLayout(row_name)

		# Warning about output directory
		self.warn_label = QLabel("")
		self.warn_label.setStyleSheet("color: #FF6B6B")
		layout.addWidget(self.warn_label)

		row_btns = QHBoxLayout()
		ok = QPushButton("开始导出"); ok.clicked.connect(self.accept)
		cancel = QPushButton("取消"); cancel.clicked.connect(self.reject)
		row_btns.addStretch(1); row_btns.addWidget(ok); row_btns.addWidget(cancel)
		layout.addLayout(row_btns)

		self._on_format(self.cmb_fmt.currentText())
		self._on_rule_index_changed(0)  # 默认使用"保留原文件名"，不显示文本框

	def _pick_dir(self) -> None:
		d = QFileDialog.getExistingDirectory(self, "选择输出目录")
		if d:
			self.edit_dir.setText(d)
			self._check_output_dir(d)

	def _on_format(self, t: str) -> None:
		is_jpeg = t.upper() == "JPEG"
		self.lbl_q.setVisible(is_jpeg)
		self.slider_q.setVisible(is_jpeg)
		self.lbl_q_value.setVisible(is_jpeg)

	def _on_quality_change(self, value: int) -> None:
		self.lbl_q_value.setText(f"{value}%")
	
	def _on_scale_change(self, value: int) -> None:
		# 如果锁定了纵横比，同步更新另一个维度
		if self.chk_lock_aspect.isChecked():
			sender = self.sender()
			# 先阻塞两个控件的信号传递
			self.spin_h.blockSignals(True)
			self.spin_w.blockSignals(True)
			# 确保两个值一致
			if sender == self.spin_w:
				self.spin_h.setValue(value)
			else:
				self.spin_w.setValue(value)
			# 恢复信号传递
			self.spin_h.blockSignals(False)
			self.spin_w.blockSignals(False)
	
	def _sync_scale_values(self) -> None:
		"""同步高度和宽度的值，确保它们一致"""
		# 先阻塞两个控件的信号传递，避免触发不必要的回调
		self.spin_w.blockSignals(True)
		self.spin_h.blockSignals(True)
		# 以高度值为基准
		current_h = self.spin_h.value()
		# 确保两个值一致
		self.spin_w.setValue(current_h)
		self.spin_h.setValue(current_h)
		# 恢复信号传递
		self.spin_w.blockSignals(False)
		self.spin_h.blockSignals(False)
	
	def _on_lock_aspect_changed(self, state: int) -> None:
		# 当锁定状态改变时
		if state == Qt.Checked:
			# 同步宽高值
			self._sync_scale_values()

	def _on_rule_index_changed(self, index: int) -> None:
		# 获取当前选择的命名规则
		rule = self.cmb_rule.itemData(index)
		
		# 如果选择的是保留原文件名，则隐藏文本框
		if rule == "original":
			self.edit_affix.setVisible(False)
		# 如果选择的是添加自定义前缀，则显示文本框并设置默认值
		elif rule == "prefix":
			self.edit_affix.setVisible(True)
			# 选择前缀时，默认显示'wm_'
			self.edit_affix.setText("wm_")
		# 如果选择的是添加自定义后缀，则显示文本框并设置默认值
		else:
			self.edit_affix.setVisible(True)
			# 选择后缀时，默认显示'_watermarked'
			self.edit_affix.setText("_watermarked")

	def _check_output_dir(self, output_dir: str) -> None:
		import os
		output_dir_abs = os.path.abspath(output_dir)
		for orig_dir in self._original_dirs:
			if os.path.samefile(output_dir_abs, orig_dir):
				self.warn_label.setText("警告：不建议导出到原始文件所在目录，可能会覆盖原图！")
				return
		self.warn_label.setText("")

	def accept(self) -> None:
		# 检查输出目录是否为原文件夹
		output_dir = self.edit_dir.text().strip()
		if output_dir:
			self._check_output_dir(output_dir)
			import os
			output_dir_abs = os.path.abspath(output_dir)
			for orig_dir in self._original_dirs:
				if os.path.samefile(output_dir_abs, orig_dir):
					from PySide6.QtWidgets import QMessageBox
					reply = QMessageBox.warning(
						self, "警告", 
						"您正在导出到原始文件所在目录，这可能会覆盖原图。\n\n是否继续？",
						QMessageBox.Yes | QMessageBox.No
					)
					if reply == QMessageBox.No:
						return
		super().accept()

	def options(self) -> ExportOptions:
		opts = ExportOptions()
		opts.output_dir = self.edit_dir.text().strip()
		opts.format = self.cmb_fmt.currentText().upper()
		opts.jpeg_quality = int(self.slider_q.value())
		# 使用百分比进行缩放
		w_percent = int(self.spin_w.value())
		h_percent = int(self.spin_h.value())
		if self.chk_lock_aspect.isChecked():
			# 锁定纵横比时，使用相同的值
			opts.scale_mode = "percent"
			opts.scale_value = float(w_percent)
		else:
			# 不锁定纵横比时，分别设置宽高百分比
			opts.scale_mode = "both"
			opts.scale_value = float(w_percent)
			opts.scale_height = float(h_percent)
		# 获取命名规则的数据值而不是显示文本
		index = self.cmb_rule.currentIndex()
		opts.name_rule = self.cmb_rule.itemData(index)
		if opts.name_rule == "original":
			opts.name_affix = ""
		elif opts.name_rule == "prefix":
			opts.name_affix = self.edit_affix.text().strip() or "wm_"
		else:
			opts.name_affix = self.edit_affix.text().strip() or "_watermarked"
		return opts

