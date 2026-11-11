# 白边相框 4.0 · WhiteFrame

> A Windows desktop photo editor for film-style white borders, paper textures and analog effects, with automatic scanned-film-strip splitting, tone curves and LUT / XMP preset support.

给照片加白边、相纸纹理与胶片风格的单文件 Windows 桌面程序。中文界面，**纯本地运行**：不联网、不上传图片、不需要安装，也不需要管理员权限。

## 直接使用

双击 `WhiteFrame40.exe` 即可（Windows 10 / 11 64 位，约 43 MB）。不需要 Python，不需要安装依赖。

## 主要功能

- **边框 / 相纸**：白边宽度、纸纹、底色、撕边、圆角与方角
- **胶片**：内置多组胶片风格预设；可导入 Lightroom / Camera Raw 的 `.xmp` 曲线预设，导出 33³ 的 `.cube` 3D LUT
- **分割**：扫描胶片条自动识别画幅间隙并切成单张，支持 35mm 齿孔片基、多行整页扫描、指定张数等距切分；可原样输出 PNG
- **调色**：自动调色（曝光 / 白平衡 / 反差）、主通道与 R / G / B 四条曲线
- **创意**：网点印刷 Riso、颗粒、暗角等效果
- **界面**：现代 / Win95 两套皮肤，8 个功能页签；多图队列、逐张预览翻页、批量导出 `*_bordered.jpg`

## 仓库内容

| 路径 | 说明 |
| --- | --- |
| `WhiteFrame40.exe` | 4.0 单文件可执行程序 |
| `src/app40.py` | 界面与交互（PySide6） |
| `src/core40.py` | 图像处理、胶片模拟、分割算法（Pillow） |
| `src/paperfx40.py` | 相纸与撕边特效 |
| `src/qt_runtime40.py` | PyInstaller runtime hook（预注册 Qt DLL 目录） |
| `src/WhiteFrame40.spec` | 打包配置（路径已改为相对，可在任意目录执行） |
| `src/icon.ico` / `src/icon.png` | 程序图标 |

**本仓库不包含**：测试例图与样张、胶片 LUT（`.cube`）与 XMP 预设的导出文件、历史版本 exe、构建中间产物。预设由程序内置生成，运行时不依赖这些外部文件；内置预设名称仅用于描述风格，与相应厂商无关。

## 重新编译

需要 Python 3.10+、Pillow、PySide6-Essentials、PyInstaller：

```
pip install pillow PySide6-Essentials pyinstaller
cd src
pyinstaller --noconfirm WhiteFrame40.spec --distpath ../dist --workpath ../build
```

产物在 `dist/WhiteFrame40.exe`。spec 里用 `SPECPATH` 定位源码与图标，因此不受存放目录影响；运行时会用 `qt_runtime40.py` 预注册 Qt DLL 目录，并剔除会被系统抢占的 ICU / UCRT / API-set DLL。

## 授权

MIT，见 [LICENSE](LICENSE)。
