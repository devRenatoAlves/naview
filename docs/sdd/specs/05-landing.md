# 05: Página de apresentação (landing page)

**Situação:** página pronta e testada localmente (14/10/2026). Falta publicar na VPS pelo Coolify.

## Requisitos

- Página online, divertida mas bonita, apresentando o NaView.
- Botão de download do app, com o arquivo servido pelo próprio site (não pelo GitHub).
- Hospedada na VPS do usuário, publicada pelo Coolify.

## Design (proposta)

- Site estático (HTML, CSS e JS, ou Astro), servido por um contêiner nginx no Coolify, com HTTPS
  automático.
- Download: pacote `.tar.gz` com o app e o `instalar.sh`, versão e SHA-256 visíveis na página.
- Seções: destaque inicial, abas do AnyDesk, galeria de temas, jogo de coleção (cartas
  interativas, reaproveitando `arte/`, `icones/` e `web/jogo.*`), download e instalação.

## Ferramentas pesquisadas (dados do GitHub em 14/10/2026)

| Ferramenta | Para quê | Estrelas | Última atualização | Licença | Veredito |
|---|---|---|---|---|---|
| `frontend-design` (anthropics/skills) | Direção visual com personalidade | 181k (repositório) | 09/10/2026 | — | Usar (já instalada) |
| `ui-ux-pro-max-skill` (nextlevelbuilder) | Paletas, fontes, estilos e checklist de interface | 136k | 12/10/2026 | MIT | Usar |
| `taste-skill` (Leonxlnx) | Regras mais fortes de tipografia e layout para landing pages | 96k | 14/10/2026 | MIT | Alternativa à anterior |
| `impeccable` (pbakaus) | Comandos de revisão e polimento do visual | 81k | 14/10/2026 | Apache-2.0 | Descartado (ver Instalação) |
| `webapp-testing` (anthropics/skills) | Testar a página num navegador automático | — | 09/10/2026 | — | Usar |
| `playwright-mcp` (microsoft) | Navegador automático para o Claude (prints só da página) | 38k | 08/10/2026 | Apache-2.0 | Usar (já no catálogo oficial) |
| `claude-seo` (AgriciDaniel) | SEO, prévia em redes sociais, checagens de Lighthouse | 19k | 04/10/2026 | MIT | Opcional (ferramenta grande; usar só a parte técnica) |
| `theme-factory` / `canvas-design` (anthropics/skills) | Temas de cores e artes estáticas | — | 09/10/2026 | — | Opcional |
| `coolify-mcp` (StuMason) | Publicar e controlar o Coolify pelo Claude | 611 | 14/10/2026 | MIT | Não usar por ora: pede token com acesso total à VPS |

Ler o código de cada ferramenta da comunidade antes de instalar.

### Instalação (14/10/2026)

- `ui-ux-pro-max`: copiado para `.claude/skills/ui-ux-pro-max` (só vale neste projeto). Código
  lido: scripts Python que só consultam tabelas locais, sem internet e sem rodar comandos.
- `playwright`: plugin oficial instalado no escopo do projeto. Roda `npx @playwright/mcp@latest`.
- `impeccable`: **não instalado**. O lançador baixa um programa compilado de
  `github.com/pbakaus/impeccable/releases` na primeira execução, e esse código não dá para ler
  antes. A versão em plugin também roda ganchos automáticos a cada edição de arquivo.

## Como foi feito (14/10/2026)

- Código em `site/fonte/` (`index.html`, `estilo.css`, `pagina.js`). Não editar `site/publico/`:
  é gerado.
- `python3 ferramentas/gerar_site.py` monta `site/publico/`: copia artes, fontes e o confete do
  app, gera `download/naview-<versão>.tar.gz` (pasta `naview/` com o app, sem `docs/` nem
  `site/`) e um `.sha256`, e preenche no HTML a versão, o arquivo, o tamanho e o SHA-256.
- Versão no arquivo `VERSAO` (formato data: `2026.10.14`). Mudou o app? Atualize `VERSAO` e
  rode o script de novo.
- `site/Dockerfile` (nginx 1.27-alpine) e `site/nginx.conf`: servem `publico/`; `/download/`
  sempre baixa como arquivo.
- Visual: tema Alto-mar (Fredoka, cores do ícone). Topo com janela do app de demonstração (abas
  clicáveis, setas do teclado trocam de aba) e cartas de tema que trocam o cenário e a janela
  (Alto-mar, Aventura Pixel, Heróis HQ, Espaço, Neon 80s, Terminal) com as cores de `temas.py`.
- Seção do jogo com baú de demonstração: sorteio com os mesmos pesos de `jogo/catalogo.py`
  (cópia em `pagina.js`; se mudar os pesos lá, mudar aqui também).
- Instalação em 3 passos com botão de copiar: dependências `apt`, extrair em `~`, `instalar.sh`.
- Testado com o Playwright em 1366 px e 375 px: sem rolagem lateral, sem erros no console;
  animações desligadas com "reduzir movimento".

## Publicação

- Código no GitHub, repositório privado `devRenatoAlves/naview`, ramo `main`.
- Endereço: `https://review.hunpe.com.br`.
- Coolify: recurso a partir de repositório privado (GitHub App), Build Pack = Dockerfile,
  Base Directory = `/`, Dockerfile Location = `/site/Dockerfile`, porta 80.
- O `Dockerfile` tem dois estágios: um Python que roda `ferramentas/gerar_site.py` e um nginx que
  serve `site/publico`. Por isso `site/publico` não vai para o git (`.gitignore`).
- `.dockerignore` deixa de fora `docs/`, `.claude/`, `.git` e arquivos gerados.
