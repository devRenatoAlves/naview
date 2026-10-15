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

## Sintaxe

```bash
python3 -m py_compile app.py jogo/*.py && node --check web/jogo.js
```
