# 02: Temas e aparência

## Requisitos

- R1. Vários temas que aplicam na hora e ficam salvos.
- R2. Ajustes por cima de qualquer tema: cores, imagem de fundo, desenhos e animações (que podem
  ser desligados).
- R3. Tema de vidro líquido com desfoque do KWin e intensidade ajustável.
- R4. Os temas são cartas do jogo: o tema que o usuário não tem aparece bloqueado, com cadeado.
- R5. Tema no nível 5 da carta ganha a versão dourada.
- R6. Nada pode pesar com uma sessão aberta.

## Design

- **`temas.py`:**
  - `TEMAS` tem os temas padrao, grafite, claro, oceano, vidro, pixel, hq, espaco, terminal,
    neon e mar (Alto-mar). Cada um define cores, fonte, desenhos (`decor`), frases e CSS próprio.
  - `carregar` e `salvar` usam `~/.config/naview/config.json`.
  - `gerar_css(cfg, dourado, moldura)` monta o CSS.
  - `imagem_reduzida` reduz a imagem de fundo, com cache em `~/.cache/naview` e no máximo
    1920x1080.
- **`janela_aparencia.py`:** galeria de temas, ajustes de cor, imagem, intensidade do vidro e
  interruptores.
  - O estilo da janela é registrado uma vez só. O controle da intensidade aplica 150 ms depois de
    parar de mexer (aplicar refaz o CSS do app todo e grava o config).
  - Trocar de tema descarta os ajustes de cor, mas mantém a imagem de fundo, com um aviso.
- **Vidro:** a propriedade X `_KDE_NET_WM_BLUR_BEHIND_REGION` recebe os retângulos arredondados.
  A força do desfoque é uma configuração global do KDE, que o app não altera.
- **Desempenho:** sem `radial-gradient` e sem sombras com desfoque grande no CSS do GTK. Desenhos
  e animações só na tela inicial.
- **Recursos:**
  - Fontes em `fonts/`, com licença OFL.
  - Arte gerada por `ferramentas/gerar_arte.py`.
  - Ícones Phosphor 2.1.1 (licença MIT) convertidos por `ferramentas/gerar_icones.py`.

## Situação

- Pronto: R1 a R6.
- Alto-mar (14/10/2026): tema lendário com a marca do NaView. Arte em `arte/mar/`
  (`gerar_mar()`), fonte Fredoka e animação `navegar` (barco balançando). Testado fora da tela
  em 1280x820 e 900x640.
- O tema atual do usuário é "pixel", com imagem de fundo própria.
