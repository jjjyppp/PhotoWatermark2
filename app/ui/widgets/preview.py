from PySide6.QtWidgets import QWidget, QApplication
from PySide6.QtGui import QPainter, QImage, QMouseEvent, QWheelEvent, QColor, QPen
from PySide6.QtCore import Qt, QRect, QSize, QPoint, Signal

from app.core.models import WatermarkConfig
from app.core.watermark_engine import WatermarkEngine


class PreviewWidget(QWidget):
	configChanged = Signal(WatermarkConfig)
	def __init__(self, parent=None) -> None:
		super().__init__(parent)
		self._image = QImage()
		self._engine = WatermarkEngine()
		self._cfg = WatermarkConfig()
		self._dragging = False
		self._resizing = False
		self._resize_handle: str | None = None  # 'n','s','e','w','nw','ne','se','sw'
		self._last_mouse = QPoint()
		self._display_rect = QRect()
		self._drag_target = "text"  # or "image"
		self._image_bbox = QRect()  # image watermark bbox on display
		self._image_selected = False  # show handles only when selected

	def setDragTarget(self, target: str) -> None:
		# Deprecated: target is chosen automatically based on cursor position
		self._drag_target = target if target in ("text","image") else "text"

	def _pick_target_by_cursor(self, pos: QPoint) -> str | None:
		# Determine which watermark (text/image) is closer to the cursor within the display rect
		if self._display_rect.width() <= 0 or self._display_rect.height() <= 0:
			return None
		if self._cfg is None:
			return None
		# Convert cursor to normalized [0,1] within display rect
		nx = (pos.x() - self._display_rect.left()) / float(self._display_rect.width())
		ny = (pos.y() - self._display_rect.top()) / float(self._display_rect.height())
		# Clamp
		nx = max(0.0, min(1.0, nx)); ny = max(0.0, min(1.0, ny))
		tx, ty = self._cfg.layout.text_position
		ix, iy = self._cfg.layout.image_position
		# If a watermark type is disabled, prefer the enabled one
		text_enabled = bool(self._cfg.layout.enabled_text)
		image_enabled = bool(self._cfg.layout.enabled_image)
		# Add distance threshold (0.15 is a reasonable threshold - 15% of display size)
		import math
		threshold = 0.15
		
		# Check if text is enabled and cursor is within threshold
		text_in_range = False
		if text_enabled:
			d_text = math.hypot(nx - tx, ny - ty)
			text_in_range = d_text <= threshold
		
		# Check if image is enabled and cursor is within threshold
		image_in_range = False
		if image_enabled:
			d_img = math.hypot(nx - ix, ny - iy)
			image_in_range = d_img <= threshold
		
		# If both are enabled and in range, pick the closer one
		if text_in_range and image_in_range:
			d_text = math.hypot(nx - tx, ny - ty)
			d_img = math.hypot(nx - ix, ny - iy)
			return "text" if d_text <= d_img else "image"
		# If only text is in range
		elif text_in_range:
			return "text"
		# If only image is in range
		elif image_in_range:
			return "image"
		# If neither is in range, return None
		else:
			return None

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

		# Overlay resize handles for image watermark (only when selected)
		self._image_bbox = QRect()
		if self._cfg.layout.enabled_image and (self._cfg.image.path or ""):
			bbox = self._calc_image_bbox_on_display()
			self._image_bbox = bbox
			if self._image_selected and bbox.width() > 4 and bbox.height() > 4:
				p.save()
				pen = QPen(QColor(14, 165, 233))  # cyan
				pen.setWidth(2)
				p.setPen(pen)
				p.setBrush(Qt.NoBrush)
				p.drawRect(bbox)
				# Draw corner and edge handles
				for cx, cy in self._handle_points(bbox):
					p.fillRect(cx - 4, cy - 4, 8, 8, QColor(14, 165, 233))
				p.restore()
		p.end()

	def _display_scale(self) -> float:
		# ratio from base image to displayed image
		if self._image.isNull() or self._display_rect.width() == 0 or self._display_rect.height() == 0:
			return 1.0
		return min(self._display_rect.width() / float(self._image.width()), self._display_rect.height() / float(self._image.height()))

	def _calc_image_bbox_on_display(self) -> QRect:
		from PySide6.QtGui import QImage as _QImg
		path = self._cfg.image.path or ""
		img = _QImg(path)
		if img.isNull():
			return QRect()
		# Size on base image
		shorter = min(self._image.width(), self._image.height())
		base_w = max(1, int(shorter * self._cfg.image.scale))
		sx = max(0.01, float(getattr(self._cfg.image, "scale_x", 1.0)))
		sy = max(0.01, float(getattr(self._cfg.image, "scale_y", 1.0)))
		w_base = max(1, int(base_w * sx))
		h_base = max(1, int(img.height() * (w_base / float(img.width())) * sy))
		# Map to display
		s = self._display_scale()
		w_disp = int(w_base * s)
		h_disp = int(h_base * s)
		# Centered at image position
		cx = self._display_rect.left() + int(self._cfg.layout.image_position[0] * self._display_rect.width())
		cy = self._display_rect.top() + int(self._cfg.layout.image_position[1] * self._display_rect.height())
		return QRect(cx - w_disp // 2, cy - h_disp // 2, w_disp, h_disp)

	def _handle_points(self, r: QRect) -> list[tuple[int,int]]:
		# corners and mids: nw, ne, se, sw, n, e, s, w
		cx = r.center().x(); cy = r.center().y()
		return [
			(r.left(), r.top()), (r.right(), r.top()), (r.right(), r.bottom()), (r.left(), r.bottom()),
			(cx, r.top()), (r.right(), cy), (cx, r.bottom()), (r.left(), cy)
		]

	def _hit_handle(self, pos: QPoint) -> str | None:
		if self._image_bbox.isNull():
			return None
		points = self._handle_points(self._image_bbox)
		names = ["nw","ne","se","sw","n","e","s","w"]
		for (x, y), name in zip(points, names):
			if abs(pos.x() - x) <= 6 and abs(pos.y() - y) <= 6:
				return name
		return None

	def mousePressEvent(self, e: QMouseEvent) -> None:  # type: ignore[override]
		if e.button() == Qt.LeftButton:
			self._last_mouse = e.pos()
		# Prefer resizing if on a handle of image; clicking image selects it
			if self._cfg.layout.enabled_image:
				# Update bbox to test selection/hit
				self._image_bbox = self._calc_image_bbox_on_display()
				h = self._hit_handle(e.pos())
				if h:
					self._resizing = True
					self._resize_handle = h
					self._image_selected = True
					return
				# Click inside image bbox selects it
				if not self._image_bbox.isNull() and self._image_bbox.contains(e.pos()):
					self._image_selected = True
				else:
					# If clicked elsewhere and current target is not image, deselect
					self._image_selected = False
			# Auto-pick drag target based on cursor; selection is controlled only by direct clicks (handles/bbox)
		target = self._pick_target_by_cursor(e.pos())
		if target:
			self._dragging = True
			self._drag_target = target
		else:
			self._dragging = False

	def mouseMoveEvent(self, e: QMouseEvent) -> None:  # type: ignore[override]
		if self._image.isNull():
			return
		delta = e.pos() - self._last_mouse
		self._last_mouse = e.pos()
		if self._resizing and self._resize_handle and self._cfg.layout.enabled_image and not self._image_bbox.isNull():
			# Resize logic in display space -> update scale_x/scale_y
			w0 = max(1, self._image_bbox.width())
			h0 = max(1, self._image_bbox.height())
			# Determine influence for each handle
			dw = 0
			dh = 0
			if 'e' in self._resize_handle:
				dw = delta.x()
			elif 'w' in self._resize_handle:
				dw = -delta.x()
			if 's' in self._resize_handle:
				dh = delta.y()
			elif 'n' in self._resize_handle:
				dh = -delta.y()
			# Convert to scale ratios
			sx_ratio = 1.0
			sy_ratio = 1.0
			if self._resize_handle in ("n","s"):
				# vertical edge -> only height
				sy_ratio = max(0.01, (h0 + dh) / float(h0))
			elif self._resize_handle in ("e","w"):
				# horizontal edge -> only width
				sx_ratio = max(0.01, (w0 + dw) / float(w0))
			else:
				# corner -> proportional (both axes equal by default if Shift held; otherwise both change)
				if QApplication.keyboardModifiers() & Qt.ShiftModifier:
					# proportional: use larger magnitude change
					ratio = max(0.01, (w0 + dw) / float(w0), (h0 + dh) / float(h0))
					sx_ratio = ratio; sy_ratio = ratio
				else:
					sx_ratio = max(0.01, (w0 + dw) / float(w0))
					sy_ratio = max(0.01, (h0 + dh) / float(h0))
			# Map display ratios back to model scale multipliers
			s = self._display_scale()
			if s <= 0:
				s = 1.0
			# Since bbox already in display, ratios already correct; just multiply scale_x/y
			self._cfg.image.scale_x = float(getattr(self._cfg.image, "scale_x", 1.0)) * sx_ratio
			self._cfg.image.scale_y = float(getattr(self._cfg.image, "scale_y", 1.0)) * sy_ratio
			# Recompute bbox origin to keep the opposite edge anchored visually: we accept slight drift for simplicity
			self.update()
			self.configChanged.emit(self._cfg)
			return

		if not self._dragging:
			return
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
			self.configChanged.emit(self._cfg)

	def mouseReleaseEvent(self, e: QMouseEvent) -> None:  # type: ignore[override]
		if e.button() == Qt.LeftButton:
			self._dragging = False
			self._resizing = False
			self._resize_handle = None

	def wheelEvent(self, e: QWheelEvent) -> None:  # type: ignore[override]
		# Ctrl + wheel rotates the nearer watermark (text or image) independently
		if e.modifiers() & Qt.ControlModifier:
			angle_delta = e.angleDelta().y() / 8.0
			target = self._pick_target_by_cursor(e.position().toPoint())
			if target == "text" and self._cfg.layout.enabled_text:
				current = float(getattr(self._cfg.layout, "text_rotation_deg", 0.0))
				self._cfg.layout.text_rotation_deg = (current + angle_delta) % 360
			elif target == "image" and self._cfg.layout.enabled_image:
				current = float(getattr(self._cfg.layout, "image_rotation_deg", 0.0))
				self._cfg.layout.image_rotation_deg = (current + angle_delta) % 360
			self.update()
			self.configChanged.emit(self._cfg)
			return
		# Otherwise, scale the nearest enabled watermark to cursor
		target = self._pick_target_by_cursor(e.position().toPoint())
		delta_steps = int(e.angleDelta().y() / 120)  # 1 step per notch
		if delta_steps == 0:
			return
		if target == "text" and self._cfg.layout.enabled_text:
			# Change font size by 1px per notch
			new_size = max(8, min(128, int(getattr(self._cfg.text, "size_px", 16) + delta_steps)))
			if new_size != getattr(self._cfg.text, "size_px", 16):
				self._cfg.text.size_px = new_size
				self.update()
				self.configChanged.emit(self._cfg)
		elif target == "image" and self._cfg.layout.enabled_image:
			# Change image scale by 1% per notch (5%..300%)
			current_percent = int(round(self._cfg.image.scale * 100))
			new_percent = max(5, min(300, current_percent + delta_steps))
			if new_percent != current_percent:
				self._cfg.image.scale = max(0.01, new_percent / 100.0)
				self.update()
				self.configChanged.emit(self._cfg)
