# 水印批量处理工具（Python + PySide6）

## 功能概览
- 批量导入图片（文件/文件夹），展示缩略图列表
- 文本/图片水印：颜色、透明度、缩放、旋转、阴影/描边
- 九宫格预设、拖拽定位、实时预览
- 导出 JPEG/PNG，JPEG 质量可调；尺寸缩放；文件命名规则
- 模板保存/加载，上次配置自动恢复

## 环境准备
- Python 3.10+（Windows 10/11）
- 安装依赖：
```bash
pip install -r requirements.txt
```

## 运行
```bash
python -m app
```

## 目录结构
```
app/
  __init__.py
  main.py
  ui/
    main_window.py
    widgets/
      image_list.py
      preview.py
      controls_panel.py
  core/
    watermark_engine.py
    models.py
    templates.py
assets/
  fonts/
  icons/
```

## 备注
- PNG 输入必须支持透明通道；建议输入也支持 BMP/TIFF。
- 导出禁止覆盖原图，需指定单独输出目录。


