# Windows 本地个人工具箱

基于 Python、PySide6 和 Pillow 的本地桌面工具箱。第一版提供“图片工具 → 批量打水印”，不需要登录、数据库或网络服务。

## 功能

- 拖拽图片、选择多张图片或选择整个文件夹（含子目录）
- 支持 JPG、JPEG、PNG、WEBP
- 文字、字号、透明度、颜色、位置和边距设置
- 单个水印与平铺水印；平铺可调角度和间距
- 当前图片实时预览
- 后台批量处理、进度、成功/失败统计和失败隔离
- 默认写入项目下的 `output` 目录；不覆盖原图，重名时自动添加序号

## 图片质量策略

- 合成前后不缩放原图，不做锐化、降噪或图像增强
- PNG 保持 PNG 并无损保存，保留透明通道
- JPEG 保持 JPEG，以质量 95、4:4:4 色度采样重新编码
- WEBP 保持 WEBP，以质量 95 和 Pillow 的高质量编码方式保存
- EXIF 与 ICC Profile 在源格式和 Pillow 支持时原样传给输出文件

JPEG 等有损格式只要修改像素就必须重新编码，因此无法做到二进制无损；本项目用固定的高质量参数避免默认低质量压缩。动画图片不在第一版范围内。

## Windows 启动

要求安装 Python 3.10 或更高版本，并确保 `python` 命令已加入 PATH。

最简单的方式：双击 `run.bat`。首次启动会自动创建 `.venv` 并安装依赖。

也可以在 PowerShell 中运行：

```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python main.py
```

## 测试

```powershell
.venv\Scripts\python.exe -m unittest discover -v
```

测试覆盖输出尺寸、JPEG 质量参数与 EXIF、PNG 透明通道、平铺合成、重名保护，以及单张失败不会中断批处理。

## 目录结构

```text
app/                    主窗口与应用入口
components/             可复用 UI 组件
services/               独立于界面的图片处理服务
tools/watermark/         批量水印界面与后台任务
utils/                   文件和系统工具
tests/                   自动化测试
main.py                  程序入口
run.bat                  Windows 一键启动
```

后续工具可继续放入 `tools/` 并在主窗口注册页面；当前没有提前实现插件系统。
