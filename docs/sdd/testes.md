# Como testar

## Cuidados (dados e privacidade do usuário)

- **Não tirar print da tela inteira.** Os prints capturam janelas privadas do usuário (navegador,
  WhatsApp). Use renderização fora da tela:
  - GTK: `Gtk.OffscreenWindow` + `get_pixbuf()`.
  - Página do jogo: Chrome em segundo plano (`google-chrome --headless=new --screenshot`).
- **Não conectar em clientes reais** do AnyDesk durante os testes.
- **Não matar** a sessão real do AnyDesk do usuário nem o processo `--frontend`.
- **Não alterar** os arquivos reais:
  - Configuração: `~/.config/naview/config.json`.
  - Progresso: `~/.local/share/naview/progresso.db`.
  - Nos testes, aponte `jogo.progresso.ARQUIVO` e `temas.ARQUIVO` para uma pasta temporária, ou
    passe `Progresso(caminho)`.
- Não mexer na configuração global do KWin (força do desfoque).
- Evitar simular teclas com XTest, porque o KDE pode pedir permissão.

## Liberar todas as cartas (testes no app real)

Com `"liberar_tudo": true` em `~/.config/naview/config.json`, o app entrega todas as cartas do
catálogo (nível 1) toda vez que abre, inclusive as que entrarem depois. O usuário pediu isso ligado
na conta dele. O padrão é `false`, e a opção não aparece na interface.

## Regras do jogo

`Progresso` aceita relógio, data e sorteio falsos:

```python
Progresso(caminho, agora=lambda: t, hoje=lambda: data, rnd=random.Random(1))
```

Assim dá para avançar o tempo e repetir sorteios.

## Economia

```bash
python3 ferramentas/simular_economia.py         # 20 sorteios, 400 dias (~1 min)
python3 ferramentas/simular_economia.py 5 200   # mais rápido
```

Usa um banco temporário. Depois de rodar, atualize a tabela em
[specs/03-jogo.md](specs/03-jogo.md).

## Página do jogo no navegador

`web/jogo.js` entra em modo de teste quando existe `window.TESTE` (catálogo + estado). Para
gerar a página de teste:

1. Copie `web/jogo.html` para uma pasta temporária.
2. Na cópia, adicione `<base href="file://.../web/">` e um polyfill de `requestAnimationFrame`.
   Sem o polyfill, o GSAP não anda no Chrome em segundo plano.
3. Antes de `jogo.js`, carregue um `teste.js` com
   `window.TESTE = {catalogo: catalogo_para_web(), estado: Progresso(...).estado(), recompensa}`.
4. Use os endereços `#pet`, `#modal:<id da carta>` e `#abrir:<toques>`.

## Desempenho (leveza e fluidez)

Medir com o jogo parado e em cada tela, antes e depois da mudança. Sem `perf` (o kernel bloqueia),
use o tempo de CPU do processo:

- **Janela GTK parada:** montar o `App` numa `Gtk.OffscreenWindow` e contar `draw` e
  `time.process_time()` por 6 s em cada tema. Esperado: perto de zero.
- **Página do jogo:** abrir `web/jogo.html` (modo de teste) num `WebKit2.WebView` dentro de uma
  `Gtk.OffscreenWindow` (com `WEBKIT_DISABLE_COMPOSITING_MODE=1 WEBKIT_DISABLE_DMABUF_RENDERER=1`) e
  somar `utime+stime` do processo do app e dos filhos (`/proc/<pid>/stat`) por 8 s, nas telas
  `#baus`, `#colecao` e `#pet`, com a página pausada (`window.__pausar(true)`) e sem pausar.
  Esperado: pausada = quase zero; tela do pet abaixo de ~10% de um núcleo.
- `document.getAnimations()` na página lista o que está animando; um `MutationObserver` mostra o que
  mexe no DOM sem ninguém pedir.

## Sintaxe

```bash
python3 -m py_compile app.py jogo/*.py && node --check web/jogo.js
```

## Versão Qt (`app_qt.py`)

- **Fora da tela:** `QT_QPA_PLATFORM=offscreen` e `janela.grab().save(...)`. Antes de importar
  `app_qt`, aponte `plataforma.CONFIG/CACHE/DADOS`, `temas.ARQUIVO`, `contatos.ARQUIVO`,
  `contatos.ANYDESK_CONF` e `jogo.progresso.ARQUIVO` para uma pasta temporária. `app_qt` força
  `QT_QPA_PLATFORM=xcb` ao ser importado: troque para `offscreen` depois do import.
- **Jogo fora da tela:** precisa de `QTWEBENGINE_CHROMIUM_FLAGS=--disable-gpu`, senão a imagem sai
  vazia.
- **Encaixe sem AnyDesk:** uma janela GTK qualquer com `GDK_BACKEND=x11` e
  `set_wmclass("testealvo", "testealvo")`; troque `janelas.linux.CLASSE_ANYDESK` para `testealvo` e
  `App.j.abrir` por uma função que abre essa janela. O app aparece na tela por alguns segundos.
- O KDE não deixa uma janela aberta por script tomar o foco enquanto o usuário usa outra
  (proteção contra roubo de foco). Por isso o teclado entre a busca e a sessão só dá para conferir
  usando o app.
- Ao sair com abas abertas, o app pergunta "Fechar o NaView?": num teste, esvazie `App.abas` antes
  de `app.quit()`.

## Ver o tema dourado e a moldura dourada (só desenvolvimento)

`NAVIEW_DEMO_DOURADO=1 python3 app.py` abre o app com um progresso descartável
(`<cache>/progresso_demo.db`, recriado a cada abertura): Padrão, Oceano, Terminal, Espaço e
Aventura Pixel no nível 5 (um de cada raridade) e a moldura dourada equipada. O progresso real
não é lido nem alterado. Sem a variável, nada muda. Obs.: trocar de tema no jogo grava o tema no
`config.json` normal.
