# -*- mode: python ; coding: utf-8 -*-
import os
import sys
import platform

block_cipher = None

# Set icon path based on OS
if platform.system() == "Windows":
    app_icon = "icon.ico"
elif platform.system() == "Darwin":
    app_icon = "icon.icns"
else:
    app_icon = "icon.png"

a = Analysis(
    ['main.py'],
    pathex=[os.path.dirname(os.path.abspath(__file__))],
    binaries=[],
    datas=[
        ('assets/*.png', 'assets'),
        ('gui/*.py', 'gui'),
        ('gui/*.ui', 'gui'),
        ('*.icns', '.'),
        ('*.ico', '.'),
        ('*.png', '.'),
        ('yolo11l-Co-train/*', 'yolo11l-Co-train'),
        ('yolo11l-De-train/*', 'yolo11l-De-train'),
    ],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='Inspectron',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    icon=app_icon,
)

if platform.system() == 'Darwin':
    app = BUNDLE(
        exe,
        name='Inspectron.app',
        icon=app_icon,
        bundle_identifier='com.inspectron.app',
    )
    coll = COLLECT(
        app,
        a.binaries,
        a.zipfiles,
        a.datas,
        strip=False,
        upx=True,
        upx_exclude=[],
        name='Inspectron'
    )
else:
    coll = COLLECT(
        exe,
        a.binaries,
        a.zipfiles,
        a.datas,
        strip=False,
        upx=True,
        upx_exclude=[],
        name='Inspectron'
    )
