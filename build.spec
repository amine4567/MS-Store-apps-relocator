# -*- mode: python ; coding: utf-8 -*-

import sys
from pathlib import Path

block_cipher = None

py_exe_path = sys.executable
pyside6_plugins_path = (
    Path(py_exe_path).parent.parent / "Lib" / "site-packages" / "PySide6" / "plugins"
)
pyside6_plugins = Tree(
    pyside6_plugins_path,
    prefix="PySide6/plugins",
    excludes=[],
    typecode="BINARY",
)

a = Analysis(
    ["src\\ui.py"],
    pathex=["C:\\Projects\\msstore_mover"],
    binaries=[],
    datas=[],
    hiddenimports=[],
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)
a.binaries += pyside6_plugins

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="MSStore apps relocator",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="MSStore apps relocator",
)
