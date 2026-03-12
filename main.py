import sys
import os
from PyQt6.QtWidgets import (QApplication, QMainWindow, QLabel, QScrollArea, 
                             QFileDialog, QMessageBox, QMenu, QSizePolicy, QToolBar)
from PyQt6.QtGui import (QPixmap, QImage, QAction, QIcon, QTransform, 
                         QPalette, QShortcut, QKeySequence, QActionGroup)
from PyQt6.QtCore import Qt, QSize
from PIL import Image, ImageOps
import pillow_heif
import urllib.parse

# Try importing win32com.client for explorer integration
try:
    import win32com.client
    HAS_WIN32 = True
except ImportError:
    HAS_WIN32 = False

# Register HEIC opener
pillow_heif.register_heif_opener()

class ImageLabel(QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Ignored)
        self.setScaledContents(True)

class ImageViewer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.image_path = None
        self.current_image = None  # PIL Image object
        self.scale_factor = 1.0
        self.angle = 0
        self.file_list = []
        self.current_index = -1
        self.auto_fit_mode = True # Default to auto-fit
        
        # Sort settings
        self.sort_mode = 'name' # name, ctime, mtime
        self.sort_reverse = False

        self.initUI()
        
        # Check if file provided as argument (e.g. "Open with")
        if len(sys.argv) > 1:
            file_path = sys.argv[1]
            if os.path.isfile(file_path):
                self.load_image(file_path)

    def initUI(self):
        self.setWindowTitle("PrismView - HEIC Viewer")
        self.resize(800, 600)

        # Image Label
        self.image_label = ImageLabel()
        self.image_label.setBackgroundRole(QPalette.ColorRole.Base)

        # Scroll Area
        self.scroll_area = QScrollArea()
        self.scroll_area.setBackgroundRole(QPalette.ColorRole.Dark)
        self.scroll_area.setWidget(self.image_label)
        self.scroll_area.setVisible(False)
        self.scroll_area.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setCentralWidget(self.scroll_area)
        
        # Install event filter on scroll area viewport to capture wheel events
        self.scroll_area.viewport().installEventFilter(self)
        
        # Shortcuts for navigation (Global to window)
        self.prev_shortcut = QShortcut(QKeySequence(Qt.Key.Key_Left), self)
        self.prev_shortcut.activated.connect(self.prev_image)

        self.next_shortcut = QShortcut(QKeySequence(Qt.Key.Key_Right), self)
        self.next_shortcut.activated.connect(self.next_image)

        # Actions
        open_act = QAction("&打开...", self)
        open_act.setShortcut("Ctrl+O")
        open_act.triggered.connect(self.open_file_dialog)

        save_act = QAction("&保存", self)
        save_act.setShortcut("Ctrl+S")
        save_act.triggered.connect(lambda: self.save_image(silent=False))

        rotate_left_act = QAction("向左旋转", self)
        rotate_left_act.setShortcut("Ctrl+L")
        rotate_left_act.triggered.connect(self.rotate_left)

        rotate_right_act = QAction("向右旋转", self)
        rotate_right_act.setShortcut("Ctrl+R")
        rotate_right_act.triggered.connect(self.rotate_right)
        
        fit_act = QAction("适应窗口", self)
        fit_act.setShortcut("Ctrl+F")
        fit_act.triggered.connect(self.fit_to_window)

        # Menus
        file_menu = self.menuBar().addMenu("&文件")
        file_menu.addAction(open_act)
        file_menu.addAction(save_act)

        view_menu = self.menuBar().addMenu("&查看")
        view_menu.addAction(rotate_left_act)
        view_menu.addAction(rotate_right_act)
        view_menu.addSeparator()
        view_menu.addAction(fit_act)
        view_menu.addSeparator()
        
        # Sort Menu
        sort_menu = view_menu.addMenu("排序方式")
        
        self.sort_name = QAction("按名称", self)
        self.sort_name.setCheckable(True)
        self.sort_name.setChecked(True)
        self.sort_name.triggered.connect(lambda: self.change_sort('name'))
        
        self.sort_ctime = QAction("按创建时间", self)
        self.sort_ctime.setCheckable(True)
        self.sort_ctime.triggered.connect(lambda: self.change_sort('ctime'))
        
        self.sort_mtime = QAction("按修改时间", self)
        self.sort_mtime.setCheckable(True)
        self.sort_mtime.triggered.connect(lambda: self.change_sort('mtime'))
        
        self.sort_asc = QAction("递增", self)
        self.sort_asc.setCheckable(True)
        self.sort_asc.setChecked(True)
        self.sort_asc.triggered.connect(lambda: self.change_sort_order(False))
        
        self.sort_desc = QAction("递减", self)
        self.sort_desc.setCheckable(True)
        self.sort_desc.triggered.connect(lambda: self.change_sort_order(True))
        
        # Group for sort mode
        self.sort_mode_group = QActionGroup(self)
        self.sort_mode_group.addAction(self.sort_name)
        self.sort_mode_group.addAction(self.sort_ctime)
        self.sort_mode_group.addAction(self.sort_mtime)
        
        # Group for sort order
        self.sort_order_group = QActionGroup(self)
        self.sort_order_group.addAction(self.sort_asc)
        self.sort_order_group.addAction(self.sort_desc)
        
        sort_menu.addAction(self.sort_name)
        sort_menu.addAction(self.sort_ctime)
        sort_menu.addAction(self.sort_mtime)
        sort_menu.addSeparator()
        sort_menu.addAction(self.sort_asc)
        sort_menu.addAction(self.sort_desc)
        
        # Sync with Explorer Action
        if HAS_WIN32:
            sort_menu.addSeparator()
            sync_explorer_act = QAction("同步资源管理器排序", self)
            sync_explorer_act.triggered.connect(self.sync_with_explorer)
            sort_menu.addAction(sync_explorer_act)

        # Toolbar
        self.toolbar = QToolBar("工具栏")
        self.toolbar.setIconSize(QSize(32, 32))
        self.addToolBar(Qt.ToolBarArea.TopToolBarArea, self.toolbar)
        
        # Add actions to toolbar
        self.toolbar.addAction(open_act)
        self.toolbar.addAction(save_act)
        self.toolbar.addSeparator()
        self.toolbar.addAction(rotate_left_act)
        self.toolbar.addAction(rotate_right_act)
        self.toolbar.addSeparator()
        self.toolbar.addAction(fit_act)
        if HAS_WIN32:
            self.toolbar.addAction(sync_explorer_act)

    def open_file_dialog(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "打开图片", "", 
                                                   "Images (*.png *.jpg *.jpeg *.bmp *.gif *.heic);;All Files (*)")
        if file_path:
            self.load_image(file_path)

    def load_image(self, file_path):
        try:
            self.image_path = file_path
            
            # Try to auto-sync sort order on first load if this is a new folder
            # or if file_list is empty. 
            # But let's be conservative: only sync if user asked or maybe just once.
            # User asked: "他有办法知道...吗，然后和这个排序方式对齐"
            # It implies automatic or semi-automatic. Let's try to sync automatically when loading a new folder.
            new_folder = os.path.dirname(file_path)
            current_folder = os.path.dirname(self.file_list[0]) if self.file_list else None
            
            should_sync = False
            if new_folder != current_folder:
                 should_sync = True

            # Open with PIL to support HEIC and rotation
            self.current_image = Image.open(self.image_path)
            # Ensure image is in a mode compatible with Qt (RGB or RGBA)
            if self.current_image.mode not in ("RGB", "RGBA"):
                self.current_image = self.current_image.convert("RGBA")
            
            if should_sync and HAS_WIN32:
                self.sync_with_explorer(silent=True)
            
            self.update_file_list()
            self.display_image()
            self.scroll_area.setVisible(True)
            self.fit_to_window()
            self.setWindowTitle(f"PrismView - {os.path.basename(file_path)}")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"无法加载图片: {str(e)}")

    def update_file_list(self):
        if not self.image_path:
            return
        
        folder = os.path.dirname(self.image_path)
        valid_extensions = {'.png', '.jpg', '.jpeg', '.bmp', '.gif', '.heic'}
        
        try:
            files = [f for f in os.listdir(folder) 
                     if os.path.splitext(f)[1].lower() in valid_extensions]
            
            # Sorting logic
            if self.sort_mode == 'name':
                # Natural sort might be better but simple sort is okay for now
                # Windows uses natural sort (1, 2, 10), python default is lexical (1, 10, 2)
                # To fully mimic windows, we might need a natural sort key
                files.sort(key=lambda x: x.lower(), reverse=self.sort_reverse)
            elif self.sort_mode == 'ctime':
                files.sort(key=lambda x: os.path.getctime(os.path.join(folder, x)), reverse=self.sort_reverse)
            elif self.sort_mode == 'mtime':
                files.sort(key=lambda x: os.path.getmtime(os.path.join(folder, x)), reverse=self.sort_reverse)
            elif self.sort_mode == 'size':
                files.sort(key=lambda x: os.path.getsize(os.path.join(folder, x)), reverse=self.sort_reverse)
            else:
                files.sort(key=lambda x: x.lower(), reverse=self.sort_reverse)

            self.file_list = [os.path.join(folder, f) for f in files]
            
            try:
                self.current_index = self.file_list.index(self.image_path)
            except ValueError:
                self.current_index = 0
        except Exception:
            self.file_list = []

    def change_sort(self, mode):
        self.sort_mode = mode
        self.update_file_list()
        
    def change_sort_order(self, reverse):
        self.sort_reverse = reverse
        self.update_file_list()

    def sync_with_explorer(self, silent=False):
        if not HAS_WIN32:
            if not silent:
                QMessageBox.warning(self, "不支持", "无法加载 pywin32 库，不支持同步功能。")
            return

        if not self.image_path:
            return

        folder_path = os.path.dirname(self.image_path)
        folder_path = os.path.normpath(folder_path).lower()

        try:
            shell = win32com.client.Dispatch("Shell.Application")
            windows = shell.Windows()
            
            found = False
            sort_column = None
            sort_direction = 1 # 1: Ascending, -1: Descending
            
            for window in windows:
                try:
                    # Check if it's an explorer window
                    if "explorer.exe" not in window.FullName.lower():
                        continue
                        
                    # Get window path
                    # LocationURL is like file:///C:/Users/...
                    url = window.LocationURL
                    path = urllib.parse.unquote(url).replace("file:///", "")
                    # Fix path format (e.g. forward slashes)
                    path = os.path.normpath(path).lower()
                    
                    if path == folder_path:
                        found = True
                        # Found the window! Get sort columns.
                        # Document is IShellFolderViewDual
                        doc = window.Document
                        # SortColumns returns string like "prop:System.DateModified;" or "prop:-System.DateModified;"
                        sort_str = doc.SortColumns
                        
                        if sort_str:
                            # Take the first sort column
                            first_col = sort_str.split(';')[0]
                            if first_col.startswith('prop:'):
                                prop = first_col[5:]
                                if prop.startswith('-'):
                                    sort_direction = -1
                                    prop = prop[1:]
                                else:
                                    sort_direction = 1
                                
                                sort_column = prop
                        break
                except Exception:
                    continue
            
            if found and sort_column:
                # Map property to sort mode
                new_mode = 'name'
                if 'System.ItemNameDisplay' in sort_column:
                    new_mode = 'name'
                elif 'System.DateModified' in sort_column:
                    new_mode = 'mtime'
                elif 'System.DateCreated' in sort_column:
                    new_mode = 'ctime'
                elif 'System.Size' in sort_column:
                    new_mode = 'size'
                else:
                    # Default fallback
                    new_mode = 'name'
                
                self.sort_mode = new_mode
                self.sort_reverse = (sort_direction == -1)
                
                # Update UI Check state
                if self.sort_mode == 'name': self.sort_name.setChecked(True)
                elif self.sort_mode == 'ctime': self.sort_ctime.setChecked(True)
                elif self.sort_mode == 'mtime': self.sort_mtime.setChecked(True)
                
                if self.sort_reverse: self.sort_desc.setChecked(True)
                else: self.sort_asc.setChecked(True)
                
                if not silent:
                    # Optional: show a small status message or tooltip instead of popup
                    # QMessageBox.information(self, "同步成功", f"已同步排序: {self.sort_mode}, {'倒序' if self.sort_reverse else '正序'}")
                    print(f"Synced: {self.sort_mode}, {self.sort_reverse}")
                    
                self.update_file_list()
                
            elif not found:
                if not silent:
                    QMessageBox.information(self, "提示", "未找到该文件夹的资源管理器窗口，无法同步排序。")
                    
        except Exception as e:
            if not silent:
                QMessageBox.warning(self, "错误", f"同步排序失败: {str(e)}")

    def display_image(self):
        if self.current_image is None:
            return

        # Convert PIL Image to QImage
        im = self.current_image
        if im.mode != "RGBA":
            im = im.convert("RGBA")
            
        data = im.tobytes("raw", "BGRA")
        qim = QImage(data, im.width, im.height, QImage.Format.Format_ARGB32)

        self.pixmap = QPixmap.fromImage(qim)
        self.update_label_size()

    def update_label_size(self):
        if hasattr(self, 'pixmap') and not self.pixmap.isNull():
            new_width = int(self.pixmap.width() * self.scale_factor)
            new_height = int(self.pixmap.height() * self.scale_factor)
            scaled_pixmap = self.pixmap.scaled(
                new_width, new_height, 
                Qt.AspectRatioMode.KeepAspectRatio, 
                Qt.TransformationMode.SmoothTransformation
            )
            self.image_label.setPixmap(scaled_pixmap)
            self.image_label.resize(scaled_pixmap.size())

    def fit_to_window(self):
        if not hasattr(self, 'pixmap') or self.pixmap.isNull():
            return
        
        self.auto_fit_mode = True
        
        # Use viewport size to get the actual visible area
        scroll_size = self.scroll_area.viewport().size()
        pixmap_size = self.pixmap.size()
        
        if pixmap_size.width() > 0 and pixmap_size.height() > 0:
            scale_w = scroll_size.width() / pixmap_size.width()
            scale_h = scroll_size.height() / pixmap_size.height()
            # Fit to window but do not upscale small images automatically
            self.scale_factor = min(scale_w, scale_h, 1.0) * 0.99 
            self.update_label_size()
            
    def resizeEvent(self, event):
        if self.auto_fit_mode:
             self.fit_to_window()
        super().resizeEvent(event)

    def rotate_left(self):
        if self.current_image:
            self.current_image = self.current_image.rotate(90, expand=True)
            self.display_image()
            self.save_image(silent=True) # Auto save silently

    def rotate_right(self):
        if self.current_image:
            self.current_image = self.current_image.rotate(-90, expand=True)
            self.display_image()
            self.save_image(silent=True) # Auto save silently

    def save_image(self, silent=False):
        if self.current_image and self.image_path:
            try:
                # Save overwrites the current file
                # For HEIC, saving might need explicit format if not inferred
                # But PIL usually handles it if format is preserved or specified.
                # However, overwriting HEIC directly might be tricky with some libs.
                # Let's try standard save first.
                self.current_image.save(self.image_path)
                if not silent:
                    QMessageBox.information(self, "成功", "图片已保存")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"保存失败: {str(e)}")

    def eventFilter(self, source, event):
        if source == self.scroll_area.viewport() and event.type() == event.Type.Wheel:
            # Check for Ctrl key if we wanted standard behavior, but user asked for simple wheel zoom
            # We'll allow simple wheel zoom. To scroll, use scrollbars or drag (drag not implemented yet)
            # Or use Ctrl to scroll? No, standard is Wheel=Scroll, Ctrl+Wheel=Zoom.
            # But user said "滚轮放大缩小". I will prioritize zoom.
            
            delta = event.angleDelta().y()
            if delta > 0:
                self.zoom_in()
            else:
                self.zoom_out()
            return True # Event handled
        return super().eventFilter(source, event)

    def zoom_in(self):
        self.auto_fit_mode = False
        self.scale_factor *= 1.25
        self.update_label_size()

    def zoom_out(self):
        self.auto_fit_mode = False
        self.scale_factor *= 0.8
        self.update_label_size()

    # keyPressEvent removed in favor of QShortcut
    
    def prev_image(self):
        if self.file_list and self.current_index > 0:
            self.current_index -= 1
            self.load_image(self.file_list[self.current_index])
        elif self.file_list:
            # Loop to end? Or stop? Let's stop at beginning.
            pass

    def next_image(self):
        if self.file_list and self.current_index < len(self.file_list) - 1:
            self.current_index += 1
            self.load_image(self.file_list[self.current_index])
        elif self.file_list:
            # Loop to start?
            pass

if __name__ == '__main__':
    app = QApplication(sys.argv)
    viewer = ImageViewer()
    viewer.showMaximized()
    sys.exit(app.exec())
