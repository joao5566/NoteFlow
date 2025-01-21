# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['calendar_widget.py'],
    pathex=[],
    binaries=[],
    datas=[('shop_items/*', 'shop_items'), ('minigames_config/*', 'minigames_config'), ('minigames/*', 'minigames'), ('images/*', 'images'), ('icons/*', 'icons'), ('game_icons/*', 'game_icons')],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='calendar_widget',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
