# -*- mode: python ; coding: utf-8 -*-
from pathlib import Path
HERE = Path(SPECPATH)


a = Analysis(
    [str(HERE / 'app40.py')],
    pathex=[str(HERE)],
    binaries=[],
    datas=[(str(HERE / 'icon.ico'), '.'),
           (str(HERE / 'icon.png'), '.')],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[str(HERE / 'qt_runtime40.py')],
    excludes=['tkinter', 'numpy', 'unittest', 'pydoc', 'PySide6.QtQml', 'PySide6.QtQuick'],
    noarchive=False,
    optimize=0,
)
# Keep the bundled Qt DLL search deterministic; omit host-provided ICU/API-set copies.
a.binaries = [
    item for item in a.binaries
    if item[0].replace(chr(92), '/').rsplit('/', 1)[-1].lower()
       not in {'icuuc.dll', 'icudt78.dll', 'ucrtbase.dll'}
    and not item[0].replace(chr(92), '/').rsplit('/', 1)[-1].lower().startswith('api-ms-win-')
]

pyz = PYZ(a.pure)
exe = EXE(
    pyz, a.scripts, a.binaries, a.datas, [],
    name='WhiteFrame40',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=[str(HERE / 'icon.ico')],
)
