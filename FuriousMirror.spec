# -*- mode: python ; coding: utf-8 -*-
import os
import sdl2dll

# Find SDL2 DLLs dynamically
sdl2_dlls_src = os.path.join(sdl2dll.__path__[0], "dll")

a = Analysis(
    ['run.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('portables/adb', 'portables/adb'),
        ('portables/images', 'portables/images'),
        (sdl2_dlls_src, 'sdl2_bins'),
        ('portables/images/furious-mirror.png', 'images')
    ],

    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['portables'],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='FuriousMirror',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    uac_admin=True,
    icon='portables/images/furious-mirror.ico',
)

# --- AUTO CLEANUP SCRIPT ---
# Remove a pasta 'build' automaticamente após o término do PyInstaller
import atexit
import shutil

def cleanup_build():
    build_dir = os.path.abspath('build')
    if os.path.exists(build_dir):
        try:
            print("\n" + "="*50)
            print("LIMPANDO ARQUIVOS TEMPORÁRIOS...")
            shutil.rmtree(build_dir)
            print("Pasta 'build' removida com sucesso! Seu .exe está na pasta 'dist'.")
            print("="*50 + "\n")
        except Exception as e:
            print(f"Aviso: Não foi possível remover a pasta build: {e}")

atexit.register(cleanup_build)
