# -*- coding: utf-8 -*-
"""Make PySide6 and shiboken6 DLL lookup deterministic in frozen builds."""
import os
import sys

if sys.platform == "win32":
    _root = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(sys.executable)))
    _dirs = [
        _root,
        os.path.join(_root, "PySide6"),
        os.path.join(_root, "shiboken6"),
    ]
    _existing = [d for d in _dirs if os.path.isdir(d)]
    if _existing:
        # Keep the handles alive for the life of the process; otherwise Windows
        # removes the AddDllDirectory entries when the temporary object dies.
        sys._whiteframe34_dll_handles = [os.add_dll_directory(d) for d in _existing]
        os.environ["PATH"] = os.pathsep.join(_existing + [os.environ.get("PATH", "")])