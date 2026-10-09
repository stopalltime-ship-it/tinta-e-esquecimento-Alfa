"""Build real para Windows via PyInstaller (execute no Windows)."""
from pathlib import Path
import os
import shutil
import subprocess
import sys


def main():
    if sys.platform != 'win32':
        raise SystemExit('Execute no Windows ou use GitHub Actions, que faz o build em Windows.')
    root=Path(__file__).resolve().parent
    os.chdir(root)
    subprocess.run([sys.executable,'preparar_assets.py'],check=True)
    subprocess.run([sys.executable,'-m','compileall','-q','main.py'],check=True)
    subprocess.run([sys.executable,'-m','unittest','discover','-s','tests','-v'],check=True)
    subprocess.run([sys.executable,'main.py','--smoke-test','--scene','chefe'],check=True)
    subprocess.run([sys.executable,'-m','PyInstaller','--noconfirm','--clean','--onedir',
                   '--windowed','--name','TintaEEsquecimentoAlfa','main.py'],check=True)
    target=root/'dist'/'TintaEEsquecimentoAlfa'
    shutil.copytree(root/'assets',target/'assets',dirs_exist_ok=True)
    shutil.copy2(root/'README.md',target/'README.md')
    subprocess.run([str(target/'TintaEEsquecimentoAlfa.exe'),'--smoke-test','--scene','chefe'],check=True,timeout=40)
    archive=shutil.make_archive(str(root/'dist'/'TintaEEsquecimentoAlfa-Windows'),'zip',root/'dist','TintaEEsquecimentoAlfa')
    print('Build concluido:',archive)

if __name__=='__main__': main()