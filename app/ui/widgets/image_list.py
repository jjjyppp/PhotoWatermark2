from PySide6.QtWidgets import QWidget, QVBoxLayout, QListWidget, QListWidgetItem, QFileDialog
from PySide6.QtGui import QImage, QPixmap, QDragEnterEvent, QDropEvent
from PySide6.QtCore import Qt, Signal, QSize
import os

SUPPORTED_INPUT_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff"}


class ImageListWidget(QWidget):
	imageSelected = Signal(str)

	def __init__(self, parent=None) -> None:
		super().__init__(parent)
		self.setAcceptDrops(True)
		self.list = QListWidget(self)
		self.list.setViewMode(QListWidget.IconMode)
		self.list.setMovement(QListWidget.Static)
		# Slightly smaller thumbnails and grid to reduce sidebar width
		self.list.setIconSize(QSize(160, 120))
		self.list.setResizeMode(QListWidget.Adjust)
		self.list.setGridSize(QSize(180, 168))
		self.list.setWordWrap(True)
		self.list.setSpacing(8)
		self.list.itemSelectionChanged.connect(self._emit_selected)

		layout = QVBoxLayout(self)
		layout.setContentsMargins(4, 4, 4, 4)
		layout.addWidget(self.list)

	def _emit_selected(self) -> None:
		items = self.list.selectedItems()
		if items:
			self.imageSelected.emit(items[0].data(Qt.UserRole))

	def add_image(self, path: str) -> None:
		ext = os.path.splitext(path)[1].lower()
		if ext not in SUPPORTED_INPUT_EXTS:
			return
		image = QImage(path)
		if image.isNull():
			return
		thumb = QPixmap.fromImage(image.scaled(self.list.iconSize(), Qt.KeepAspectRatio, Qt.SmoothTransformation))
		item = QListWidgetItem()
		item.setText(os.path.basename(path))
		item.setToolTip(path)
		item.setIcon(thumb)
		item.setData(Qt.UserRole, path)
		self.list.addItem(item)

	def openFiles(self) -> None:
		paths, _ = QFileDialog.getOpenFileNames(self, "选择图片", "", "Images (*.png *.jpg *.jpeg *.bmp *.tif *.tiff)")
		for p in paths:
			self.add_image(p)

	def openFolder(self) -> None:
		folder = QFileDialog.getExistingDirectory(self, "选择文件夹")
		if not folder:
			return
		for root, _, files in os.walk(folder):
			for f in files:
				self.add_image(os.path.join(root, f))

	def get_all_paths(self) -> list[str]:
		paths: list[str] = []
		for i in range(self.list.count()):
			item = self.list.item(i)
			p = item.data(Qt.UserRole)
			if isinstance(p, str):
				paths.append(p)
		return paths

	def get_selected_paths(self) -> list[str]:
		paths: list[str] = []
		for item in self.list.selectedItems():
			p = item.data(Qt.UserRole)
			if isinstance(p, str):
				paths.append(p)
		return paths

	def dragEnterEvent(self, event: QDragEnterEvent) -> None:
		if event.mimeData().hasUrls():
			event.acceptProposedAction()
		else:
			event.ignore()

	def dropEvent(self, event: QDropEvent) -> None:
		for url in event.mimeData().urls():
			path = url.toLocalFile()
			if os.path.isdir(path):
				for root, _, files in os.walk(path):
					for f in files:
						self.add_image(os.path.join(root, f))
			else:
				self.add_image(path)
