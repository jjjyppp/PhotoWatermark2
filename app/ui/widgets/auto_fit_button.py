from PySide6.QtWidgets import QPushButton
from PySide6.QtGui import QFontMetrics, QResizeEvent, QFont


class AutoFitButton(QPushButton):
	def __init__(self, text: str = "", parent=None) -> None:
		super().__init__(text, parent)
		self._base_point_size = self.font().pointSize() if self.font().pointSize() > 0 else 12
		self._min_point_size = 9

	def resizeEvent(self, event: QResizeEvent) -> None:  # type: ignore[override]
		super().resizeEvent(event)
		self._adjust_font()

	def setText(self, text: str) -> None:  # type: ignore[override]
		super().setText(text)
		self._adjust_font()

	def _adjust_font(self) -> None:
		if not self.text():
			return
		w = max(0, self.width() - 16)
		if w <= 0:
			return
		font = QFont(self.font())
		ps = max(self._min_point_size, self._base_point_size)
		fm = QFontMetrics(font)
		if fm.horizontalAdvance(self.text()) <= w:
			return
		# decrease until fits or at minimum
		while ps > self._min_point_size:
			ps -= 1
			font.setPointSize(ps)
			fm = QFontMetrics(font)
			if fm.horizontalAdvance(self.text()) <= w:
				break
		self.setFont(font)


