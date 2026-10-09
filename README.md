# Tinta e Esquecimento — Alfa (Pygame)

Versao experimental de plataforma **lateral 2D**, derivada da historia e mecanicas da demo original. O repositorio original permanece separado.

## Jogar no VS Code (Windows)

1. Baixe o ZIP completo desta versao, extraia a pasta toda e abra-a no VS Code.
2. Execute `preparar_windows.bat` (cria `.venv` e instala Pygame); se os recursos estiverem ausentes, restaura o pacote de midia interno ou baixa as copias publicas da demo anterior. **A musica de inicio escolhida esta incluida no ZIP completo e no pacote interno do repositorio.**
3. Abra `main.py`, selecione `.venv\\Scripts\\python.exe` e pressione **F5**, ou clique em `jogar.bat`.

Via terminal: `python -m pip install -r requirements.txt` e `python main.py`.

## Controles

| Tecla | Acao |
| --- | --- |
| A/D ou esquerda/direita | Andar |
| W ou cima | Pular |
| S ou baixo | Agachar |
| Q | Disparar tinta na direcao do personagem |
| W + Q | Disparar tinta diagonalmente para cima |
| Espaco | Ataque curto de tinta |
| E | Escudo temporario do jogador |
| F | Ler livros verdes, entrar no portal, ativar pedestal |
| B | Ponte de tinta na fase 2 |
| ESC | Pausa |

## Objetivo e Boss

Colete **3 livros em cada fase**. Os livros verdes no chao recuperam vida e tinta com intervalo de recarga. Na fase final, busque os tres livros, volte ao **pedestal no nivel do chao** e aperte **F** perto dele. O escudo do Boss desliga de forma permanente. A luta pode ser vencida atirando em linha reta; nao exige saltos de precisao. Os livros de cura continuam acessiveis.

## Opcoes e recordes

A musica e os efeitos tem volumes independentes na tela Configuracoes (setas ou A/D). Sao salvos automaticamente em `%LOCALAPPDATA%\\TintaEEsquecimento\\progresso.json` (Windows) ou `~/.tinta_e_esquecimento/progresso.json` (Linux/macOS). **Ranking limita a 5 pontuacoes** e grava nome e pontuacao quando a aventura e concluida.

## Build Windows

Com Python e dependencias de `requirements-build.txt`:

```powershell
python build_windows.py
```

O script executa smoke tests e empacota o jogo com PyInstaller no modo `--onedir`; o resultado sera `dist/TintaEEsquecimentoAlfa-Windows.zip`. O GitHub Actions executa build no `windows-latest` em cada push e publica um artefato para baixar. O arquivo `.exe` nao e gerado num ambiente Linux: o build real ocorre no Windows.

Teste sem janela/monitor: `python main.py --smoke-test --scene chefe`; screenshots: `python main.py --frames 2 --scene fase1 --screenshot teste.png`.

### Creditos e direitos

Conceito e historia: autor do projeto. Personagem GrafxKid (CC0); paisagens CraftPix Freebies conforme licenca do pacote. Sons recebidos: Packsmithy, newlocknew, benson_arizona e kevp888; consulte as licencas originais de cada recurso antes de redistribuir. Os audios desta versao foram compactados e os originais enviados nao foram modificados.