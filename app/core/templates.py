from __future__ import annotations

import json
import os
from dataclasses import asdict
from typing import Optional, List, Dict

from app.core.models import WatermarkConfig


def get_templates_dir() -> str:
	dir_path = os.path.join(os.path.expanduser("~"), ".watermark_studio", "templates")
	os.makedirs(dir_path, exist_ok=True)
	return dir_path


def get_last_settings_path() -> str:
	dir_path = os.path.join(os.path.expanduser("~"), ".watermark_studio")
	os.makedirs(dir_path, exist_ok=True)
	return os.path.join(dir_path, "last_settings.json")


def get_default_template_path() -> str:
	dir_path = os.path.join(os.path.expanduser("~"), ".watermark_studio")
	os.makedirs(dir_path, exist_ok=True)
	return os.path.join(dir_path, "default_template.json")


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


def set_default_template(template_path: str) -> bool:
	try:
		default_path = get_default_template_path()
		# 读取模板内容
		with open(template_path, "r", encoding="utf-8") as f:
			data = json.load(f)
		# 保存为默认模板
		with open(default_path, "w", encoding="utf-8") as f:
			json.dump(data, f, ensure_ascii=False, indent=2)
		return True
	except Exception:
		return False


def load_default_template() -> Optional[WatermarkConfig]:
	path = get_default_template_path()
	if not os.path.exists(path):
		return None
	try:
		with open(path, "r", encoding="utf-8") as f:
			data = json.load(f)
		return _from_dict(data)
	except Exception:
		return None


def _from_dict(data: dict) -> WatermarkConfig:
	from app.core.models import WatermarkConfig
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


def get_session_file_path() -> str:
	"""获取会话文件的路径"""
	return os.path.join(os.path.expanduser("~"), "PhotoWatermark2", "last_session.json")


def save_session_state(image_paths: List[str], per_image_configs: Dict[str, WatermarkConfig]) -> bool:
	"""保存当前会话状态，包括图片列表和每个图片的水印配置"""
	try:
		# 确保目录存在
		session_path = get_session_file_path()
		os.makedirs(os.path.dirname(session_path), exist_ok=True)
		
		# 准备要保存的数据
		data = {
			"image_paths": image_paths,
			"per_image_configs": {}
		}
		
		# 转换每个图片的配置为字典
		for path, config in per_image_configs.items():
			try:
				data["per_image_configs"][path] = asdict(config)
			except Exception:
				# 跳过无法序列化的配置
				continue
		
		# 保存数据到文件
		with open(session_path, "w", encoding="utf-8") as f:
			json.dump(data, f, ensure_ascii=False, indent=2)
		return True
	except Exception:
		return False


def load_session_state() -> Optional[Dict]:
	"""加载之前保存的会话状态"""
	try:
		session_path = get_session_file_path()
		if not os.path.exists(session_path):
			return None
			
		with open(session_path, "r", encoding="utf-8") as f:
			data = json.load(f)
			
		# 验证数据结构
		if "image_paths" not in data or "per_image_configs" not in data:
			return None
			
		return data
	except Exception:
		return None


def clear_session_state() -> bool:
	"""清除保存的会话状态"""
	try:
		session_path = get_session_file_path()
		if os.path.exists(session_path):
			os.remove(session_path)
		return True
	except Exception:
		return False
