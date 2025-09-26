from PySide6.QtWidgets import QWidget
from PySide6.QtGui import QPainter, QImage, QMouseEvent, QWheelEvent, QColor
from PySide6.QtCore import Qt, QRect, QSize, QPoint

from app.core.models import WatermarkConfig
from app.core.watermark_engine import WatermarkEngine


class PreviewWidget(QWidget):
	def __init__(self, parent=None) -> None:
		super().__init__(parent)
		self._image = QImage()
		self._engine = WatermarkEngine()
		self._cfg = WatermarkConfig()
		self._dragging = False
		self._last_mouse = QPoint()
		self._display_rect = QRect()
		self._drag_target = "text"  # or "image"

	def setDragTarget(self, target: str) -> None:
		self._drag_target = target if target in ("text","image") else "text"

	def minimumSizeHint(self) -> QSize:  # type: ignore[override]
		return QSize(500, 360)

	def onImageSelected(self, path: str) -> None:
		img = QImage(path)
		if not img.isNull():
			self._image = img
			self.update()

	def updateConfig(self, cfg: WatermarkConfig) -> None:
		self._cfg = cfg
		self.update()

	def paintEvent(self, event) -> None:  # type: ignore[override]
		p = QPainter(self)
		p.fillRect(self.rect(), QColor(255, 255, 255))
		if self._image.isNull():
			p.end()
			return
		src = self._engine.render(self._image, self._cfg)
		target = self.rect()
		scaled = src.scaled(target.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
		x = target.center().x() - scaled.width() // 2
		y = target.center().y() - scaled.height() // 2
		self._display_rect = QRect(x, y, scaled.width(), scaled.height())
		p.drawImage(self._display_rect, scaled)
		p.end()

	def mousePressEvent(self, e: QMouseEvent) -> None:  # type: ignore[override]
		if e.button() == Qt.LeftButton:
			self._dragging = True
			self._last_mouse = e.pos()

	def mouseMoveEvent(self, e: QMouseEvent) -> None:  # type: ignore[override]
		if not self._dragging or self._image.isNull():
			return
		delta = e.pos() - self._last_mouse
		self._last_mouse = e.pos()
		if self._display_rect.width() > 0 and self._display_rect.height() > 0:
			nx = delta.x() / float(self._display_rect.width())
			ny = delta.y() / float(self._display_rect.height())
			px, py = self._cfg.layout.text_position if self._drag_target == "text" else self._cfg.layout.image_position
			px = min(max(px + nx, 0.0), 1.0)
			py = min(max(py + ny, 0.0), 1.0)
			if self._drag_target == "text":
				self._cfg.layout.text_position = (px, py)
			else:
				self._cfg.layout.image_position = (px, py)
			self.update()

	def mouseReleaseEvent(self, e: QMouseEvent) -> None:  # type: ignore[override]
		if e.button() == Qt.LeftButton:
			self._dragging = False

	def wheelEvent(self, e: QWheelEvent) -> None:  # type: ignore[override]
		if e.modifiers() & Qt.ControlModifier:
			angle_delta = e.angleDelta().y() / 8.0
			self._cfg.layout.rotation_deg = (self._cfg.layout.rotation_deg + angle_delta) % 360
			self.update()
