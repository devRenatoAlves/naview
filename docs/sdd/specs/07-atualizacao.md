# 07: Atualização automática do app

**Situação:** implementado em 22/10/2026 (Linux testado de ponta a ponta com um pacote local; GTK
testado sem abrir a janela; Qt e Windows **ainda não testados**, falta rodar num PC com Windows e
com PySide6).

## Requisitos

- Quem baixou o NaView (Linux ou Windows) recebe cada versão nova que for publicada, sem baixar
  de novo na mão.
- Funciona em qualquer PC da equipe: nada de caminho, usuário ou ambiente fixo; o Linux funciona
  com GTK e com Qt; no Windows, sem pedir administrador.
- Leve: nenhuma animação ou repintura. A rede roda em thread, uma vez 30 s depois de abrir e a cada
  6 h.
- O usuário escolhe a hora de atualizar (botão **Atualizar** na barra), exceto quando a versão
  instalada fica abaixo da mínima (ver abaixo).
- Não mexer em arquivos do usuário (`~/.config/naview`, `~/.local/share/naview`, `%APPDATA%`).

## Design

```
push no main → Coolify refaz o site (gerar_site.py) → /download/versao.json
app abre (+30 s) e a cada 6 h → consulta → botão "Atualizar" na barra
clique → confirma (avisa das conexões abertas) → baixa e confere o SHA-256 → fecha o app
ao terminar o processo (atexit) → troca os arquivos (Linux) ou roda o instalador (Windows) → reabre
```

- **Manifesto** `download/versao.json`, gerado por `ferramentas/gerar_site.py`: `formato`,
  `minimo`, `pagina`, e uma entrada `linux` e outra `windows` com `versao`, `arquivo` (relativo ao
  manifesto), `sha256` e `tamanho`. Cada sistema tem a sua versão: o instalador do Windows chega
  depois do pacote do Linux (o GitHub Actions o monta e o site refaz).
- **Versão** em `VERSAO`, formato `AAAA.MM.DD.N`. `python3 ferramentas/nova_versao.py` sobe o número
  antes do push. O app só atualiza se a versão do site for maior que a instalada.
- **Versão mínima** (opcional): arquivo `VERSAO_MINIMA` na raiz. Quem estiver abaixo vê a pergunta
  de atualizar assim que o app acha a versão nova (não bloqueia o app).
- **`atualizador.py`** (só biblioteca padrão), usado por `app.py` (GTK) e `app_qt.py` (Qt):
  `consultar()`, `preparar()`, `agendar()`.
- **Linux:** o `.tar.gz` é extraído em `<pasta do app>/.atualizacao/`, conferido (`app.py` presente,
  `VERSAO` igual à anunciada) e, quando o programa termina, as pastas e arquivos do pacote trocam
  de lugar com os atuais; se algo falhar no meio, volta tudo. Arquivos que não são do pacote ficam.
  O app reabre sozinho com o mesmo interpretador e o mesmo script.
- **Windows:** o instalador (`NaView-instalador.exe`) é baixado para uma pasta temporária e roda com
  `/SILENT` depois que o NaView fecha; o Inno Setup instala por cima e reabre o app (entrada
  `[Run]` com `Check: WizardSilent`). O app empacotado lê a versão de `VERSAO`, que o PyInstaller
  agora leva (`--add-data "VERSAO;."`).
- **Quando não atualiza sozinho:** pasta do app sem permissão de escrita, ou com `.git` (cópia de
  desenvolvimento), ou Windows rodando do código-fonte. O botão abre a página de download.

## Segurança

- Só `https` (a variável `NAVIEW_URL_ATUALIZACAO`, usada nos testes, libera `http` e `file`).
- O SHA-256 vem do manifesto, que vem do mesmo site: protege de download corrompido, **não** de
  quem invadir a VPS. Para a equipe de ~10 pessoas foi aceito; se crescer, assinar o manifesto com
  uma chave que só o dono tem (a chave pública vai dentro do app).
- Extração só de arquivos e pastas comuns, sempre dentro da pasta de preparo.

## Limites conhecidos

- Quem já tem uma versão **sem** o atualizador precisa baixar uma vez à mão; depois é automático.
- No Windows o aviso do SmartScreen para `.exe` sem assinatura continua; a atualização silenciosa
  não tira esse aviso.
- Se o app for fechado à força (kill) depois de baixar, a troca não acontece; na próxima vez ele
  baixa de novo.

## Como testar

- `python3 ferramentas/gerar_site.py` e conferir `site/publico/download/versao.json`.
- Linux: extrair o pacote numa pasta temporária (sem `.git`), baixar o `VERSAO` dela para uma
  versão antiga e chamar `consultar()`, `preparar()`, `agendar()` com
  `NAVIEW_URL_ATUALIZACAO=file:///.../versao.json`. Conferir a troca, que um arquivo do usuário
  continua lá e que o app reabre na versão nova.
- Windows: instalar a versão A, publicar a B, abrir a A e clicar em Atualizar.
