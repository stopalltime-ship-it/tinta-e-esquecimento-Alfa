"""Baixa apenas os recursos publicos da demo original que estao ausentes.
A distribuicao ZIP completa ja traz os recursos enviados pelo autor, incluindo
menu_music.ogg. Nenhum recurso local existente sera substituido.
"""
from pathlib import Path
import base64
from urllib.request import urlopen
import sys
BASE = 'https://raw.githubusercontent.com/stopalltime-ship-it/tinta-e-esquecimento/main/assets/'
ROOT = Path(__file__).resolve().parent / 'assets'
SOURCES = {
 'images/classic_hero.png':'images/classic_hero.png',
 'images/scene_1.png':'images/conto_floresta.png',
 'images/scene_2.png':'images/mapa_montanhas.png',
 'images/scene_3.png':'images/ultima_pagina_ceu.png',
 'audio/confirm.wav':'audio/menu_confirm.wav',
 'audio/forest.ogg':'audio/ambiente_contos.ogg',
 'audio/bells.ogg':'audio/sinos_revisor.ogg',
 'audio/menu_music.ogg':'audio/ambiente_contos.ogg',
}
def main():
    failed=[]
    for relative, origin in SOURCES.items():
        dest=ROOT/relative
        if dest.is_file() and dest.stat().st_size>0:
            continue
        dest.parent.mkdir(parents=True,exist_ok=True)
        packed=ROOT/'packed'/(dest.name+'.b64')
        if packed.is_file():
            try:
                dest.write_bytes(base64.b64decode(packed.read_text(encoding='ascii')))
                print('Restaurado do pacote interno:',relative)
                continue
            except (ValueError, OSError) as err:
                print('Pacote interno falhou:',err, file=sys.stderr)
        try:
            print('Obtendo:',relative)
            with urlopen(BASE+origin,timeout=30) as response:
                data=response.read()
            if not data:
                raise ValueError('arquivo vazio')
            dest.write_bytes(data)
        except Exception as err:
            print('Nao foi possivel baixar',relative,err,file=sys.stderr)
            failed.append(relative)
    return 1 if failed else 0
if __name__=='__main__':raise SystemExit(main())