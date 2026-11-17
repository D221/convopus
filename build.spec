# -*- mode: python ; coding: utf-8 -*-

block_cipher = None


a = Analysis(
    ['./src/convopus/__main__.py'],
    pathex=['./src'],
    binaries=[],
    datas=[],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # convopus never talks to the network, so the OpenSSL bindings
        # (libcrypto/libssl, ~9.6 MB on disk) are dead weight.
        'ssl',
        '_ssl',
        'hashlib',
        '_hashlib',
        'tkinter',
        'unittest',
        'pydoc',
        'doctest',
        'xmlrpc',
        # compression helpers that nothing here uses
        'bz2',
        'lzma',
        '_bz2',
        '_lzma',
        '_zstd',
        'compression',
        'tarfile',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='convopus',
    icon='docs/icon.ico',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    # UPX is not used: the onefile archive is already compressed, so packing
    # the outer PE saves ~0.2 MB and only risks antivirus false positives.
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
