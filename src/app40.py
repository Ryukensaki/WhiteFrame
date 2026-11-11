# -*- coding: utf-8 -*-
"""白边相框 4.0"""
import os
import sys
import tempfile
import traceback as _tb


def _bootlog(msg):
    """调试开关：打包正式版时保持静默。"""
    return


_bootlog("python started")
try:
    from PIL import Image
    _bootlog("PIL ok")
    from PySide6.QtCore import Qt as _QtProbe
    _bootlog("Qt ok")
    from core40 import FILMS as _FilmProbe
    _bootlog("core40 ok, films=%d" % len(_FilmProbe))
    from PIL import Image, ImageDraw, ImageOps
    from PySide6.QtCore import QEvent, QPointF, QRectF, QSize, Qt, QThread, QTimer, Signal
    from PySide6.QtGui import (QBrush, QColor, QFontDatabase, QIcon, QImage, QKeySequence,
                               QPen,
                               QPainter, QPainterPath, QPixmap, QShortcut)
    from PySide6.QtWidgets import (
        QApplication, QButtonGroup, QCheckBox, QColorDialog, QComboBox, QFileDialog,
        QFrame, QGridLayout, QHBoxLayout, QLabel, QLineEdit, QMainWindow, QMessageBox,
        QProgressBar, QPushButton, QScrollArea, QSizePolicy, QSlider, QStackedWidget, QToolButton,
        QVBoxLayout, QWidget,
    )

    from core40 import (FIELD_DEFS, SKIP_DIR, STRIP_FORMATS, Style, XMP_FILMS, _save,
                       collage, collage_name, collect, compose, draw_strip_boxes,
                       export_cube, field_auto, parse_xmp, process_one, read_exif,
                       register_xmp, split_sheet, split_strip, strip_boxes,
                       twin_canvas)
    from paperfx40 import paper_texture
    _bootlog("all imports ok")
except Exception:
    _bootlog("IMPORT FAIL:\n" + _tb.format_exc())
    raise


APP = "白边相框 4.0"
DEFAULT_ON = {"camera", "lens", "focal", "aperture", "shutter", "iso"}
MODES = [("纯色", "solid"), ("取色", "sample"), ("模糊", "blur")]
RATIOS = [("原图", None), ("1:1", 1.0), ("4:5", 0.8), ("3:4", 0.75),
          ("3:2", 1.5), ("16:9", 16 / 9)]
COLS = [("自动", 0), ("2 列", 2), ("3 列", 3), ("4 列", 4)]
PUSH_CHIPS = [("标准", "0"), ("+1 档", "1"), ("+2 档", "2"), ("−1 档", "-1")]
FINISH_CHIPS = [("光面", "光面"), ("绒面", "绒面"), ("金属", "金属"), ("哑光", "哑光")]
POS = [("右下", "br"), ("左下", "bl"), ("右上", "tr"), ("左上", "tl"),
       ("底中", "bc"), ("顶中", "tc")]
GRADE_GROUPS = [
    ("白平衡", [("temp", "色温"), ("tint", "色调")]),
    ("色调", [("exposure", "曝光"), ("contrast", "对比度"), ("highlights", "高光"),
              ("shadows", "阴影"), ("whites", "白色色阶"), ("blacks", "黑色色阶")]),
    ("细节与色彩", [("texture", "纹理"), ("clarity", "清晰度"), ("dehaze", "去朦胧"),
                   ("vibrance", "鲜艳度"), ("saturation", "饱和度")]),
]
XMP_DIR = os.path.join(os.path.expanduser("~"), ".whiteframe_xmp")
RISO_INKS = [("墨黑 + 珊瑚", ("#1f1c1a", "#ff5a4a")),
             ("墨蓝 + 橙", ("#1d2b46", "#ff8a3d")),
             ("墨绿 + 樱粉", ("#20302a", "#ff9ec4")),
             ("单色黑", ("#1b1b1b", "#1b1b1b"))]
FILM_LIST = ["关闭", "Portra 160", "Portra 400", "Portra 800", "Gold 200",
             "Ektar 100", "Pro 400H", "Superia 400", "Lomo 400", "Velvia 50",
             "Provia 100F", "Ektachrome E100", "CineStill 800T", "HP5 Plus", "Tri-X 400",
             "Kodachrome 64", "Ultramax 400", "ColorPlus 200", "Fuji C200", "Astia 100F",
             "Vista 400", "Delta 3200", "Acros 100", "Pan F 50", "Retro 80S",
             "Cross Process", "Bleach Bypass",
             "Vision3 250D", "Vision3 500T", "Eterna 500T", "Superia Reala",
             "Natura 1600", "Agfa Vista 100", "T-Max 400", "Acros II 100"]
DS_POS = [("右下", "br"), ("左下", "bl"), ("右上", "tr"), ("左上", "tl")]
DS_COLORS = [("橙红", "#ff5a2a"), ("亮黄", "#ffb02e"), ("纯白", "#ffffff")]
STRIP_TONES_UI = [("黑", "#141414"), ("暗棕", "#1c1611"), ("米白", "#efe9dd")]
DE_MODES = [("滤色", "滤色"), ("正片叠底", "正片叠底"), ("叠加", "叠加"), ("强光", "强光")]
PAPERS = [("\u65e0\u7eb9\u7406", "\u65e0"), ("\u7ec6\u68c9\u7eb8", "\u7ec6\u68c9\u7eb9"), ("\u624b\u5de5\u7eb8", "\u7c97\u7eb9\u7eb8"), ("\u753b\u5e03", "\u753b\u5e03")]
PAPER_GUIDE = {"\u65e0": "\u4fdd\u6301\u5e72\u51c0\u7559\u767d\uff0c\u9002\u5408\u73b0\u4ee3\u6781\u7b80\u76f8\u6846\u3002", "\u7ec6\u68c9\u7eb9": "\u7ec6\u5bc6\u67d4\u548c\u7684\u68c9\u7ea4\u7ef4\uff0c\u9002\u5408\u4eba\u50cf\u4e0e\u65e5\u5e38\u7167\u7247\u3002", "\u7c97\u7eb9\u7eb8": "\u53ef\u89c1\u624b\u5de5\u7ea4\u7ef4\u4e0e\u538b\u7eb9\uff0c\u9002\u5408\u590d\u53e4\u76f8\u7eb8\u548c\u827a\u672f\u5370\u5237\u3002", "\u753b\u5e03": "\u5747\u5300\u7ec7\u7ebf\u7eb9\u7406\uff0c\u589e\u52a0\u5e03\u9762\u5370\u5237\u7684\u89c2\u611f\u3002"}
TONE_CHIPS = [("默认", ""), ("纯白", "#ffffff"), ("暖白", "#fbf8f1"),
              ("米黄", "#f7f0e2"), ("冷灰", "#f1f2f4"), ("黑卡", "#262626")]
LEAK_TINTS = [("琥珀", "#ff9a5a"), ("品红", "#ff5c8a"), ("冰蓝", "#7ad0ff")]
GRADS = [("关闭", "关闭"), ("线性", "线性"), ("径向", "径向")]
GDIRS = [("上→下", "上→下"), ("下→上", "下→上"), ("左→右", "左→右"), ("右→左", "右→左")]
TINTS = [("暖橙", "#ff7a50"), ("白光", "#ffffff"), ("冷青", "#7ad0ff")]



def resource_path(name):
    root = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(root, name)


def _riso_ink(win, idx):
    for b in getattr(win, "riso_btns", []):
        if b.isChecked():
            data = b.property("data")
            if isinstance(data, (tuple, list)) and len(data) == 2:
                return data[idx]
    return "#1f1c1a" if idx == 0 else "#ff5a4a"


def to_pixmap(im, box=None, outline=True):
    im = im.copy()
    if box:
        im.thumbnail(box, Image.LANCZOS)
    if im.mode != "RGB":
        im = im.convert("RGB")
    if outline:
        bg = Image.new("RGB", (im.width + 2, im.height + 2), (208, 201, 191))
        bg.paste(im, (1, 1))
        im = bg
    q = QImage(im.tobytes("raw", "RGB"), im.width, im.height, im.width * 3,
               QImage.Format.Format_RGB888)
    return QPixmap.fromImage(q.copy())



def _paper_swatch(kind):
    size = (84, 54)
    if kind in ("", "\u65e0"):
        return Image.new("RGB", size, "#f5f3ec")
    return ImageOps.colorize(ImageOps.autocontrast(paper_texture(size, kind), cutoff=2),
                             black="#918879", white="#fffdf6")

QSS = """
QWidget{font-family:"Microsoft YaHei UI","Microsoft YaHei","Segoe UI";font-size:13px;color:#292f2a}
QMainWindow,#root{background:#e5e7e2}
#root{background:#e5e7e2}
#title{font-size:22px;font-weight:700;color:#242a26}
#sub{color:#777d75;font-size:12px}
#hint,#previewMeta{color:#747a72;font-size:12px}
#sec{color:#626a60;font-size:12px;font-weight:700}
#count{color:#46534a;background:#efeee8;border:1px solid #dddacf;border-radius:11px;padding:6px 10px}
#footer{background:#f7f6f1;border:1px solid #d8d7cf;border-radius:14px}
#settingsShell{background:#f7f6f1;border:1px solid #d8d7cf;border-radius:16px}
#navPanel{background:#2c342f;border-radius:11px}
#navCaption{color:#aab2a8;font-size:10px;font-weight:700;letter-spacing:1px;padding:5px 8px}
#navButton{color:#e0e2dc;background:transparent;border:1px solid transparent;border-radius:8px;text-align:left;padding:9px 10px;font-weight:550}
#navButton:hover{background:#38423b}
#navButton:checked{color:#262c27;background:#e3dfd2;border-color:#a98450;font-weight:700}
#paperPanel{background:#fbfaf6;border:1px solid #e5e2d9;border-radius:12px}
#paperDesc{color:#515d53;font-size:12px;padding:2px 1px}
#paperNote{color:#72786f;font-size:11px;padding-top:2px}
#preview{background:#d5d8d2;border:1px solid #cdd0ca;border-radius:17px}
#drop{border:2px dashed #c9cec6;border-radius:16px;background:#f7f6f1;color:#828980}
#drop[hot="true"]{border-color:#8f7854;background:#f2efe6;color:#4c5148}
QPushButton{border:1px solid #deddd4;background:#fbfaf6;border-radius:9px;padding:8px 13px}
QPushButton:hover{background:#f2f0e8;border-color:#c8c2b2}
QPushButton:focus,QLineEdit:focus,QComboBox:focus{outline:0;border-color:#a98450}
QPushButton:disabled{color:#adb1a9;background:#f0f0eb;border-color:#e5e5dd}
QPushButton#primary{background:#313b34;border:0;color:#fff;font-weight:700;font-size:14px;border-radius:11px;padding:12px 24px}
QPushButton#primary:hover{background:#252d28}
QPushButton#primary:disabled{background:#c4c7bd;color:#fff}
QPushButton#chip{background:#f0efe9;border:1px solid transparent;border-radius:8px;padding:6px 9px;font-size:12px;color:#6d746b}
QPushButton#chip:hover{background:#e8e6dd}
QPushButton#chip:checked{background:#e8e2d4;border-color:#b69768;color:#3a4039;font-weight:650}
QToolButton#paperChip{background:#fbfaf6;border:1px solid #e4e0d5;border-radius:10px;padding:7px 6px;min-height:54px;text-align:left}
QToolButton#paperChip:hover{background:#f4f1e8;border-color:#cfc5af}
QToolButton#paperChip:checked{background:#eeeadf;border-color:#a98450;color:#303731;font-weight:650}
QPushButton#pager{background:#f2f0ea;border:1px solid #e2ded2;border-radius:7px;color:#4d554c;font-size:16px;padding:0}
QPushButton#pager:hover{background:#e9e6dc}
QPushButton#pager:disabled{color:#c3c6bf;background:#f6f4ef}
QLabel#pagerLbl{color:#7b837a;font-size:11px}
QPushButton#dir{background:#eeece5;border:1px solid transparent;border-radius:9px;padding:0;color:#686e64}
QPushButton#dir:checked{background:#313b34;color:#fff}
QComboBox{border:1px solid #deddd4;border-radius:9px;padding:7px 9px;background:#fbfaf6}
QComboBox::drop-down{border:0;width:18px}
QComboBox:disabled,QLineEdit:disabled{color:#adb1a9;background:#f0f0eb}
QLineEdit{border:1px solid #deddd4;border-radius:9px;padding:8px 10px;background:#fbfaf6}
QLineEdit:focus{border-color:#a98450}
QSlider::groove:horizontal{height:4px;background:#e1dfd6;border-radius:2px}
QSlider::handle:horizontal{width:14px;height:14px;margin:-5px 0;border-radius:7px;background:#8d7048}
QSlider::handle:horizontal:disabled{background:#c9cbc3}
QCheckBox{color:#4c554d;spacing:8px}
QCheckBox::indicator{width:17px;height:17px;border:1px solid #d0d1c8;border-radius:5px;background:#fff}
QCheckBox::indicator:checked{background:#465249;border-color:#465249}
QProgressBar{border:0;background:#e4e3db;border-radius:3px;max-height:6px;text-align:center;color:transparent}
QProgressBar::chunk{background:#8d7048;border-radius:3px}
QScrollArea{background:transparent;border:0}
QScrollBar:vertical{background:transparent;width:7px;margin:2px}
QScrollBar::handle:vertical{background:#d0d0c7;border-radius:3px;min-height:28px}
QScrollBar::add-line,QScrollBar::sub-line{height:0}
"""


