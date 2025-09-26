from __future__ import annotations

from PySide6.QtGui import QImage, QPainter, QColor, QFont, QPixmap, QTransform, QPainterPath, QPen
from PySide6.QtCore import Qt, QPointF, QRectF
from .models import WatermarkConfig


class WatermarkEngine:
	def __init__(self) -> None:
		self._logo_cache: dict[str, QPixmap] = {}

	def render(self, base: QImage, cfg: WatermarkConfig) -> QImage:
		if base.isNull():
			return base
		canvas = QImage(base.size(), QImage.Format_ARGB32_Premultiplied)
		canvas.fill(Qt.transparent)

		p = QPainter(canvas)
		p.setRenderHints(QPainter.Antialiasing | QPainter.TextAntialiasing | QPainter.SmoothPixmapTransform, True)

		p.drawImage(0, 0, base)

		# image watermark at its own position
		if cfg.layout.enabled_image and cfg.image.path:
			ix = base.width() * (cfg.layout.image_position[0] if cfg.layout.image_position else cfg.layout.position[0])
			iy = base.height() * (cfg.layout.image_position[1] if cfg.layout.image_position else cfg.layout.position[1])
			p.save()
			p.translate(QPointF(ix, iy))
			# Prefer specific image rotation; fallback to legacy unified rotation
			p.rotate(getattr(cfg.layout, "image_rotation_deg", 0.0) or getattr(cfg.layout, "rotation_deg", 0.0))
			self._draw_image_watermark(p, base, cfg)
			p.restore()

		# text watermark at its own position
		if cfg.layout.enabled_text and (cfg.text.text or ""):
			tx = base.width() * (cfg.layout.text_position[0] if cfg.layout.text_position else cfg.layout.position[0])
			ty = base.height() * (cfg.layout.text_position[1] if cfg.layout.text_position else cfg.layout.position[1])
			p.save()
			p.translate(QPointF(tx, ty))
			# Prefer specific text rotation; fallback to legacy unified rotation
			p.rotate(getattr(cfg.layout, "text_rotation_deg", 0.0) or getattr(cfg.layout, "rotation_deg", 0.0))
			self._draw_text_watermark(p, base, cfg)
			p.restore()

		p.end()
		return canvas

	def _text_path_centered(self, painter: QPainter, text: str) -> QPainterPath:
		metrics = painter.fontMetrics()
		rect = metrics.boundingRect(text)
		path = QPainterPath()
		path.addText(-rect.width() / 2.0, rect.height() / 2.5, painter.font(), text)
		return path

	def _draw_text_watermark(self, p: QPainter, base: QImage, cfg: WatermarkConfig) -> None:
		font = QFont(cfg.text.family)
		# Use pixel size to avoid DPI differences across images
		try:
			font.setPixelSize(int(getattr(cfg.text, "size_px", 16)))
		except Exception:
			font.setPixelSize(16)
		font.setBold(cfg.text.bold)
		font.setItalic(cfg.text.italic)
		p.setFont(font)

		main_color = QColor(*cfg.text.color)
		outline_color = QColor(*cfg.text.outline_color)
		shadow_color = QColor(*cfg.text.shadow_color)

		path = self._text_path_centered(p, cfg.text.text)

		if cfg.text.shadow:
			p.save()
			p.translate(cfg.text.shadow_offset[0], cfg.text.shadow_offset[1])
			p.setPen(Qt.NoPen)
			p.setBrush(shadow_color)
			p.drawPath(path)
			p.restore()

		if cfg.text.outline:
			p.save()
			pen = QPen(outline_color)
			pen.setWidth(3)
			p.setPen(pen)
			p.setBrush(Qt.NoBrush)
			p.drawPath(path)
			p.restore()

		p.save()
		p.setPen(Qt.NoPen)
		p.setBrush(main_color)
		p.drawPath(path)
		p.restore()

	def _draw_image_watermark(self, p: QPainter, base: QImage, cfg: WatermarkConfig) -> None:
		path = cfg.image.path or ""
		pix = self._logo_cache.get(path)
		if pix is None:
			pm = QPixmap(path)
			if pm.isNull():
				return
			self._logo_cache[path] = pm
			pix = pm

		shorter = min(base.width(), base.height())
		# Base width from uniform scale
		base_w = max(1, int(shorter * cfg.image.scale))
		# Apply non-uniform multipliers
		sx = max(0.01, float(getattr(cfg.image, "scale_x", 1.0)))
		sy = max(0.01, float(getattr(cfg.image, "scale_y", 1.0)))
		w = max(1, int(base_w * sx))
		# Compute height preserving pixmap aspect then apply sy
		scaled_w = pix.scaledToWidth(w, Qt.SmoothTransformation)
		h = max(1, int(scaled_w.height() * sy))
		scaled = pix.scaled(w, h, Qt.IgnoreAspectRatio, Qt.SmoothTransformation)

		p.save()
		p.setOpacity(cfg.image.opacity)
		p.drawPixmap(int(-scaled.width() / 2), int(-scaled.height() / 2), scaled)
		p.restore()

