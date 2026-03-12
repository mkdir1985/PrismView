# PrismView (图片查看器)

**PrismView** 是一个支持HEIC格式的轻量级图片查看器，具有艺术家般的流畅体验。它能够捕捉并折射出图片的每一处细节。

## 核心特性
- **格式支持**: 完美支持 Apple HEIC, JPG, PNG, BMP, GIF 等。
- **流畅操控**: 
    - 滚轮缩放 / 自适应窗口
    - 左右方向键切换图片
    - 自动同步资源管理器排序 (名称/时间/大小)
- **即时编辑**: 
    - 一键左/右旋转
    - 旋转后自动无损保存
- **系统集成**: 右键菜单 "Open with PrismView"

## 环境配置 (venv)
我已经为你准备好了独立的虚拟环境。

1. **自动使用**: 运行 `run.bat` 会自动检测并使用 `venv` 目录下的 Python 环境。
2. **手动激活**: 如果你想在命令行操作，请运行：
   ```powershell
   .\venv\Scripts\activate
   ```

## 安装依赖
虚拟环境 `venv` 已预装好所有依赖。如果需要重新安装：
```bash
# 确保已激活虚拟环境
pip install -r requirements.txt
```
如果你需要启用资源管理器同步排序功能，还需要安装 `pywin32`:
```bash
pip install pywin32
```

## 使用方法
1. 直接运行 `run.bat` (支持拖拽图片到 bat 文件上打开)。
2. 在图片上右键 -> 打开方式 -> 选择 "My Python Image Viewer" (已配置为使用 venv)。

## 注册右键菜单
如果 "打开方式" 中没有显示，或者你想更新为使用 venv 环境，请运行：
```bash
.\venv\Scripts\python.exe register.py
```