class Preview(QWidget):
    """预览：滚轮缩放、按住拖动查看细节。"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("preview")
        self.pm = None
        self.hint = "拖入照片，或点击上方选择"
        self.zoom = 1.0
        self.pan = QPointF(0, 0)
        self._press = None
        self.setMinimumSize(320, 340)
        self.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
        self.setCursor(Qt.OpenHandCursor)
        self.setFocusPolicy(Qt.StrongFocus)

    def set_pixmap(self, pm):
        self.pm = pm
        self.zoom = 1.0
        self.pan = QPointF(0, 0)
        self.update()

    def clear(self):
        self.pm = None
        self.zoom = 1.0
        self.pan = QPointF(0, 0)
        self.update()

    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        p.setRenderHint(QPainter.SmoothPixmapTransform)
        if self.property("retro"):
            p.fillRect(self.rect(), QColor("#c0c0c0"))
            p.setPen(QPen(QColor("#808080"), 1))
            p.drawRect(self.rect().adjusted(0, 0, -1, -1))
            p.setPen(QPen(QColor("#ffffff"), 1))
            p.drawRect(self.rect().adjusted(1, 1, -2, -2))
        else:
            path = QPainterPath()
            path.addRoundedRect(QRectF(self.rect()).adjusted(0.5, 0.5, -0.5, -0.5), 18, 18)
            p.fillPath(path, QColor("#e8ece9"))
            p.setClipPath(path)
        if self.pm is None or self.pm.isNull():
            p.setPen(QColor("#a89f93"))
            p.drawText(self.rect(), Qt.AlignCenter, self.hint)
            return
        base = min(self.width() / self.pm.width(), self.height() / self.pm.height())
        sc = base * self.zoom
        w, h = self.pm.width() * sc, self.pm.height() * sc
        x = (self.width() - w) / 2 + self.pan.x()
        y = (self.height() - h) / 2 + self.pan.y()
        p.drawPixmap(QRectF(x, y, w, h), self.pm, QRectF(self.pm.rect()))
        if self.zoom < 1.02:
            p.setPen(QColor(90, 84, 78, 150))
            f = p.font()
            f.setPointSize(9)
            p.setFont(f)
            p.drawText(self.rect().adjusted(0, 0, -14, -10),
                       Qt.AlignRight | Qt.AlignBottom, "滚轮缩放 · 拖动查看")

    def wheelEvent(self, e):
        if self.pm is None:
            return
        step = 1.12 if e.angleDelta().y() > 0 else 1 / 1.12
        self.zoom = max(0.4, min(6.0, self.zoom * step))
        self.update()
        e.accept()

    def mousePressEvent(self, e):
        self.setFocus(Qt.MouseFocusReason)
        if self.pm is not None:
            self._press = e.position()
            self.setCursor(Qt.ClosedHandCursor)

    def mouseMoveEvent(self, e):
        if self._press is None:
            return
        self.pan += e.position() - self._press
        self._press = e.position()
        self.update()

    def mouseReleaseEvent(self, e):
        self._press = None
        self.setCursor(Qt.OpenHandCursor)
        self.setFocusPolicy(Qt.StrongFocus)


class DirPicker(QWidget):
    """3x3 圆点点阵选光源方向，不使用箭头字符。"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(126, 126)
        self.idx = 7
        self.setCursor(Qt.PointingHandCursor)

    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        p.setPen(Qt.NoPen)
        on = self.isEnabled()
        for i in range(9):
            cx, cy = 21 + (i % 3) * 42, 21 + (i // 3) * 42
            if i == self.idx and on:
                p.setBrush(QColor(47, 47, 47, 34))
                p.drawEllipse(cx - 16, cy - 16, 32, 32)
                p.setBrush(QColor("#2f2f2f"))
                p.drawEllipse(cx - 8, cy - 8, 16, 16)
            else:
                p.setBrush(QColor("#dedbd5") if on else QColor("#efedea"))
                r = 5 if on else 4
                p.drawEllipse(cx - r, cy - r, r * 2, r * 2)
        p.end()

    def mousePressEvent(self, e):
        if not self.isEnabled():
            return
        c = min(2, max(0, int(e.position().x() // 42)))
        r = min(2, max(0, int(e.position().y() // 42)))
        self.idx = r * 3 + c
        self.update()
        w = self.parent()
        while w is not None and not hasattr(w, "refresh_preview"):
            w = w.parent()
        if w is not None:
            w.refresh_preview()


class Worker(QThread):
    tick = Signal(int, int, str)
    done = Signal(int, int, str)

    def __init__(self, files, outdir, st):
        super().__init__()
        self.files, self.outdir, self.st = files, outdir, st

    def run(self):
        ok = bad = 0
        taken = set()
        os.makedirs(self.outdir, exist_ok=True)
        ext = ".png" if self.st.fmt == "png" else ".jpg"
        if (self.st.twin or self.st.collage) and len(self.files) > 1:
            self.tick.emit(1, 1, "正在合成…")
            try:
                imgs, exif = [], None
                for f in self.files:
                    with Image.open(f) as im:
                        if exif is None:
                            exif = read_exif(im)
                        imgs.append(ImageOps.exif_transpose(im).convert("RGB").copy())
                if self.st.twin:
                    big = twin_canvas(imgs[:2], self.st)
                    base = collage_name(self.outdir, ext, taken).replace("拼图_", "双图_")
                else:
                    big = collage(imgs, self.st.cols, self.st.gap, self.st.color)
                    base = collage_name(self.outdir, ext, taken)
                out = compose(big, self.st, exif)
                _save(out, base, self.st)
                ok = 1
            except Exception:
                bad = 1
            self.done.emit(ok, bad, self.outdir)
            return

        for i, f in enumerate(self.files, 1):
            self.tick.emit(i, len(self.files), os.path.basename(f))
            try:
                process_one(f, self.outdir, self.st, taken)
                ok += 1
            except Exception:
                bad += 1
        self.done.emit(ok, bad, self.outdir)


class CurveEdit(QWidget):
    """可拖动的曲线控件：左键加点/拖动，右键删点。"""
    changed = Signal()

    def __init__(self, pts=None, parent=None):
        super().__init__(parent)
        self.pts = sorted((float(x), float(y)) for x, y in (pts or [(0, 0), (255, 255)]))
        self.sel = None
        self.setMinimumSize(168, 168)
        self.setCursor(Qt.CrossCursor)

    def set_points(self, pts):
        self.pts = sorted((float(x), float(y)) for x, y in (pts or [(0, 0), (255, 255)]))
        self.sel = None
        self.update()

    def points(self):
        return [(int(round(x)), int(round(y))) for x, y in self.pts]

    def _box(self):
        m = 10
        return QRectF(m, m, max(20, self.width() - 2 * m), max(20, self.height() - 2 * m))

    def _pos(self, x, y):
        b = self._box()
        return QPointF(b.left() + x / 255.0 * b.width(),
                       b.bottom() - y / 255.0 * b.height())

    def _inv(self, pos):
        b = self._box()
        x = (pos.x() - b.left()) / b.width() * 255.0
        y = (b.bottom() - pos.y()) / b.height() * 255.0
        return max(0.0, min(255.0, x)), max(0.0, min(255.0, y))

    def _near(self, pos):
        for i, (x, y) in enumerate(self.pts):
            if (self._pos(x, y) - pos).manhattanLength() <= 12:
                return i
        return None

    def paintEvent(self, e):
        from core40 import curve_lut
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        p.fillRect(self.rect(), QColor("#f8f6f1"))
        b = self._box()
        p.setPen(QPen(QColor("#ddd8cc"), 1))
        for i in range(1, 4):
            x = b.left() + b.width() * i / 4.0
            y = b.top() + b.height() * i / 4.0
            p.drawLine(QPointF(x, b.top()), QPointF(x, b.bottom()))
            p.drawLine(QPointF(b.left(), y), QPointF(b.right(), y))
        p.setPen(QPen(QColor("#cfc9ba"), 1, Qt.DashLine))
        p.drawLine(b.bottomLeft(), b.topRight())
        p.setPen(QPen(QColor("#b9b2a2"), 1))
        p.drawRect(b)

        lut = curve_lut(self.points()) or list(range(256))
        path = QPainterPath()
        for i in range(256):
            pt = self._pos(i, lut[i])
            path.moveTo(pt) if i == 0 else path.lineTo(pt)
        p.setPen(QPen(QColor("#8d7048"), 2))
        p.drawPath(path)
        for i, (x, y) in enumerate(self.pts):
            c = self._pos(x, y)
            p.setPen(QPen(QColor("#6f5636"), 1))
            p.setBrush(QColor("#fffdf7") if i != self.sel else QColor("#8d7048"))
            p.drawRect(QRectF(c.x() - 3.5, c.y() - 3.5, 7, 7))

    def mousePressEvent(self, e):
        pos = e.position()
        if e.button() == Qt.RightButton:
            i = self._near(pos)
            if i not in (None, 0, len(self.pts) - 1) and len(self.pts) > 2:
                self.pts.pop(i)
                self.sel = None
                self.update()
                self.changed.emit()
            return
        i = self._near(pos)
        if i is None:
            x, y = self._inv(pos)
            self.pts.append((x, y))
            self.pts.sort()
            i = self.pts.index((x, y))
        self.sel = i
        self.update()

    def mouseMoveEvent(self, e):
        if self.sel is None:
            return
        x, y = self._inv(e.position())
        lo = self.pts[self.sel - 1][0] + 1 if self.sel > 0 else 0
        hi = self.pts[self.sel + 1][0] - 1 if self.sel < len(self.pts) - 1 else 255
        if self.sel == 0:
            x = 0
        elif self.sel == len(self.pts) - 1:
            x = 255
        else:
            x = max(lo, min(hi, x))
        self.pts[self.sel] = (x, y)
        self.update()

    def mouseReleaseEvent(self, e):
        if self.sel is not None:
            self.sel = None
            self.update()
            self.changed.emit()


class Main(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"{APP} · 暗房工作台")
        self.setWindowIcon(QIcon(resource_path("icon.ico")))
        self.resize(1180, 760)
        self.setMinimumSize(1040, 680)
        self.setAcceptDrops(True)
        self.files, self.worker, self.logo = [], None, ""
        self.split_files = []
        self.idx = 0
        self.film_names = list(FILM_LIST)
        self.theme = "win95"
        self.curves = {"m": [(0, 0), (255, 255)], "r": [(0, 0), (255, 255)],
                       "g": [(0, 0), (255, 255)], "b": [(0, 0), (255, 255)]}
        self.curve_ch = "m"
        self._load_saved_xmp()
        self._preview, self._thumbs, self._exif = None, [], {}
        self.color, self.line_color = "#ffffff", "#111111"
        self.leak_seed = 7
        self.torn_seed = 11
        self.de_path = ""
        self._last_pic = None
        self._preview_timer = QTimer(self)
        self._preview_timer.setSingleShot(True)
        self._preview_timer.setInterval(75)
        self._preview_timer.timeout.connect(self._render_preview)
        self._build()
        if self.theme == "win95":
            self.preview.setProperty("retro", True)

    def resizeEvent(self, e):
        super().resizeEvent(e)
        self._relayout_film()

    def showEvent(self, e):
        super().showEvent(e)
        self._relayout_film()

    def _relayout_film(self):
        """窗口变窄时胶片预设改单列，避免长片名被横向裁掉。"""
        if not getattr(self, "film_btns", None):
            return
        cols = 1 if self.width() < 1120 else 2
        if cols == self._film_cols:
            return
        self._film_cols = cols
        for b in self.film_btns:
            self.film_grid.removeWidget(b)
        for i, b in enumerate(self.film_btns):
            self.film_grid.addWidget(b, i // cols, i % cols)

    # ---------- 小部件 ----------
    def _chips(self, items, cb):
        box = QHBoxLayout()
        box.setSpacing(8)
        group = QButtonGroup(self)
        group.setExclusive(True)
        btns = []
        for i, (text, data) in enumerate(items):
            b = QPushButton(text, objectName="chip")
            b.setCheckable(True)
            b.setProperty("data", data)
            group.addButton(b, i)
            box.addWidget(b)
            btns.append(b)
        btns[0].setChecked(True)
        group.buttonClicked.connect(lambda _: cb())
        box.addStretch(1)
        return box, btns

    @staticmethod
    def _val(btns):
        for b in btns:
            if b.isChecked():
                return b.property("data")
        return None

    def _slider(self, label, lo, hi, val, suffix, cb, width=62):
        w = QWidget()
        h = QHBoxLayout(w)
        h.setContentsMargins(0, 0, 0, 0)
        h.setSpacing(10)
        lb = QLabel(label, objectName="hint")
        lb.setFixedWidth(width)
        s = QSlider(Qt.Horizontal)
        s.setRange(lo, hi)
        s.setValue(val)
        v = QLabel(f"{val}{suffix}", objectName="hint")
        v.setFixedWidth(46)
        v.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        s.valueChanged.connect(lambda x: (v.setText(f"{x}{suffix}"), cb()))
        h.addWidget(lb)
        h.addWidget(s, 1)
        h.addWidget(v)
        return w, s

    def _sec(self, text):
        lb = QLabel(text, objectName="sec")
        lb.setContentsMargins(0, 6, 0, 0)
        return lb

    # ---------- 界面 ----------
    def _build(self):
        root = QWidget(objectName="root")
        self.setCentralWidget(root)
        v = QVBoxLayout(root)
        v.setContentsMargins(24, 18, 24, 18)
        v.setSpacing(12)

        head = QHBoxLayout()
        head.setSpacing(12)
        mark = QLabel()
        mark.setObjectName("brandMark")
        mark.setFixedSize(40, 40)
        mark.setPixmap(QPixmap(resource_path("icon.png")).scaled(
            38, 38, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        head.addWidget(mark)
        ttl = QVBoxLayout()
        ttl.setSpacing(2)
        ttl.addWidget(QLabel(APP, objectName="title"))
        ttl.addWidget(QLabel("相框 · 纸面 · 胶片，本地处理", objectName="sub"))
        head.addLayout(ttl)
        head.addStretch(1)
        self.count = QLabel("未选择照片", objectName="count")
        head.addWidget(self.count)
        self.theme_btn = QPushButton("皮肤：95")
        self.theme_btn.setFixedWidth(96)
        self.theme_btn.clicked.connect(self.toggle_theme)
        head.addWidget(self.theme_btn)
        b1 = QPushButton("选择照片")
        b1.clicked.connect(self.pick_files)
        b2 = QPushButton("选择文件夹")
        b2.clicked.connect(self.pick_folder)
        b3 = QPushButton("清空")
        b3.clicked.connect(self.clear)
        head.addWidget(b1)
        head.addWidget(b2)
        head.addWidget(b3)
        v.addLayout(head)

        body = QHBoxLayout()
        body.setSpacing(14)

        # 左：类别导航与参数面板
        settings = QFrame(objectName="settingsShell")
        settings.setMinimumWidth(500)
        settings_row = QHBoxLayout(settings)
        settings_row.setContentsMargins(10, 10, 10, 10)
        settings_row.setSpacing(10)

        nav = QFrame(objectName="navPanel")
        nav.setFixedWidth(104)
        nav_v = QVBoxLayout(nav)
        nav_v.setContentsMargins(6, 8, 6, 8)
        nav_v.setSpacing(5)
        nav_v.addWidget(QLabel("\u7f16\u8f91", objectName="navCaption"))
        self.nav_group = QButtonGroup(self)
        self.nav_group.setExclusive(True)
        self.nav_buttons = []
        page_names = ["\u8fb9\u6846", "\u7eb8\u9762", "\u8272\u5f69", "\u80f6\u7247",
                      "\u5b57\u5e55", "\u521b\u610f", "\u753b\u5e03", "\u5206\u5272"]
        self.pages = QStackedWidget()
        page_builders = [self.page_frame, self.page_paper, self.page_grade, self.page_film,
                         self.page_text, self.page_creative, self.page_canvas,
                         self.page_split]
        for i, (name, build_page) in enumerate(zip(page_names, page_builders)):
            button = QPushButton(name, objectName="navButton")
            button.setCheckable(True)
            button.setMinimumHeight(39)
            self.nav_group.addButton(button, i)
            self.nav_buttons.append(button)
            nav_v.addWidget(button)
            button.clicked.connect(lambda checked=False, idx=i: self.pages.setCurrentIndex(idx))
            self.pages.addWidget(build_page())
        nav_v.addStretch(1)
        self.nav_buttons[0].setChecked(True)
        self.pages.currentChanged.connect(lambda _: self.refresh_preview())
        settings_row.addWidget(nav)
        settings_row.addWidget(self.pages, 1)
        body.addWidget(settings, 11)

        # 右：预览
        right = QVBoxLayout()
        right.setSpacing(6)
        self.preview = Preview()
        right.addWidget(self.preview, 1)

        pager = QHBoxLayout()
        pager.setSpacing(6)
        self.prev_btn = QPushButton("<", objectName="pager")
        self.prev_btn.setFixedSize(30, 24)
        self.prev_btn.setToolTip("\u4e0a\u4e00\u5f20\uff08\u2190\uff09")
        self.prev_btn.clicked.connect(lambda: self.goto(-1))
        self.page_lbl = QLabel("\u2014 / \u2014", objectName="pagerLbl")
        self.page_lbl.setAlignment(Qt.AlignCenter)
        self.page_lbl.setMinimumWidth(88)
        self.next_btn = QPushButton(">", objectName="pager")
        self.next_btn.setFixedSize(30, 24)
        self.next_btn.setToolTip("\u4e0b\u4e00\u5f20\uff08\u2192\uff09")
        self.next_btn.clicked.connect(lambda: self.goto(1))
        self.file_lbl = QLabel("", objectName="pagerLbl")
        self.file_lbl.setAlignment(Qt.AlignCenter)
        self.file_lbl.setMinimumWidth(120)
        pager.addStretch(1)
        pager.addWidget(self.prev_btn)
        pager.addWidget(self.page_lbl)
        pager.addWidget(self.next_btn)
        pager.addSpacing(8)
        pager.addWidget(self.file_lbl)
        pager.addStretch(1)
        right.addLayout(pager)

        for key, delta in ((Qt.Key_Left, -1), (Qt.Key_Right, 1)):
            sc = QShortcut(QKeySequence(key), self.preview)
            sc.setContext(Qt.WidgetWithChildrenShortcut)
            sc.activated.connect(lambda d=delta: self.goto(d))
        self.exif_label = QLabel("预览：尚未导入照片", objectName="previewMeta")
        self.exif_label.setAlignment(Qt.AlignCenter)
        self.exif_label.setContentsMargins(8, 2, 8, 2)
        self.exif_label.setWordWrap(True)
        right.addWidget(self.exif_label)
        body.addLayout(right, 10)
        v.addLayout(body, 1)

        # 底部输出
        footer = QFrame(objectName="footer")
        foot = QHBoxLayout(footer)
        foot.setContentsMargins(12, 9, 12, 9)
        foot.setSpacing(9)
        self.custom_out = QCheckBox("另存到")
        self.custom_out.toggled.connect(self.on_custom_out)
        self.out_edit = QLineEdit()
        self.out_edit.setPlaceholderText("默认：照片目录 / 白边输出")
        self.out_edit.setReadOnly(True)
        self.out_edit.setEnabled(False)
        self.out_btn = QPushButton("浏览")
        self.out_btn.setFixedWidth(60)
        self.out_btn.clicked.connect(self.pick_out)
        self.out_btn.setEnabled(False)
        self.out_size = QComboBox()
        for t, d in [("原始尺寸", None), ("长边 2048", 2048), ("长边 1080", 1080)]:
            self.out_size.addItem(t, d)
        self.out_size.setFixedWidth(104)
        self.out_size.currentIndexChanged.connect(self.refresh_preview)
        self.fmt = QComboBox()
        self.fmt.addItems(["JPG", "PNG"])
        self.fmt.setFixedWidth(66)
        self.status = QLabel("准备就绪", objectName="hint")
        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setTextVisible(False)
        self.progress.setFixedWidth(150)
        self.start = QPushButton("导出照片", objectName="primary")
        self.start.setEnabled(False)
        self.start.clicked.connect(self.run)

        foot.addWidget(self.custom_out)
        foot.addWidget(self.out_edit, 1)
        foot.addWidget(self.out_btn)
        foot.addWidget(self.out_size)
        foot.addWidget(self.fmt)
        foot.addWidget(self.status)
        foot.addWidget(self.progress)
        foot.addWidget(self.start)
        v.addWidget(footer)

    # ---------- 相框页 ----------
    def page_frame(self):
        w = QWidget()
        outer = QVBoxLayout(w)
        outer.setContentsMargins(0, 0, 0, 0)
        area = QScrollArea()
        area.setWidgetResizable(True)
        area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        inner = QWidget()
        inner.setObjectName("scrollBody")
        inner.setStyleSheet("#scrollBody{background:transparent}")
        v = QVBoxLayout(inner)
        v.setContentsMargins(4, 8, 12, 8)
        v.setSpacing(10)

        v.addWidget(QLabel("边框样式", objectName="sec"))
        row, self.mode_btns = self._chips(MODES, self.on_mode)
        v.addLayout(row)

        hollow = QHBoxLayout()
        hollow.setSpacing(10)
        lb = QLabel("边框颜色", objectName="hint")
        lb.setFixedWidth(62)
        self.color_btn = QPushButton()
        self.color_btn.setFixedSize(44, 28)
        self.color_btn.clicked.connect(self.pick_color)
        self.paint_color()
        hollow.addWidget(lb)
        hollow.addWidget(self.color_btn)
        hollow.addStretch(1)
        v.addLayout(hollow)

        rw, self.pad_s = self._slider("边框宽度", 0, 20, 6, "%", self.refresh_preview)
        v.addWidget(rw)
        v.addWidget(QLabel("画布比例", objectName="hint"))
        row, self.ratio_btns = self._chips(RATIOS[:5], self.refresh_preview)
        v.addLayout(row)
        rr, self.radius = self._slider("圆角", 0, 100, 0, "", self.refresh_preview)
        v.addWidget(rr)

        v.addWidget(self._sec("细边线"))
        hz = QHBoxLayout()
        hz.setSpacing(10)
        self.line_on = QCheckBox("显示")
        self.line_on.toggled.connect(self.refresh_preview)
        self.line_btn = QPushButton()
        self.line_btn.setFixedSize(44, 28)
        self.line_btn.clicked.connect(self.pick_line_color)
        self.paint_line()
        hz.addWidget(self.line_on)
        hz.addWidget(self.line_btn)
        hz.addStretch(1)
        v.addLayout(hz)
        sl = self._slider("粗细", 0, 8, 2, "px", self.refresh_preview)
        self.line_w = sl[1]
        v.addWidget(sl[0])

        v.addWidget(self._sec("阴影"))
        hs = QHBoxLayout()
        self.sh_on = QCheckBox("显示")
        self.sh_on.toggled.connect(self.on_shadow)
        hs.addWidget(self.sh_on)
        hs.addStretch(1)
        v.addLayout(hs)

        self.dp = DirPicker(self)
        hd = QHBoxLayout()
        hd.addWidget(self.dp)
        hd.addStretch(1)
        v.addLayout(hd)
        r1, self.sh_pos = self._slider("位置", 0, 60, 18, "", self.refresh_preview)
        r2, self.sh_blur_s = self._slider("柔和度", 2, 80, 22, "", self.refresh_preview)
        r3, self.sh_str = self._slider("强度", 10, 255, 95, "", self.refresh_preview)
        for r in (r1, r2, r3):
            v.addWidget(r)
        self.sh_sliders = [self.sh_pos, self.sh_blur_s, self.sh_str]
        v.addStretch(1)
        self.on_shadow(False)
        area.setWidget(inner)
        outer.addWidget(area)
        return w

    # ---------- Paper surface page ----------
    def page_paper(self):
        w = QWidget()
        outer = QVBoxLayout(w)
        outer.setContentsMargins(0, 0, 0, 0)
        area = QScrollArea()
        area.setWidgetResizable(True)
        area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        inner = QWidget()
        inner.setObjectName("scrollBody")
        inner.setStyleSheet("#scrollBody{background:transparent}")
        v = QVBoxLayout(inner)
        v.setContentsMargins(18, 18, 18, 16)
        v.setSpacing(12)
        title = QLabel("\u7eb8\u9762\u4e0e\u7eb9\u7406", objectName="sec")
        title.setStyleSheet("font-size:15px;font-weight:700;color:#34483d")
        v.addWidget(title)
        intro = QLabel("\u9009\u62e9\u4e00\u79cd\u7eb8\u9762\u3002\u7eb9\u7406\u53ea\u4f5c\u7528\u4e8e\u7559\u767d\uff0c\u539f\u7247\u4fdd\u6301\u6e05\u6670\u3002")
        intro.setObjectName("hint")
        intro.setWordWrap(True)
        v.addWidget(intro)

        panel = QFrame()
        panel.setObjectName("paperPanel")
        pv = QVBoxLayout(panel)
        pv.setContentsMargins(14, 14, 14, 14)
        pv.setSpacing(10)
        pv.addWidget(self._sec("\u7eb8\u9762\u7c7b\u578b"))
        row = QGridLayout()
        row.setSpacing(6)
        self.paper_group = QButtonGroup(self)
        self.paper_group.setExclusive(True)
        self.paper_btns = []
        for i, (label, kind) in enumerate(PAPERS):
            button = QToolButton()
            button.setObjectName("paperChip")
            button.setCheckable(True)
            button.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
            button.setFixedHeight(82)
            button.setMinimumWidth(68)
            button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            button.setIconSize(QSize(52, 32))
            button.setIcon(QIcon(to_pixmap(_paper_swatch(kind), outline=False)))
            button.setText(label)
            button.setProperty("data", kind)
            button.setToolTip(label)
            self.paper_group.addButton(button, i)
            self.paper_btns.append(button)
            row.addWidget(button, i // 2, i % 2)
        row.setColumnStretch(0, 1)
        row.setColumnStretch(1, 1)
        self.paper_btns[0].setChecked(True)
        self.paper_group.buttonClicked.connect(lambda _: self.on_paper_change())
        pv.addLayout(row)
        self.paper_desc = QLabel(PAPER_GUIDE.get("无", ""), objectName="paperDesc")
        self.paper_desc.setWordWrap(True)
        pv.addWidget(self.paper_desc)
        pv.addWidget(self._sec("\u7eb9\u7406\u5f3a\u5ea6"))
        r, self.paper_amt = self._slider("\u8f7b\u67d4  \u2194  \u660e\u663e", 0, 100, 48, "", self.refresh_preview, width=96)
        pv.addWidget(r)
        self.paper_amt.setEnabled(False)
        amt_hint = QLabel("\u5f3a\u5ea6\u4ece\u7ec6\u815c\u7eb8\u611f\u5230\u66f4\u6e05\u6670\u7684\u7ea4\u7ef4\u808c\u7406\u3002")
        amt_hint.setObjectName("hint")
        pv.addWidget(amt_hint)
        v.addWidget(panel)

        tone_panel = QFrame()
        tone_panel.setObjectName("paperPanel")
        tv = QVBoxLayout(tone_panel)
        tv.setContentsMargins(14, 14, 14, 14)
        tv.setSpacing(10)
        tv.addWidget(self._sec("\u7eb8\u5f20\u5e95\u8272"))
        row = QGridLayout()
        row.setSpacing(6)
        self.tone_btns = []
        self.tone_group = QButtonGroup(self)
        self.tone_group.setExclusive(True)
        for i, (text, tone) in enumerate(TONE_CHIPS):
            b = QPushButton(text, objectName="chip")
            b.setCheckable(True)
            b.setProperty("data", tone)
            self.tone_group.addButton(b, i)
            row.addWidget(b, i // 3, i % 3)
            self.tone_btns.append(b)
        for _c in range(3):
            row.setColumnStretch(_c, 1)
        self.tone_btns[0].setChecked(True)
        self.tone_group.buttonClicked.connect(lambda _: self.refresh_preview())
        for (_, tone), button in zip(TONE_CHIPS, self.tone_btns):
            swatch = Image.new("RGB", (18, 18), tone or "#f5f3ec")
            ImageDraw.Draw(swatch).rectangle((0, 0, 17, 17), outline="#c9cec9")
            button.setIcon(QIcon(to_pixmap(swatch, outline=False)))
            button.setIconSize(QSize(14, 14))
        tv.addLayout(row)
        tone_hint = QLabel("\u7eb8\u8272\u4ec5\u5728\u7eaf\u8272\u8fb9\u6846\u6a21\u5f0f\u4e0b\u751f\u6548\u3002")
        tone_hint.setObjectName("hint")
        tone_hint.setWordWrap(True)
        tv.addWidget(tone_hint)
        v.addWidget(tone_panel)

        print_panel = QFrame()
        print_panel.setObjectName("paperPanel")
        rv = QVBoxLayout(print_panel)
        rv.setContentsMargins(14, 14, 14, 14)
        rv.setSpacing(8)
        rv.addWidget(self._sec("相纸冲印"))
        row, self.finish_btns = self._chips(FINISH_CHIPS, self.refresh_preview)
        rv.addLayout(row)
        r, self.cc_m = self._slider("品红滤色片", 0, 100, 0, "", self.refresh_preview, width=78)
        rv.addWidget(r)
        r, self.cc_y = self._slider("黄滤色片", 0, 100, 0, "", self.refresh_preview, width=78)
        rv.addWidget(r)
        cc_hint = QLabel("模拟放大机的 CC 滤色片：加品红偏洋红，加黄偏暖。")
        cc_hint.setObjectName("hint")
        cc_hint.setWordWrap(True)
        rv.addWidget(cc_hint)
        v.addWidget(print_panel)

        edge_panel = QFrame()
        edge_panel.setObjectName("paperPanel")
        ev = QVBoxLayout(edge_panel)
        ev.setContentsMargins(14, 14, 14, 14)
        ev.setSpacing(8)
        ev.addWidget(self._sec("\u5361\u7eb8\u538b\u8fb9"))
        r, self.recess = self._slider("\u9634\u5f71\u6df1\u5ea6", 0, 100, 0, "", self.refresh_preview, width=78)
        ev.addWidget(r)
        v.addWidget(edge_panel)
        v.addStretch(1)
        area.setWidget(inner)
        outer.addWidget(area)
        return w

    # ---------- 文本页 ----------
    def page_text(self):
        w = QWidget()
        v = QVBoxLayout(w)
        v.setContentsMargins(4, 8, 12, 8)
        v.setSpacing(10)

        hb = QHBoxLayout()
        self.bar_on = QCheckBox("显示相机参数")
        self.bar_on.toggled.connect(self.refresh_preview)
        self.logo_btn = QPushButton("品牌图标…")
        self.logo_btn.clicked.connect(self.pick_logo)
        hb.addWidget(self.bar_on)
        hb.addStretch(1)
        hb.addWidget(self.logo_btn)
        v.addLayout(hb)

        pre = QHBoxLayout()
        pre.setSpacing(8)
        self.cam_pre = QLineEdit()
        self.cam_pre.setPlaceholderText("相机名前缀，如 Shot on")
        self.lens_pre = QLineEdit()
        self.lens_pre.setPlaceholderText("镜头名前缀，如 SIGMA")
        for e in (self.cam_pre, self.lens_pre):
            e.textChanged.connect(self.refresh_preview)
        pre.addWidget(self.cam_pre)
        pre.addWidget(self.lens_pre)
        v.addLayout(pre)
        v.addWidget(QLabel("勾选要显示的字段，留空自动读 EXIF", objectName="hint"))

        area = QScrollArea()
        area.setWidgetResizable(True)
        area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        inner = QWidget()
        inner.setObjectName("scrollBody")
        inner.setStyleSheet("#scrollBody{background:transparent}")
        grid = QGridLayout(inner)
        grid.setContentsMargins(0, 0, 6, 0)
        grid.setHorizontalSpacing(12)
        grid.setVerticalSpacing(9)
        self.f_check, self.f_edit = {}, {}
        for i, (key, label) in enumerate(FIELD_DEFS):
            r, c = divmod(i, 2)
            cell = QWidget()
            cv = QVBoxLayout(cell)
            cv.setContentsMargins(0, 0, 0, 0)
            cv.setSpacing(3)
            top = QHBoxLayout()
            top.setSpacing(7)
            cb = QCheckBox(label)
            cb.setChecked(key in DEFAULT_ON)
            cb.toggled.connect(self.refresh_preview)
            ed = QLineEdit()
            ed.setPlaceholderText("自动")
            ed.textChanged.connect(self.refresh_preview)
            top.addWidget(cb)
            top.addStretch(1)
            cv.addLayout(top)
            cv.addWidget(ed)
            grid.addWidget(cell, r, c)
            self.f_check[key] = cb
            self.f_edit[key] = ed
        grid.setRowStretch(grid.rowCount(), 1)
        area.setWidget(inner)
        v.addWidget(area, 1)
        return w

    # ---------- 调色页 ----------
    def page_grade(self):
        w = QWidget()
        v = QVBoxLayout(w)
        v.setContentsMargins(4, 8, 12, 4)
        v.setSpacing(8)
        area = QScrollArea()
        area.setWidgetResizable(True)
        area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        inner = QWidget()
        inner.setObjectName("scrollBody")
        inner.setStyleSheet("#scrollBody{background:transparent}")
        iv = QVBoxLayout(inner)
        iv.setContentsMargins(0, 0, 6, 0)
        iv.setSpacing(8)
        row = QHBoxLayout()
        self.auto_btn = QPushButton("自动调色")
        self.auto_btn.clicked.connect(self.auto_grade)
        self.curve_reset = QPushButton("复位曲线")
        self.curve_reset.clicked.connect(self.reset_curve)
        row.addWidget(self.auto_btn)
        row.addWidget(self.curve_reset)
        row.addStretch(1)
        iv.addLayout(row)

        iv.addWidget(QLabel("曲线", objectName="sec"))
        self.curve = CurveEdit(self.curves["m"])
        self.curve.changed.connect(self.on_curve_changed)
        iv.addWidget(self.curve)
        rowc, self.curve_btns = self._chips(
            [("主", "m"), ("红", "r"), ("绿", "g"), ("蓝", "b")], self.on_curve_channel)
        iv.addLayout(rowc)

        self.g_sliders = {}
        for title, rows in GRADE_GROUPS:
            iv.addWidget(QLabel(title, objectName="sec"))
            grid = QGridLayout()
            grid.setHorizontalSpacing(18)
            grid.setVerticalSpacing(7)
            for i, (key, label) in enumerate(rows):
                cell = QWidget()
                cv = QVBoxLayout(cell)
                cv.setContentsMargins(0, 0, 0, 0)
                cv.setSpacing(1)
                top = QHBoxLayout()
                top.setSpacing(6)
                top.addWidget(QLabel(label, objectName="hint"))
                top.addStretch(1)
                num = QLabel("0", objectName="hint")
                num.setFixedWidth(34)
                num.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
                top.addWidget(num)
                sl = QSlider(Qt.Horizontal)
                sl.setRange(-100, 100)
                sl.valueChanged.connect(
                    lambda x, n=num: (n.setText(f"{x:+d}" if x else "0"), self.refresh_preview()))
                cv.addLayout(top)
                cv.addWidget(sl)
                grid.addWidget(cell, i // 2, i % 2)
                self.g_sliders[key] = sl
            iv.addLayout(grid)
        iv.addStretch(1)
        area.setWidget(inner)
        v.addWidget(area, 1)
        bt = QPushButton("重置全部调色")
        bt.clicked.connect(self.reset_grade)
        v.addWidget(bt)
        return w

    def reset_grade(self):
        for sl in self.g_sliders.values():
            sl.setValue(0)
        self.refresh_preview()

    # ---------- 胶片页（含漏光与光晕）----------
    def page_film(self):
        w = QWidget()
        v = QVBoxLayout(w)
        v.setContentsMargins(4, 8, 12, 4)
        v.setSpacing(6)
        area = QScrollArea()
        area.setWidgetResizable(True)
        area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        inner = QWidget()
        inner.setObjectName("scrollBody")
        inner.setStyleSheet("#scrollBody{background:transparent}")
        iv = QVBoxLayout(inner)
        iv.setContentsMargins(0, 0, 6, 0)
        iv.setSpacing(9)

        iv.addWidget(QLabel("胶片预设", objectName="sec"))
        hx = QHBoxLayout()
        self.xmp_btn = QPushButton("导入 XMP 预设…")
        self.xmp_btn.clicked.connect(self.import_xmp)
        hx.addWidget(self.xmp_btn)
        hx.addStretch(1)
        iv.addLayout(hx)
        self.xmp_info = QLabel("支持 Lightroom / Camera Raw 的 .xmp（曲线 + 饱和度 + 黑白）",
                               objectName="hint")
        self.xmp_info.setWordWrap(True)
        iv.addWidget(self.xmp_info)

        grid = QGridLayout()
        grid.setSpacing(7)
        self.film_group = QButtonGroup(self)
        self.film_group.setExclusive(True)
        self.film_btns = []
        self._film_cols = 2
        for i, name in enumerate(self.film_names):
            b = QPushButton(name, objectName="chip")
            b.setCheckable(True)
            self.film_group.addButton(b, i)
            grid.addWidget(b, i // 2, i % 2)
            self.film_btns.append(b)
        self.film_group.button(0).setChecked(True)
        self.film_group.buttonClicked.connect(lambda _: self.refresh_preview())
        iv.addLayout(grid)
        self.film_grid, self.film_area = grid, area


        iv.addWidget(QLabel("质感", objectName="sec"))
        r, self.f_strength = self._slider("强度", 0, 200, 100, "", self.refresh_preview)
        iv.addWidget(r)
        r, self.f_grain = self._slider("颗粒", 0, 100, 0, "", self.refresh_preview)
        iv.addWidget(r)
        r, self.f_vig = self._slider("暗角", 0, 100, 0, "", self.refresh_preview)
        iv.addWidget(r)
        r, self.f_fade = self._slider("褪色", 0, 100, 0, "", self.refresh_preview)
        iv.addWidget(r)
        r, self.f_roll = self._slider("高光滚降", 0, 100, 0, "", self.refresh_preview)
        iv.addWidget(r)

        iv.addWidget(QLabel("推冲 / 拉冲", objectName="sec"))
        row, self.push_btns = self._chips(PUSH_CHIPS, self.refresh_preview)
        iv.addLayout(row)
        iv.addWidget(QLabel("每档约 +0.13 反差、+5% 饱和，颗粒同步变粗", objectName="hint"))

        iv.addWidget(QLabel("随机漏光", objectName="sec"))
        r, self.leak_s = self._slider("强度", 0, 100, 0, "", self.refresh_preview)
        iv.addWidget(r)
        hb = QHBoxLayout()
        hb.setSpacing(8)
        self.leak_btn = QPushButton("换一种形态")
        self.leak_btn.clicked.connect(self.shuffle_leak)
        hb.addWidget(self.leak_btn)
        hb.addStretch(1)
        iv.addLayout(hb)
        row, self.leak_btns = self._chips(LEAK_TINTS, self.refresh_preview)
        iv.addLayout(row)

        iv.addWidget(QLabel("光晕 Halation / Glow", objectName="sec"))
        r, self.h_int = self._slider("强度", 0, 100, 0, "", self.refresh_preview)
        iv.addWidget(r)
        r, self.h_thr = self._slider("阈值", 120, 250, 200, "", self.refresh_preview)
        iv.addWidget(r)
        r, self.h_rad = self._slider("半径", 5, 80, 18, "", self.refresh_preview)
        iv.addWidget(r)
        r, self.h_glow = self._slider("柔光", 0, 100, 0, "", self.refresh_preview)
        iv.addWidget(r)
        iv.addWidget(QLabel("溢出颜色", objectName="hint"))
        row, self.tint_btns = self._chips(TINTS, self.refresh_preview)
        iv.addLayout(row)

        iv.addWidget(QLabel("导出 3D LUT", objectName="sec"))
        hx = QHBoxLayout()
        self.lut_btn = QPushButton("导出全部 .cube（33³）")
        self.lut_btn.clicked.connect(self.export_luts)
        hx.addWidget(self.lut_btn)
        hx.addStretch(1)
        iv.addLayout(hx)
        lut_tip = QLabel("一次烘焙全部胶片预设，可直接导入 Premiere / 达芬奇 / Photoshop。",
                         objectName="hint")
        lut_tip.setWordWrap(True)
        iv.addWidget(lut_tip)
        iv.addStretch(1)
        area.setWidget(inner)
        v.addWidget(area, 1)
        return w

    def export_luts(self):
        d = QFileDialog.getExistingDirectory(self, "选择 LUT 输出文件夹")
        if not d:
            return
        names = [n for n in FILM_LIST if n != "关闭"]
        self.status.setText("正在烘焙 3D LUT…")
        QApplication.processEvents()
        done = 0
        try:
            for n in names:
                fn = n.replace(" ", "_").replace("/", "-") + ".cube"
                export_cube(n, os.path.join(d, fn), 33)
                done += 1
                self.status.setText(f"烘焙中 {done}/{len(names)} · {n}")
                QApplication.processEvents()
        except Exception as e:
            QMessageBox.warning(self, APP, "导出失败：%s" % e)
            return
        self.status.setText(f"已导出 {done} 个 LUT")
        QMessageBox.information(
            self, APP,
            f"已导出 {done} 个 33×33×33 的 .cube 到：\n{d}\n\n"
            "可直接导入 Premiere / 达芬奇 / Photoshop / Affinity。")

    def shuffle_leak(self):
        import random as _r
        self.leak_seed = _r.randint(1, 9999)
        if self.leak_s.value() == 0:
            self.leak_s.setValue(45)
        self.refresh_preview()

    # ---------- 创意页 ----------
    def page_creative(self):
        w = QWidget()
        outer = QVBoxLayout(w)
        outer.setContentsMargins(0, 0, 0, 0)
        area = QScrollArea()
        area.setWidgetResizable(True)
        area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        inner = QWidget()
        inner.setObjectName("scrollBody")
        inner.setStyleSheet("#scrollBody{background:transparent}")
        v = QVBoxLayout(inner)
        v.setContentsMargins(4, 10, 12, 10)
        v.setSpacing(8)

        # 35mm 胶片条
        v.addWidget(QLabel("胶片片边", objectName="sec"))
        hz = QHBoxLayout()
        self.strip_on = QCheckBox("加胶片片边")
        self.strip_on.toggled.connect(lambda _: self.refresh_preview())
        hz.addWidget(self.strip_on)
        hz.addStretch(1)
        v.addLayout(hz)
        hf = QHBoxLayout()
        hf.setSpacing(8)
        hf.addWidget(QLabel("画幅", objectName="hint"))
        self.strip_fmt = QComboBox()
        for _name in STRIP_FORMATS:
            self.strip_fmt.addItem(_name, _name)
        self.strip_fmt.currentIndexChanged.connect(lambda _: self.refresh_preview())
        hf.addWidget(self.strip_fmt, 1)
        v.addLayout(hf)
        fmt_hint = QLabel("选定画幅后会按该规格居中裁切；120 系是背纸边，无过片孔。",
                          objectName="hint")
        fmt_hint.setWordWrap(True)
        v.addWidget(fmt_hint)
        rr, self.strip_h = self._slider("片边高度", 3, 14, 7, "%", self.refresh_preview)
        v.addWidget(rr)
        v.addWidget(QLabel("片边颜色", objectName="hint"))
        row, self.strip_tone_btns = self._chips(STRIP_TONES_UI, self.refresh_preview)
        v.addLayout(row)
        self.strip_label = QLineEdit()
        self.strip_label.setPlaceholderText("片边文字，如 KODAK 400TX")
        self.strip_label.textChanged.connect(self.refresh_preview)
        v.addWidget(self.strip_label)
        self.strip_no = QLineEdit()
        self.strip_no.setPlaceholderText("片号，如 24A")
        self.strip_no.textChanged.connect(self.refresh_preview)
        v.addWidget(self.strip_no)

        # 拍立得
        v.addWidget(QLabel("拍立得相纸", objectName="sec"))
        hp = QHBoxLayout()
        self.pola_on = QCheckBox("拍立得画框")
        self.pola_on.toggled.connect(lambda _: self.refresh_preview())
        hp.addWidget(self.pola_on)
        hp.addStretch(1)
        v.addLayout(hp)
        self.pola_title = QLineEdit()
        self.pola_title.setPlaceholderText("相纸下方的手写标题")
        self.pola_title.textChanged.connect(self.refresh_preview)
        v.addWidget(self.pola_title)

        # 双重曝光
        v.addWidget(QLabel("双重曝光", objectName="sec"))
        hd = QHBoxLayout()
        hd.setSpacing(8)
        self.de_btn = QPushButton("选择叠加图…")
        self.de_btn.clicked.connect(self.pick_overlay)
        self.de_clear = QPushButton("×")
        self.de_clear.setFixedWidth(34)
        self.de_clear.setToolTip("清除叠加图")
        self.de_clear.clicked.connect(self.clear_overlay)
        hd.addWidget(self.de_btn, 1)
        hd.addWidget(self.de_clear)
        v.addLayout(hd)
        row, self.de_btns = self._chips(DE_MODES, self.refresh_preview)
        v.addLayout(row)
        rd, self.de_amt = self._slider("混合强度", 0, 100, 0, "", self.refresh_preview)
        v.addWidget(rd)
        # 日期背印
        v.addWidget(QLabel("日期背印", objectName="sec"))
        hds = QHBoxLayout()
        self.ds_on = QCheckBox("显示日期")
        self.ds_on.toggled.connect(lambda _: self.refresh_preview())
        hds.addWidget(self.ds_on)
        hds.addStretch(1)
        v.addLayout(hds)
        self.ds_text = QLineEdit()
        self.ds_text.setPlaceholderText("如 26 10 18，留空取今天")
        self.ds_text.textChanged.connect(self.refresh_preview)
        v.addWidget(self.ds_text)
        row, self.ds_pos_btns = self._chips(DS_POS, self.refresh_preview)
        v.addLayout(row)
        r, self.ds_size = self._slider("字号", 1, 10, 4, "%", self.refresh_preview)
        v.addWidget(r)
        row, self.ds_color_btns = self._chips(DS_COLORS, self.refresh_preview)
        v.addLayout(row)

        # 撕纸边
        v.addWidget(QLabel("撕纸边", objectName="sec"))
        ht = QHBoxLayout()
        self.torn_btn = QPushButton("换一种毛边")
        self.torn_btn.clicked.connect(self.shuffle_torn)
        ht.addWidget(self.torn_btn)
        ht.addStretch(1)
        v.addLayout(ht)
        r, self.torn = self._slider("毛边幅度", 0, 100, 0, "", self.refresh_preview)
        v.addWidget(r)

        # 网点印刷
        v.addWidget(QLabel("网点印刷 Riso", objectName="sec"))
        self.riso_on = QCheckBox("启用双色网点")
        self.riso_on.toggled.connect(lambda _: self.refresh_preview())
        hp = QHBoxLayout()
        hp.addWidget(self.riso_on)
        hp.addStretch(1)
        v.addLayout(hp)
        gridi = QGridLayout()
        gridi.setSpacing(6)
        self.riso_btns = []
        self.riso_group = QButtonGroup(self)
        self.riso_group.setExclusive(True)
        for i, (label, pair) in enumerate(RISO_INKS):
            b = QPushButton(label, objectName="chip")
            b.setCheckable(True)
            b.setProperty("data", pair)
            self.riso_group.addButton(b, i)
            gridi.addWidget(b, i // 2, i % 2)
            self.riso_btns.append(b)
        gridi.setColumnStretch(0, 1)
        gridi.setColumnStretch(1, 1)
        self.riso_btns[0].setChecked(True)
        self.riso_group.buttonClicked.connect(lambda _: self.refresh_preview())
        v.addLayout(gridi)
        r, self.riso_cell = self._slider("网点大小", 4, 16, 7, "", self.refresh_preview)
        v.addWidget(r)
        r, self.riso_angle = self._slider("网屏角度", 0, 90, 45, "°", self.refresh_preview)
        v.addWidget(r)
        r, self.riso_amt = self._slider("强度", 0, 100, 75, "", self.refresh_preview)
        v.addWidget(r)

        tip = QLabel("胶片条按 35mm 规格生成过片孔与片边字；双重曝光会把叠加图与每张照片混合；"
                     "网点印刷按 45° 网屏把画面转成两色点阵。", objectName="hint")
        tip.setWordWrap(True)
        v.addWidget(tip)
        v.addStretch(1)
        area.setWidget(inner)
        outer.addWidget(area)
        return w

    def pick_overlay(self):
        f, _ = QFileDialog.getOpenFileName(self, "选择叠加图", "", "图片 (*.jpg *.jpeg *.png *.webp)")
        if f:
            self.de_path = f
            self.de_btn.setText("✓ 已选叠加图")
            if self.de_amt.value() == 0:
                self.de_amt.setValue(50)
            self.refresh_preview()

    def shuffle_torn(self):
        import random as _r
        self.torn_seed = _r.randint(1, 9999)
        if self.torn.value() == 0:
            self.torn.setValue(35)
        self.refresh_preview()

    def clear_overlay(self):
        self.de_path = ""
        self.de_btn.setText("选择叠加图…")
        self.refresh_preview()

    # ---------- 画布页 ----------
    def page_canvas(self):
        w = QWidget()
        v = QVBoxLayout(w)
        v.setContentsMargins(4, 8, 12, 8)
        v.setSpacing(10)

        v.addWidget(QLabel("多图排版", objectName="sec"))
        hz = QHBoxLayout()
        self.collage_on = QCheckBox("网格拼图")
        self.collage_on.toggled.connect(self.on_collage)
        self.twin_on = QCheckBox("双图画布")
        self.twin_on.toggled.connect(self.on_twin)
        hz.addWidget(self.collage_on)
        hz.addWidget(self.twin_on)
        hz.addStretch(1)
        v.addLayout(hz)

        hc = QHBoxLayout()
        hc.setSpacing(10)
        lb = QLabel("列数", objectName="hint")
        lb.setFixedWidth(62)
        self.cols_combo = QComboBox()
        for t, k in COLS:
            self.cols_combo.addItem(t, k)
        self.cols_combo.currentIndexChanged.connect(self.refresh_preview)
        hc.addWidget(lb)
        hc.addWidget(self.cols_combo)
        hc.addStretch(1)
        v.addLayout(hc)
        rg, self.gap_s = self._slider("间距", 0, 30, 18, "", self.on_gap)
        v.addWidget(rg)

        v.addWidget(self._sec("双图微调"))
        rt, self.twin_top_s = self._slider("上下占比", 25, 75, 54, "%", self.refresh_preview, 72)
        v.addWidget(rt)
        v.addWidget(QLabel("上图", objectName="hint"))
        self.t1 = []
        for lbl, lo, hi, val in [("缩放", 100, 220, 100), ("左右", -100, 100, 0),
                                 ("上下", -100, 100, 0)]:
            r, sl = self._slider(lbl, lo, hi, val, "", self.refresh_preview)
            v.addWidget(r)
            self.t1.append(sl)
        v.addWidget(QLabel("下图", objectName="hint"))
        self.t2 = []
        for lbl, lo, hi, val in [("缩放", 100, 220, 100), ("左右", -100, 100, 0),
                                 ("上下", -100, 100, 0)]:
            r, sl = self._slider(lbl, lo, hi, val, "", self.refresh_preview)
            v.addWidget(r)
            self.t2.append(sl)
        v.addStretch(1)
        self.on_collage(False)
        return w



    # ---------- 曲线 / 自动调色 ----------
    def on_curve_changed(self):
        self.curves[self.curve_ch] = self.curve.points()
        self.refresh_preview()

    def on_curve_channel(self):
        self.curves[self.curve_ch] = self.curve.points()
        data = self._val(self.curve_btns)
        if data:
            self.curve_ch = data
            self.curve.set_points(self.curves.get(data) or [(0, 0), (255, 255)])

    def reset_curve(self):
        self.curves[self.curve_ch] = [(0, 0), (255, 255)]
        self.curve.set_points(self.curves[self.curve_ch])
        self.refresh_preview()

    def auto_grade(self):
        from core40 import auto_params
        pic = None
        if self.files:
            try:
                with Image.open(self.files[self.idx]) as im:
                    pic = ImageOps.exif_transpose(im).convert("RGB")
            except Exception:
                pic = None
        pic = pic or self._preview
        if pic is None:
            return
        prm = auto_params(pic)
        for k, v in prm.items():
            if k in self.g_sliders:
                self.g_sliders[k].setValue(int(v))
        self.refresh_preview()

    def toggle_theme(self):
        self.theme = "win95" if self.theme == "modern" else "modern"
        self.theme_btn.setText("皮肤：95" if self.theme == "win95" else "皮肤：现代")
        QApplication.instance().setStyleSheet(QSS95 if self.theme == "win95" else QSS)
        self.preview.setProperty("retro", self.theme == "win95")
        self.preview.update()
        self.paint_color()
        self.paint_line()
        self._paint_split_prev()

    # ---------- XMP 预设 ----------
    def _load_saved_xmp(self):
        try:
            if not os.path.isdir(XMP_DIR):
                return
            for fn in sorted(os.listdir(XMP_DIR)):
                if not fn.lower().endswith(".xmp"):
                    continue
                pr = parse_xmp(os.path.join(XMP_DIR, fn))
                if not pr:
                    continue
                name = register_xmp(pr)
                if name not in self.film_names:
                    self.film_names.append(name)
        except Exception:
            pass

    def import_xmp(self):
        fs, _ = QFileDialog.getOpenFileNames(self, "导入 XMP 预设", "", "XMP (*.xmp)")
        if not fs:
            return
        ok = 0
        try:
            os.makedirs(XMP_DIR, exist_ok=True)
        except Exception:
            pass
        for f in fs:
            pr = parse_xmp(f)
            if not pr:
                continue
            name = register_xmp(pr)
            if name not in self.film_names:
                self.film_names.append(name)
            try:
                with open(f, "rb") as src, open(os.path.join(XMP_DIR, os.path.basename(f)), "wb") as dst:
                    dst.write(src.read())
            except Exception:
                pass
            ok += 1
        if not ok:
            QMessageBox.information(self, APP, "没有读到可用曲线，请确认是 Lightroom 预设。")
            return
        self.rebuild_film_grid()
        self.xmp_info.setText(f"已导入 {ok} 个预设，已加入胶片列表（存在 ~/.whiteframe_xmp）")

    def rebuild_film_grid(self):
        while self.film_grid.count():
            item = self.film_grid.takeAt(0)
            w = item.widget()
            if w is not None:
                w.setParent(None)
        for b in list(self.film_group.buttons()):
            self.film_group.removeButton(b)
        self.film_btns = []
        cols = self._film_cols
        for i, name in enumerate(self.film_names):
            b = QPushButton(name, objectName="chip")
            b.setCheckable(True)
            self.film_group.addButton(b, i)
            self.film_grid.addWidget(b, i // cols, i % cols)
            self.film_btns.append(b)
        if self.film_btns:
            self.film_btns[0].setChecked(True)
        self.film_group.buttonClicked.connect(lambda _: self.refresh_preview())
        self.refresh_preview()

    # ---------- 扫描条分割 ----------
    def page_split(self):
        w = QWidget()
        v = QVBoxLayout(w)
        v.setContentsMargins(4, 8, 12, 8)
        v.setSpacing(9)

        v.addWidget(QLabel("\u626b\u63cf\u80f6\u7247\u6761\uff0c\u81ea\u52a8\u5207\u6210\u5355\u5f20", objectName="sec"))
        tip = QLabel("\u5bfc\u5165\u626b\u63cf\u4eea\u4e00\u6b21\u626b\u51fa\u7684\u6574\u6761\u5e95\u7247\uff0c"
                     "\u7a0b\u5e8f\u6309\u753b\u5e45\u81ea\u52a8\u5207\u5f00\u3002"
                     "\u7247\u57fa\u95f4\u9699\u8d8a\u5e72\u51c0\uff0c\u5207\u5f97\u8d8a\u51c6\u3002")
        tip.setObjectName("hint")
        tip.setWordWrap(True)
        v.addWidget(tip)

        hb = QHBoxLayout()
        hb.setSpacing(8)
        self.split_pick = QPushButton("\u9009\u62e9\u626b\u63cf\u6761\u2026")
        self.split_pick.clicked.connect(self.pick_strips)
        self.split_clear = QPushButton("\u6e05\u7a7a")
        self.split_clear.clicked.connect(self.clear_strips)
        hb.addWidget(self.split_pick)
        hb.addWidget(self.split_clear)
        hb.addStretch(1)
        v.addLayout(hb)

        self.split_info = QLabel("\u5c1a\u672a\u9009\u62e9\u626b\u63cf\u6761", objectName="hint")
        self.split_info.setWordWrap(True)
        v.addWidget(self.split_info)

        hc = QHBoxLayout()
        hc.setSpacing(8)
        hc.addWidget(QLabel("\u753b\u5e45\u6570", objectName="hint"))
        self.sp_count = QComboBox()
        self.sp_count.addItem("\u81ea\u52a8\u68c0\u6d4b", 0)
        for _n in range(2, 9):
            self.sp_count.addItem(f"{_n} \u5f20", _n)
        self.sp_count.currentIndexChanged.connect(lambda _: self.refresh_split())
        hc.addWidget(self.sp_count, 1)
        v.addLayout(hc)

        r, self.sp_min = self._slider("\u6700\u5c0f\u753b\u5e45\u5bbd", 4, 40, 10, "%", self.refresh_split)
        v.addWidget(r)
        r, self.sp_sens = self._slider("\u5206\u5272\u7075\u654f\u5ea6", 0, 100, 50, "", self.refresh_split)
        v.addWidget(r)
        r, self.sp_pad = self._slider("\u4e0a\u4e0b\u5185\u7f29", 0, 15, 2, "%", self.refresh_split)
        v.addWidget(r)

        self.split_prev = QLabel(objectName="splitPrev")
        self.split_prev.setMinimumHeight(96)
        self.split_prev.setMaximumHeight(230)
        self.split_prev.setAlignment(Qt.AlignCenter)
        self._paint_split_prev()
        v.addWidget(self.split_prev, 1)

        self.split_raw = QCheckBox("\u539f\u6837\u8f93\u51fa\uff08\u4e0d\u52a0\u767d\u8fb9\uff0c\u76f4\u63a5\u5b58 PNG\uff09")
        self.split_raw.toggled.connect(self.on_split_raw)
        v.addWidget(self.split_raw)

        self.split_go = QPushButton("\u5206\u5272\u5e76\u52a0\u5165\u4efb\u52a1")
        self.split_go.clicked.connect(self.do_split)
        self.split_go.setEnabled(False)
        v.addWidget(self.split_go)
        return w

    def _ensure_outdir(self):
        base = os.path.dirname(os.path.abspath(self.split_files[0]))
        d = os.path.join(base, "\u5206\u5272\u8f93\u51fa")
        os.makedirs(d, exist_ok=True)
        return d

    def on_split_raw(self, on):
        self.split_go.setText("分割并直接导出" if on else "分割并加入任务")

    def pick_strips(self):
        fs, _ = QFileDialog.getOpenFileNames(
            self, "\u9009\u62e9\u626b\u63cf\u7684\u80f6\u7247\u6761", "",
            "\u56fe\u7247 (*.jpg *.jpeg *.png *.tif *.tiff *.bmp)")
        if not fs:
            return
        self.split_files = fs
        self.split_go.setEnabled(True)
        self.refresh_split()

    def clear_strips(self):
        self.split_files = []
        self.idx = 0
        self.film_names = list(FILM_LIST)
        self.theme = "win95"
        self.curves = {"m": [(0, 0), (255, 255)], "r": [(0, 0), (255, 255)],
                       "g": [(0, 0), (255, 255)], "b": [(0, 0), (255, 255)]}
        self.curve_ch = "m"
        self._load_saved_xmp()
        self.split_go.setEnabled(False)
        self.split_prev.clear()
        self.split_info.setText("\u5c1a\u672a\u9009\u62e9\u626b\u63cf\u6761")

    def refresh_split(self):
        if not getattr(self, "split_files", None):
            return
        path = self.split_files[0]
        try:
            with Image.open(path) as im:
                full = ImageOps.exif_transpose(im).convert("RGB")
                small = full.copy()
                small.thumbnail((1500, 1500), Image.LANCZOS)
            boxes = []
            cnt = self.sp_count.currentData() or 0
            from core40 import _down, _row_bands
            sw, sh, px = _down(small, 900)
            bands = _row_bands(sw, sh, px)
            ky = small.height / float(sh)
            for by0, by1 in (bands if len(bands) > 1 else [(0, sh)]):
                top, bot = int(by0 * ky), int(by1 * ky)
                sub = small.crop((0, top, small.width, bot))
                sub_boxes, _rot = strip_boxes(sub, self.sp_min.value(),
                                              self.sp_sens.value(), self.sp_pad.value(), cnt)
                boxes.extend([(a, b + top, c, d_ + top) for a, b, c, d_ in sub_boxes])
            rot = False
        except Exception as e:
            self.split_info.setText(f"\u8bfb\u53d6\u5931\u8d25\uff1a{e}")
            return
        shot = draw_strip_boxes(small, boxes, rot, 900)
        self.split_prev.setPixmap(to_pixmap(shot, (max(360, self.split_prev.width()), 240)))
        name = os.path.basename(path)
        extra = "" if boxes else "\uff08\u8c03\u5c0f\u6700\u5c0f\u753b\u5e45\u5bbd\u6216\u63d0\u9ad8\u7075\u654f\u5ea6\uff09"
        self.split_info.setText(f"{len(self.split_files)} \u6761 \u00b7 {name} "
                                f"\u68c0\u6d4b\u5230 {len(boxes)} \u5f20{extra}")

    def do_split(self):
        if not getattr(self, "split_files", None):
            return
        merged = self.collage_on.isChecked() or self.twin_on.isChecked()
        if merged:                     # 拼图/双图会把多张合成一张，与“每张独立”冲突
            self.collage_on.setChecked(False)
            self.twin_on.setChecked(False)
        raw = self.split_raw.isChecked()
        tmp = (self._ensure_outdir() if raw else tempfile.mkdtemp(prefix="wf_split_"))
        out, bad = [], 0
        for p in self.split_files:
            try:
                with Image.open(p) as im:
                    full = ImageOps.exif_transpose(im).convert("RGB")
                    pieces = split_sheet(full, self.sp_min.value(),
                                         self.sp_sens.value(), self.sp_pad.value(),
                                         self.sp_count.currentData() or 0)
            except Exception:
                bad += 1
                continue
            stem = os.path.splitext(os.path.basename(p))[0]
            for i, pc in enumerate(pieces, 1):
                fp = os.path.join(tmp, f"{stem}_{i:02d}.png")
                pc.save(fp, "PNG", optimize=True)   # 中间件一律无损，避免二次压缩
                out.append(fp)
        if not out:
            QMessageBox.information(self, APP, "\u6ca1\u6709\u68c0\u6d4b\u5230\u53ef\u7528\u753b\u5e45\u3002")
            return
        if raw:
            self.split_info.setText(f"已切出 {len(out)} 张，原样 PNG 已存到：{tmp}")
            return
        if not self.custom_out.isChecked():
            base = os.path.dirname(os.path.abspath(self.split_files[0]))
            self.out_edit.setText(os.path.join(base, SKIP_DIR))
            self.custom_out.setChecked(True)   # 输出落到扫描条旁的「白边输出」
        first = out[0]
        self.add(list(self.files) + out)       # 追加，不清空已导入的照片
        if first in self.files:
            self.idx = self.files.index(first)
            self._show_current()
        msg = f"\u5df2\u5207\u51fa {len(out)} \u5f20\uff0c\u5df2\u52a0\u5165\u4efb\u52a1"
        if merged:
            msg += "；已关闭拼图/双图，保证逐张独立导出"
        if bad:
            msg += f"\uff08{bad} \u6761\u8bfb\u53d6\u5931\u8d25\uff09"
        self.split_info.setText(msg)

    # ---------- 状态 ----------
    def _flat(self):
        return getattr(self, "theme", "modern") == "win95"

    def _swatch_qss(self, color):
        if self._flat():
            return (f"background:{color};border:2px solid;"
                    "border-color:#808080 #ffffff #ffffff #808080")
        return f"background:{color};border:1px solid #e0d8cc;border-radius:9px"

    def paint_color(self):
        self.color_btn.setStyleSheet(self._swatch_qss(self.color))

    def paint_line(self):
        self.line_btn.setStyleSheet(self._swatch_qss(self.line_color))

    def _paint_split_prev(self):
        if self._flat():
            self.split_prev.setStyleSheet(
                "background:#ffffff;border:2px solid;"
                "border-color:#808080 #ffffff #ffffff #808080")
        else:
            self.split_prev.setStyleSheet(
                "background:#f4f2ec;border:1px solid #e2ded2;border-radius:10px")

    def on_mode(self):
        solid = self._val(self.mode_btns) == "solid"
        self.color_btn.setEnabled(solid)
        for button in getattr(self, "tone_btns", []):
            button.setEnabled(solid)
        self.refresh_preview()

    def on_shadow(self, on):
        self.sh_on.setChecked(on)
        self.dp.setEnabled(on)
        for s in self.sh_sliders:
            s.setEnabled(on)
        self.refresh_preview()

    def on_collage(self, on):
        self.collage_on.setChecked(on)
        if on and self.twin_on.isChecked():
            self.twin_on.setChecked(False)
        self.cols_combo.setEnabled(on)
        self.refresh_preview()

    def on_twin(self, on):
        self.twin_on.setChecked(on)
        if on and self.collage_on.isChecked():
            self.collage_on.setChecked(False)
        self.refresh_preview()

    def on_gap(self):
        self.refresh_preview()

    def on_custom_out(self, on):
        self.out_edit.setEnabled(on)
        self.out_btn.setEnabled(on)
        if on and not self.out_edit.text():
            d = QFileDialog.getExistingDirectory(self, "选择输出文件夹")
            if d:
                self.out_edit.setText(d)

    # ---------- 文件 ----------
    def pick_files(self):
        fs, _ = QFileDialog.getOpenFileNames(
            self, "选择照片", "", "图片 (*.jpg *.jpeg *.png *.webp *.bmp *.tif *.tiff)")
        if fs:
            self.add(fs)

    def pick_folder(self):
        d = QFileDialog.getExistingDirectory(self, "选择照片文件夹")
        if d:
            self.add([d])

    def pick_out(self):
        d = QFileDialog.getExistingDirectory(self, "选择输出文件夹")
        if d:
            self.out_edit.setText(d)

    def pick_color(self):
        c = QColorDialog.getColor(QColor(self.color), self, "边框颜色")
        if c.isValid():
            self.color = c.name()
            self.paint_color()
            self.refresh_preview()

    def pick_line_color(self):
        c = QColorDialog.getColor(QColor(self.line_color), self, "边线颜色")
        if c.isValid():
            self.line_color = c.name()
            self.paint_line()
            self.refresh_preview()

    def pick_logo(self):
        f, _ = QFileDialog.getOpenFileName(self, "品牌图标（建议透明底 PNG）", "",
                                           "图片 (*.png *.jpg *.jpeg *.webp)")
        if f:
            self.logo = f
            self.logo_btn.setText("✓ 已选图标")
            self.refresh_preview()

    def add(self, paths):
        found = collect(paths)
        if not found:
            QMessageBox.information(self, APP, "没有找到可处理的图片。")
            return
        self.files = found
        self.count.setText(f"{len(found)} 张")
        self.start.setEnabled(True)
        self.start.setText(f"导出 {len(found)} 张")
        self.status.setText("准备就绪")
        self.load_preview(found)

    def clear(self):
        self.files, self._preview, self._thumbs, self._exif = [], None, [], {}
        self.count.setText("未选择照片")
        self.start.setEnabled(False)
        self.start.setText("导出照片")
        self.progress.setValue(0)
        self.status.setText("准备就绪")
        self.preview.clear()
        self.idx = 0
        self._update_pager()
        self.exif_label.setText("预览：尚未导入照片")

    def load_preview(self, paths, idx=0):
        self._preview, self._thumbs, self._exif = None, [], {}
        self.idx = max(0, min(int(idx), len(paths) - 1)) if paths else 0
        try:
            with Image.open(paths[self.idx]) as im:
                im.load()
                self._exif = read_exif(im)
                self._preview = im.copy()
        except Exception:
            pass
        for p in paths[:9]:
            try:
                with Image.open(p) as im:
                    im.thumbnail((420, 420), Image.LANCZOS)
                    self._thumbs.append(im.convert("RGB").copy())
            except Exception:
                pass
        self.refresh_placeholders()
        self.update_exif_label()
        self.refresh_preview()
        self._update_pager()

    def _update_pager(self):
        n = len(self.files)
        if not n:
            self.page_lbl.setText("\u2014 / \u2014")
            self.file_lbl.setText("")
            self.prev_btn.setEnabled(False)
            self.next_btn.setEnabled(False)
            return
        self.idx = max(0, min(self.idx, n - 1))
        self.page_lbl.setText(f"{self.idx + 1} / {n}")
        self.file_lbl.setText(os.path.basename(self.files[self.idx])[:22])
        self.prev_btn.setEnabled(n > 1)
        self.next_btn.setEnabled(n > 1)

    def goto(self, delta):
        if not self.files:
            return
        n = len(self.files)
        self.idx = (self.idx + delta) % n
        self._show_current()

    def _show_current(self):
        if not self.files:
            return
        self.idx = max(0, min(self.idx, len(self.files) - 1))
        try:
            with Image.open(self.files[self.idx]) as im:
                im.load()
                self._exif = read_exif(im)
                self._preview = im.copy()
        except Exception:
            return
        self.refresh_placeholders()
        self.update_exif_label()
        self.refresh_preview()
        self._update_pager()

    def refresh_placeholders(self):
        for key, ed in self.f_edit.items():
            auto = field_auto(key, self._exif)
            ed.setPlaceholderText(auto or "自动")

    def update_exif_label(self):
        d = self._exif or {}
        if not (d.get("make") or d.get("model") or d.get("lens")):
            self.exif_label.setText("无 EXIF 信息，可在「文本」页手动填写型号与参数")
            return
        bits = [d.get("model") or d.get("make")]
        if d.get("lens"):
            bits.append(d["lens"])
        if d.get("fnum"):
            bits.append(f"F{float(d['fnum']):g}")
        self.exif_label.setText(" · ".join(bits))

    # ---------- 参数 ----------
    def style(self):
        return Style(
            mode=self._val(self.mode_btns) or "solid",
            color=self.color,
            # 胶片片边自带画幅边界，留白会变成片框里的白条
            pad=0.0 if self.strip_on.isChecked() else self.pad_s.value() / 100.0,
            ratio=self._val(self.ratio_btns),
            max_side=self.out_size.currentData(),
            fmt="png" if self.fmt.currentIndex() == 1 else "jpg",
            line=(self.line_w.value() / 1000.0) if self.line_on.isChecked() else 0.0,
            line_color=self.line_color,
            shadow=self.sh_on.isChecked(),
            sh_dir=self.dp.idx,
            sh_dist=(self.sh_sliders[0].value() / 1000.0) if self.sh_sliders else 0.018,
            sh_blur=(self.sh_sliders[1].value() / 1000.0) if self.sh_sliders else 0.022,
            sh_strength=self.sh_sliders[2].value() if self.sh_sliders else 95,
            bar=self.bar_on.isChecked(),
            logo=self.logo,
            cam_prefix=self.cam_pre.text(),
            lens_prefix=self.lens_pre.text(),
            fields={k: e.text() for k, e in self.f_edit.items()},
            enabled={k: c.isChecked() for k, c in self.f_check.items()},
            grade={k: v.value() for k, v in self.g_sliders.items()},
            curve_m=self.curves.get("m"),
            curve_r=self.curves.get("r"),
            curve_g=self.curves.get("g"),
            curve_b=self.curves.get("b"),
            leak=self.leak_s.value(),
            leak_seed=self.leak_seed,
            leak_tint=self._val(self.leak_btns) or "#ff9a5a",
            paper=self._val(self.paper_btns) or "无",
            paper_amt=self.paper_amt.value(),
            paper_tone=self._val(self.tone_btns) or "",
            recess=self.recess.value(),
            film=(self.film_names[self.film_group.checkedId()]
                  if 0 <= self.film_group.checkedId() < len(self.film_names) else "关闭"),
            film_strength=self.f_strength.value(),
            radius=self.radius.value(),
            polaroid=self.pola_on.isChecked(),
            polaroid_title=self.pola_title.text(),
            ds_on=self.ds_on.isChecked(),
            ds_text=self.ds_text.text(),
            ds_size=self.ds_size.value(),
            ds_color=self._val(self.ds_color_btns) or "#ff5a2a",
            ds_pos=self._val(self.ds_pos_btns) or "br",
            torn=self.torn.value(),
            torn_seed=self.torn_seed,
            riso_on=self.riso_on.isChecked(),
            riso_cell=self.riso_cell.value(),
            riso_angle=self.riso_angle.value(),
            riso_ink1=_riso_ink(self, 0),
            riso_ink2=_riso_ink(self, 1),
            riso_amt=self.riso_amt.value(),
            de_image=self.de_path,
            de_mode=self._val(self.de_btns) or "滤色",
            de_amt=self.de_amt.value(),
            strip=self.strip_on.isChecked(),
            strip_h=self.strip_h.value(),
            strip_tone=self._val(self.strip_tone_btns) or "#141414",
            strip_fmt=self.strip_fmt.currentData() or "135 全画幅",
            strip_label=self.strip_label.text() or "KODAK 400",
            strip_no=self.strip_no.text(),
            push=int(self._val(self.push_btns) or 0),
            paper_finish=self._val(self.finish_btns) or "光面",
            cc_m=self.cc_m.value(),
            cc_y=self.cc_y.value(),
            film_grain=self.f_grain.value(),
            film_vig=self.f_vig.value(),
            film_fade=self.f_fade.value(),
            film_roll=self.f_roll.value(),
            halo=self.h_int.value(),
            halo_thr=self.h_thr.value(),
            halo_radius=self.h_rad.value() / 1000.0,
            halo_tint=self._val(self.tint_btns) or "#ff7a50",
            glow=self.h_glow.value(),
            collage=self.collage_on.isChecked(),
            twin=self.twin_on.isChecked(),
            cols=self.cols_combo.currentData() or 0,
            gap=self.gap_s.value() / 1000.0,
            twin_top=self.twin_top_s.value() / 100.0,
            twin_zoom=(self.t1[0].value() / 100.0, self.t2[0].value() / 100.0),
            twin_px=(self.t1[1].value() / 100.0, self.t2[1].value() / 100.0),
            twin_py=(self.t1[2].value() / 100.0, self.t2[2].value() / 100.0),
        )

    def on_paper_change(self):
        kind = self._val(self.paper_btns) or "无"
        self.paper_desc.setText(PAPER_GUIDE.get(kind, PAPER_GUIDE["无"]))
        self.paper_amt.setEnabled(kind != "\u65e0")
        self.refresh_preview()

    def refresh_preview(self, *args):
        self._preview_timer.start()

    def _render_preview(self):
        if self._preview is None and not self._thumbs:
            return
        st = self.style()
        try:
            if st.twin and len(self._thumbs) > 1:
                pic = compose(twin_canvas(self._thumbs[:2], st), st, self._exif)
            elif st.collage and len(self._thumbs) > 1:
                big = collage(self._thumbs, st.cols, st.gap, st.color, cell=400)
                pic = compose(big, st, self._exif)
            elif self._preview is not None:
                im = self._preview.copy()
                im.thumbnail((900, 900), Image.LANCZOS)
                pic = compose(im, st, self._exif)
            else:
                return
            self.preview.set_pixmap(to_pixmap(pic, (1100, 1200)))
        except Exception as e:
            self.preview.setText(f"预览失败：{e}")

    # ---------- 执行 ----------
    def run(self):
        if not self.files:
            return
        outdir = (self.out_edit.text() if self.custom_out.isChecked() and self.out_edit.text()
                  else os.path.join(os.path.dirname(self.files[0]), SKIP_DIR))
        self.start.setEnabled(False)
        self.progress.setValue(0)
        self.worker = Worker(self.files, outdir, self.style())
        self.worker.tick.connect(self.on_tick)
        self.worker.done.connect(self.on_done)
        self.worker.start()

    def on_tick(self, i, total, name):
        self.progress.setValue(int(i / total * 100))
        self.status.setText(f"{i}/{total} · {name[:14]}")

    def on_done(self, ok, bad, outdir):
        self.start.setEnabled(True)
        self.start.setText(f"导出 {len(self.files)} 张")
        self.status.setText(f"完成：{ok} 张" + (f"，失败 {bad}" if bad else ""))
        box = QMessageBox(self)
        box.setWindowTitle(APP)
        box.setText(f"处理完成：成功 {ok} 张" + (f"，失败 {bad} 张" if bad else ""))
        box.setInformativeText(f"输出目录：\n{outdir}")
        open_btn = box.addButton("打开文件夹", QMessageBox.ActionRole)
        box.addButton("关闭", QMessageBox.AcceptRole)
        box.exec()
        if box.clickedButton() is open_btn:
            try:
                os.startfile(outdir)
            except Exception:
                pass

    # ---------- 拖放 ----------
    def _hot(self, on):
        self.preview.setProperty("hot", on)

    def dragEnterEvent(self, e):
        if e.mimeData().hasUrls():
            e.acceptProposedAction()

    def dropEvent(self, e):
        paths = [u.toLocalFile() for u in e.mimeData().urls()]
        if paths:
            self.add(paths)


def _log_error():
    import traceback
    base = (os.path.dirname(sys.executable) if getattr(sys, "frozen", False)
            else os.path.dirname(os.path.abspath(__file__)))
    try:
        with open(os.path.join(base, "error.log"), "a", encoding="utf-8") as f:
            f.write(traceback.format_exc() + "\n")
    except Exception:
        pass


QSS95 = """
* { font-family: "MS Sans Serif", "SimSun", "Microsoft YaHei", sans-serif; }
QMainWindow, QWidget { background:#c0c0c0; }
QLabel { color:#000000; background:transparent; }
QLabel#title { color:#000080; font-size:15px; font-weight:700; }
QLabel#sub, QLabel#hint, QLabel#previewMeta { color:#3a3a3a; font-size:11px; }
QLabel#sec { color:#000080; font-weight:700; }
QLabel#count { color:#000000; }
QFrame#settingsShell, QFrame#navPanel, QFrame#paperPanel, QFrame#footer {
    background:#c0c0c0; border:2px solid; border-color:#ffffff #808080 #808080 #ffffff;
    border-radius:0;
}
QWidget#scrollBody { background:transparent; }
QPushButton {
    background:#c0c0c0; color:#000000; border:2px solid;
    border-color:#ffffff #808080 #808080 #ffffff;
    border-radius:0; padding:4px 8px; min-height:14px;
}
QPushButton:hover { background:#cacaca; }
QPushButton:pressed { border-color:#808080 #ffffff #ffffff #808080; padding:5px 7px 3px 9px; }
QPushButton:disabled { color:#808080; }
QPushButton#navButton {
    background:#c0c0c0; border:2px solid transparent; text-align:left; padding:5px 8px;
}
QPushButton#navButton:checked {
    border-color:#808080 #ffffff #ffffff #808080; background:#d6d3ce; font-weight:700;
}
QPushButton#chip {
    background:#c0c0c0; color:#000000; border:2px solid;
    border-color:#ffffff #808080 #808080 #ffffff; border-radius:0;
}
QPushButton#chip:checked {
    background:#000080; color:#ffffff; border-color:#808080 #404040 #404040 #808080;
}
QPushButton#pager { background:#c0c0c0; border:2px solid; border-color:#ffffff #808080 #808080 #ffffff; }
QLabel#pagerLbl { color:#000000; }
QLineEdit, QComboBox {
    background:#ffffff; color:#000000; border:2px solid;
    border-color:#808080 #ffffff #ffffff #808080; padding:3px; border-radius:0;
}
QComboBox::drop-down { border:0; width:16px; background:#c0c0c0; }
QCheckBox { color:#000000; }
QSlider::groove:horizontal { height:4px; background:#808080; border:1px solid #404040; }
QSlider::handle:horizontal {
    width:11px; height:18px; margin:-8px 0; background:#c0c0c0; border:2px solid;
    border-color:#ffffff #404040 #404040 #ffffff;
}
QProgressBar { border:2px solid; border-color:#808080 #ffffff #ffffff #808080;
               background:#ffffff; text-align:center; color:#000; }
QProgressBar::chunk { background:#000080; }
QScrollArea { border:2px solid; border-color:#808080 #ffffff #ffffff #808080; }
QScrollBar:vertical { background:#c0c0c0; width:16px; }
QScrollBar::handle:vertical { background:#c0c0c0; border:2px solid;
                              border-color:#ffffff #404040 #404040 #ffffff; min-height:24px; }
QScrollBar::add-line, QScrollBar::sub-line { height:0; }
QToolButton#paperChip { background:#c0c0c0; border:2px solid;
                        border-color:#ffffff #808080 #808080 #ffffff; }
QToolButton#paperChip:checked { background:#000080; color:#ffffff; }
QWidget#preview { background:#ffffff; border:2px solid;
                  border-color:#808080 #ffffff #ffffff #808080; }
"""


def main():
    _bootlog("main enter")
    try:
        QApplication.setHighDpiScaleFactorRoundingPolicy(
            Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)
        app = QApplication(sys.argv)
        _ico = resource_path("icon.ico")
        if os.path.exists(_ico):
            app.setWindowIcon(QIcon(_ico))
        _bootlog("qapp ok")
        for font_file in ("msyh.ttc", "msyhbd.ttc"):
            path = os.path.join(os.environ.get("WINDIR", r"C:\Windows"), "Fonts", font_file)
            if os.path.exists(path):
                QFontDatabase.addApplicationFont(path)
        app.setApplicationName(APP)
        app.setStyleSheet(QSS95)
        w = Main()
        app._whiteframe_main = w      # 关键：保持顶层窗口引用，避免被 GC 回收
        _bootlog("main window ok")
        w.show()
        sys.exit(app.exec())
    except SystemExit:
        raise
    except BaseException:
        _bootlog("EXC://n" + _tb.format_exc())
        _log_error()
        raise


if __name__ == "__main__":
    main()
