from __future__ import annotations

import json
import os
from dataclasses import asdict
from typing import Optional

from .models import WatermarkConfig


def get_templates_dir() -> str:
	dir_path = os.path.join(os.path.expanduser("~"), ".watermark_studio", "templates")
	os.makedirs(dir_path, exist_ok=True)
	return dir_path


def get_last_settings_path() -> str:
	dir_path = os.path.join(os.path.expanduser("~"), ".watermark_studio")
	os.makedirs(dir_path, exist_ok=True)
	return os.path.join(dir_path, "last_settings.json")


def save_template(name: str, cfg: WatermarkConfig) -> str:
	path = os.path.join(get_templates_dir(), f"{name}.json")
	with open(path, "w", encoding="utf-8") as f:
		json.dump(asdict(cfg), f, ensure_ascii=False, indent=2)
	return path


def load_template(path: str) -> Optional[WatermarkConfig]:
	try:
		with open(path, "r", encoding="utf-8") as f:
			data = json.load(f)
		return _from_dict(data)
	except Exception:
		return None


def list_templates() -> list[str]:
	dir_path = get_templates_dir()
	return [os.path.join(dir_path, f) for f in os.listdir(dir_path) if f.lower().endswith(".json")]


def delete_template(path: str) -> bool:
	try:
		if os.path.exists(path):
			os.remove(path)
			return True
		return False
	except Exception:
		return False


def rename_template(path: str, new_name: str) -> Optional[str]:
	dir_path = get_templates_dir()
	new_path = os.path.join(dir_path, f"{new_name}.json")
	try:
		os.replace(path, new_path)
		return new_path
	except Exception:
		return None


def save_last_settings(cfg: WatermarkConfig) -> None:
	path = get_last_settings_path()
	with open(path, "w", encoding="utf-8") as f:
		json.dump(asdict(cfg), f, ensure_ascii=False, indent=2)


def load_last_settings() -> Optional[WatermarkConfig]:
	path = get_last_settings_path()
	if not os.path.exists(path):
		return None
	with open(path, "r", encoding="utf-8") as f:
		data = json.load(f)
	return _from_dict(data)


def _from_dict(data: dict) -> WatermarkConfig:
	from .models import WatermarkConfig
	wm = WatermarkConfig()
	if "text" in data:
		t = data["text"]
		for k, v in t.items():
			setattr(wm.text, k, v)
	if "image" in data:
		i = data["image"]
		for k, v in i.items():
			setattr(wm.image, k, v)
	if "layout" in data:
		l = data["layout"]
		for k, v in l.items():
			setattr(wm.layout, k, v)
	return wm
