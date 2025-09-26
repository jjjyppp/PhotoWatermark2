from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional, Tuple


Color = Tuple[int, int, int, int]  # RGBA 0-255


@dataclass
class TextWatermark:
	text: str = "Sample Watermark"
	family: str = "Segoe UI"
	size_px: int = 16
	bold: bool = False
	italic: bool = False
	color: Color = (0, 0, 0, 255)
	shadow: bool = False
	outline: bool = False
	outline_color: Color = (0, 0, 0, 160)
	shadow_color: Color = (0, 0, 0, 160)
	shadow_offset: Tuple[int, int] = (2, 2)


@dataclass
class ImageWatermark:
	path: Optional[str] = None
	scale: float = 0.3  # relative to shorter edge (uniform)
	scale_x: float = 1.0  # non-uniform scaling multiplier on width
	scale_y: float = 1.0  # non-uniform scaling multiplier on height
	opacity: float = 0.75  # 0-1


@dataclass
class WatermarkLayout:
	# Deprecated unified position kept for backward compatibility
	position: Tuple[float, float] = (0.5, 0.5)
	# New separate positions
	text_position: Tuple[float, float] = (0.5, 0.5)
	image_position: Tuple[float, float] = (0.5, 0.5)
	# Backward-compatible unified rotation; new fields below take precedence where used
	rotation_deg: float = 0.0
	# Separate rotations
	text_rotation_deg: float = 0.0
	image_rotation_deg: float = 0.0
	enabled_text: bool = False
	enabled_image: bool = False


@dataclass
class WatermarkConfig:
	text: TextWatermark = field(default_factory=TextWatermark)
	image: ImageWatermark = field(default_factory=ImageWatermark)
	layout: WatermarkLayout = field(default_factory=WatermarkLayout)


@dataclass
class ExportOptions:
	output_dir: str = ""
	format: str = "PNG"  # or JPEG
	jpeg_quality: int = 90
	scale_mode: str = "none"  # none, width, height, both, percent
	scale_value: float = 1.0   # width, or percent, or width in both
	scale_height: float = 0.0  # used when scale_mode == 'both'
	name_rule: str = "suffix"  # original, prefix, suffix
	name_affix: str = "_watermarked"

