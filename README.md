# Tinta e Esquecimento — Alfa

Jogo de aventura **2D de plataforma lateral** feito com Python e Pygame. Jogue os tres capitulos, recolha os livros, vença o Revisor e registre seu nome no **ranking Top 5**.

![Uploading image.png…]()


> Imagem da versao Alfa. O projeto atualizado inclui Ilo azul, novos efeitos e trilhas originais.

## Como jogar no VS Code (Windows)

1. Baixe o ZIP completo e extraia todos os arquivos, sem mover somente `main.py`.
2. Abra a pasta `TintaEEsquecimentoAlfa` no VS Code.
3. Execute `preparar_windows.bat` uma vez, para instalar Pygame e restaurar os recursos se necessario.
4. Execute `jogar.bat` ou pressione **F5** com `main.py` aberto (Python selecionado: `.venv\Scripts\python.exe`).

Alternativa pelo terminal, com Python instalado:

```bash
python -m pip install -r requirements.txt
python preparar_assets.py
python main.py
```

## Controles

| Teclas | Acao |
| --- | --- |
| A/D ou setas esquerda/direita | Movimentar |
| W ou seta para cima | Pular |
| S ou seta para baixo | Agachar |
| Q | Atirar tinta para frente |
| W + Q | Atirar tinta na diagonal para cima |
| ESPACO | Ataque curto de tinta (efeito visual breve) |
| E | Escudo temporario do jogador |
| F | Interagir com livros verdes, portal e pedestal |
| B | Desenhar ponte na fase 2 |
| ESC | Pausar |

## Capítulos e combate final

- **Capitulo 1: Sala de Contos Infantis** — Explore a floresta e recupere os 3 livros.
- **Capitulo 2: Arquivo dos Versos e Mapas** — Construa a ponte com B e encontre os livros.
- **Capitulo 3: A Ultima Pagina** — Junte 3 livros, volte ao pedestal no nivel do chao e pressione F para desativar permanentemente o escudo do Revisor.

Ao vencer o Revisor, a tela para **digitar o nome aparece automaticamente**; confirme com ENTER para registrar a pontuacao. Os cinco melhores resultados ficam salvos entre as sessoes. A altura das plataformas foi ajustada para tornar os saltos mais acessiveis.

## Trilha sonora e configuracoes

Cinco **composicoes instrumentais originais** e diferentes, feitas para esta versao: menu, capitulos 1 e 2, batalha do Boss e tela de vitoria. As trilhas compartilham identidade melodica, sem reutilizar o mesmo arquivo. O som de confirmar do menu continua presente.

Configure musica e efeitos separadamente em **Configuracoes**. Os ajustes e o ranking sao salvos em `%LOCALAPPDATA%\TintaEEsquecimento\progresso.json` (Windows) ou `~/.tinta_e_esquecimento/progresso.json` (Linux/macOS). O ranking guarda no maximo 5 nomes.

## Build de Windows

```powershell
python -m pip install -r requirements-build.txt
python build_windows.py
```

O script testa o codigo e gera `dist/TintaEEsquecimentoAlfa-Windows.zip` com executavel Windows (`.exe`). O workflow **Build Alfa Windows** executa essa compilacao no GitHub Actions em um runner Windows e disponibiliza o pacote na area de *Artifacts*. **O arquivo executavel de Windows nao pode ser compilado neste ambiente Linux.**

Para verificar cenas em uma maquina com Pygame instalado:

```bash
python main.py --smoke-test --scene chefe
python main.py --frames 2 --scene fase1 --screenshot captura.png
```

## Creditos

Conceito e historia: autor do jogo. Pixel art de Ilo azul criada para esta versao; personagem anterior GrafxKid (CC0) conservado como recurso de compatibilidade. Cenarios do pacote original CraftPix Freebies (ver licenca original). As 5 novas trilhas instrumentais sao criacoes originais sintetizadas para este projeto, sem amostras de musicas comerciais. Efeito de confirmacao preservado da versao anterior; verifique a respectiva licenca ao redistribuir. Arte de capa/ilustracao da arvore preservada.
