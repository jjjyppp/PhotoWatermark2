from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QFileDialog, QComboBox, QSlider, QSpinBox, QCheckBox
from PySide6.QtCore import Qt

from app.core.models import ExportOptions


class ExportDialog(QDialog):
	def __init__(self, parent=None) -> None:
		super().__init__(parent)
		self.setWindowTitle("导出设置")
		self._opts = ExportOptions()
		self._opts.name_affix = "_watermarked"

		layout = QVBoxLayout(self)

		# Output folder
		row_dir = QHBoxLayout()
		row_dir.addWidget(QLabel("输出目录"))
		self.edit_dir = QLineEdit()
		btn_dir = QPushButton("选择…"); btn_dir.clicked.connect(self._pick_dir)
		row_dir.addWidget(self.edit_dir); row_dir.addWidget(btn_dir)
		layout.addLayout(row_dir)

		# Format
		row_fmt = QHBoxLayout()
		row_fmt.addWidget(QLabel("格式"))
		self.cmb_fmt = QComboBox(); self.cmb_fmt.addItems(["PNG", "JPEG"]) ; self.cmb_fmt.currentTextChanged.connect(self._on_format)
		row_fmt.addWidget(self.cmb_fmt)
		layout.addLayout(row_fmt)

		# JPEG quality (label + slider in one row, hide both when PNG)
		row_q = QHBoxLayout()
		self.lbl_q = QLabel("JPEG质量")
		row_q.addWidget(self.lbl_q)
		self.slider_q = QSlider(Qt.Horizontal); self.slider_q.setRange(0, 100); self.slider_q.setValue(self._opts.jpeg_quality)
		row_q.addWidget(self.slider_q, 1)
		layout.addLayout(row_q)

		# Resize: give three inputs, user填其一优先（宽高同时、否则按百分比）
		row_wh = QHBoxLayout(); row_wh.addWidget(QLabel("导出尺寸"))
		self.spin_w = QSpinBox(); self.spin_w.setRange(1, 20000); self.spin_w.setPrefix("W:")
		self.spin_h = QSpinBox(); self.spin_h.setRange(1, 20000); self.spin_h.setPrefix(" H:")
		self.spin_percent = QSpinBox(); self.spin_percent.setRange(1, 10000); self.spin_percent.setSuffix(" %")
		row_wh.addWidget(self.spin_w); row_wh.addWidget(self.spin_h); row_wh.addWidget(self.spin_percent)
		layout.addLayout(row_wh)

		# Naming
		row_name = QHBoxLayout(); row_name.addWidget(QLabel("命名规则"))
		self.cmb_rule = QComboBox(); self.cmb_rule.addItems(["original","prefix","suffix"]) ; self.cmb_rule.currentTextChanged.connect(self._on_rule)
		self.edit_affix = QLineEdit("wm_")
		row_name.addWidget(self.cmb_rule); row_name.addWidget(self.edit_affix)
		layout.addLayout(row_name)

		row_btns = QHBoxLayout()
		ok = QPushButton("开始导出"); ok.clicked.connect(self.accept)
		cancel = QPushButton("取消"); cancel.clicked.connect(self.reject)
		row_btns.addStretch(1); row_btns.addWidget(ok); row_btns.addWidget(cancel)
		layout.addLayout(row_btns)

		self._on_format(self.cmb_fmt.currentText())
		self._on_rule(self.cmb_rule.currentText())

	def _pick_dir(self) -> None:
		d = QFileDialog.getExistingDirectory(self, "选择输出目录")
		if d:
			self.edit_dir.setText(d)

	def _on_format(self, t: str) -> None:
		is_jpeg = t.upper() == "JPEG"
		self.lbl_q.setVisible(is_jpeg)
		self.slider_q.setVisible(is_jpeg)

	def _on_rule(self, t: str) -> None:
		if t == "original":
			self.edit_affix.setVisible(False)
		elif t == "prefix":
			self.edit_affix.setVisible(True)
			if not self.edit_affix.text().strip():
				self.edit_affix.setText("wm_")
		else:
			self.edit_affix.setVisible(True)
			if not self.edit_affix.text().strip():
				self.edit_affix.setText("_watermarked")

	def options(self) -> ExportOptions:
		opts = ExportOptions()
		opts.output_dir = self.edit_dir.text().strip()
		opts.format = self.cmb_fmt.currentText().upper()
		opts.jpeg_quality = int(self.slider_q.value())
		w = int(self.spin_w.value() or 0)
		h = int(self.spin_h.value() or 0)
		p = int(self.spin_percent.value() or 0)
		if w > 0 and h > 0:
			opts.scale_mode = "both"; opts.scale_value = float(w); opts.scale_height = float(h)
		elif p > 0:
			opts.scale_mode = "percent"; opts.scale_value = float(p)
		elif w > 0:
			opts.scale_mode = "width"; opts.scale_value = float(w)
		elif h > 0:
			opts.scale_mode = "height"; opts.scale_value = float(h)
		else:
			opts.scale_mode = "none"; opts.scale_value = 1.0
		opts.name_rule = self.cmb_rule.currentText()
		if opts.name_rule == "original":
			opts.name_affix = ""
		elif opts.name_rule == "prefix":
			opts.name_affix = self.edit_affix.text().strip() or "wm_"
		else:
			opts.name_affix = self.edit_affix.text().strip() or "_watermarked"
		return opts

