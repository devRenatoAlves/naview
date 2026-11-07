# Contribuindo com o NaView

Obrigado pelo interesse! Projeto pequeno, mantido por pouca gente, então o fluxo é simples.

## Antes de abrir um PR

- **Abra uma issue primeiro** para mudanças que não sejam correção pequena — alinhar a ideia
  evita trabalho perdido.
- **Teste em mais de um sistema sempre que possível.** O NaView roda em vários Linux (GNOME, KDE)
  e em Windows (em testes); evite qualquer caminho, usuário, ambiente de desktop ou atalho fixo de
  uma máquina só. Se não puder testar num dos sistemas, diga isso no PR.
- **Leve e fluido**: o app fica aberto o dia todo com sessões remotas em aba. Nada de animação
  contínua sem necessidade, timer que repinta a tela parada, ou efeito caro (desfoque grande,
  sombra grande, gradiente radial). Anime só quando a tela está visível.
- **Arte e sons originais** (scripts em `ferramentas/`), exceto os três pets de Pokémon em
  `arte/pets/` (arte de fã, ver aviso no README) — não adicione mais sprites de propriedade de
  terceiros sem marcar a licença/origem.
- Interface em português, sem emoji; ícones são [Phosphor](https://phosphoricons.com/).

## Rodando localmente

```bash
python3 app.py
```

Requisitos: Python 3, PyGObject (GTK 3), libX11 e AnyDesk. O jogo usa também WebKit2GTK 4.1,
GStreamer e libnotify — sem eles, o app roda normal e só o jogo fica indisponível.

### Versão Qt (Linux e Windows), em teste

```bash
sudo apt install python3-pyside6.qtwidgets python3-pyside6.qtsvg python3-pyside6.qtwebenginewidgets \
  python3-pyside6.qtwebchannel python3-pyside6.qtmultimedia python3-pyside6.qtdbus
python3 app_qt.py
```

Usa os mesmos contatos, temas e progresso do `app.py`; não abra os dois ao mesmo tempo. No
Windows, o instalador é montado pelo GitHub Actions (`.github/workflows/windows.yml`).

## Estrutura do projeto

- `app.py`: janela, abas, contatos, conexões e foco do teclado (GTK3). `app_qt.py`: versão Qt.
- `temas.py`, `janela_aparencia.py`: temas e galeria de opções.
- `contatos.py`: leitura dos contatos do AnyDesk e apelidos.
- `x11.py`: acesso à libX11 (listar janelas, PID, foco, desfoque).
- `fontes.py`, `fonts/`, `arte/`, `ferramentas/gerar_arte.py`: fontes e desenhos dos temas e do
  jogo (pets em `ferramentas/desenhos_pets.py` e `ferramentas/importar_pets.py`; sprites dos
  Pokémon por `ferramentas/baixar_sprites.py`).
- `jogo/catalogo.py` (cartas, baús, regras), `jogo/progresso.py` (motor e banco de
  `~/.local/share/naview/progresso.db`), `jogo/tela.py` (página do jogo no WebKitGTK), `jogo/gtk.py`
  (pet no rodapé, sons, notificações).
- `web/`: página do jogo (HTML/CSS/JS, GSAP e canvas-confetti); `ferramentas/gerar_sons.py`: sons
  sintetizados.
- `ferramentas/simular_economia.py`: simula meses de uso pra medir o ritmo das recompensas do
  jogo — rode depois de mudar um número da economia.
- `icones/phosphor/`: ícones Phosphor (MIT). `ferramentas/gerar_icones.py` gera os dois formatos
  usados (web e GTK).
- `VERSAO`: versão do app (`AAAA.MM.DD.N`). `atualizador.py`: checagem e aplicação da atualização.
- `site/fonte/`: página de apresentação; `ferramentas/gerar_site.py` monta `site/publico/`.
- `ferramentas/provisao_uso.py`, `relatorios/`: benchmark de uso (ver `BENCHMARKS.md`).

## Temas disponíveis

Padrão, Grafite, Claro, Oceano (cores), Vidro líquido (desfoque), Aventura Pixel, Heróis HQ,
Espaço, Terminal, Neon 80s, Mangá Noir e Alto-mar — cada um com fonte, paleta e animações
próprias, trocados no botão de presente da barra de título.

## Testes

Veja `ferramentas/` para os scripts de geração de arte/economia do jogo. Se mudar um número da
economia do jogo, rode `python3 ferramentas/simular_economia.py` e confira o resultado.

## Estilo de commit

Mensagens curtas, descrevendo o efeito da mudança (`tipo: o que mudou`), em português, como o
restante do histórico do projeto.

## Dúvidas

Abra uma issue.
