# NaView

Junta as conexões do AnyDesk em abas, numa única janela, com a lista de contatos ao lado —
pensado para quem atende vários clientes por dia. Linux hoje; Windows em andamento.

> **English:** NaView embeds multiple AnyDesk connections as tabs in a single window, with a
> contacts sidebar — built for support teams juggling many clients a day.

Além do essencial, tem temas visuais e um jogo opcional de coleção (cartas, baús, pet), de
propósito lento, pra dar um motivo de abrir o app sem distrair do trabalho.

## Instalar (Linux)

Requisitos: Python 3, PyGObject (GTK 3), libX11 e o AnyDesk instalado. O jogo usa também
WebKit2GTK 4.1, GStreamer e libnotify (opcional — sem eles, só o jogo fica indisponível).

```bash
sudo apt install python3-gi gir1.2-gtk-3.0 gir1.2-webkit2-4.1 gir1.2-notify-0.7 \
  gir1.2-gstreamer-1.0 gstreamer1.0-plugins-good
```

Baixe o pacote em [naview.hunpe.com.br](https://naview.hunpe.com.br) e extraia na pasta pessoal,
ou rode direto do código:

```bash
python3 app.py
```

`./instalar.sh` cria o atalho no menu de aplicativos (avisa se faltar alguma biblioteca).

## Como funciona

- O app e o AnyDesk rodam pelo X11/XWayland (`GDK_BACKEND=x11`), o que permite encaixar a janela
  do AnyDesk dentro de uma aba.
- A lista de contatos vem do catálogo do AnyDesk (`~/.anydesk/user.conf`); apelidos ficam só no
  NaView, sem alterar o arquivo original.
- Duplo clique ou Enter conecta; o teclado vai direto pro cliente com a sessão em foco; **F9**
  mostra/esconde contatos, **Ctrl+F** busca.
- Temas (cores simples a temas completos com fonte e animação própria) e o jogo de coleção ficam
  no botão de presente da barra de título — tudo salvo localmente, nada depende de servidor.
- Desenhos e animações só na tela inicial; com uma sessão de atendimento aberta, nada fica
  pesando a máquina.

## Atualizações

O app confere sozinho se há versão nova (a cada 6h) e mostra um botão **Atualizar** quando houver;
baixa, confere o arquivo e troca sem apagar configuração ou progresso.

## Desempenho

Quanto o NaView pesa a mais que o AnyDesk puro (RAM, CPU, rede, disco), com números marcados como
medidos ou projetados: [`BENCHMARKS.md`](BENCHMARKS.md).

## Contribuindo

Veja [CONTRIBUTING.md](CONTRIBUTING.md) — estrutura do projeto, convenções e como testar.

## Licença

GPLv3 — veja [LICENSE](LICENSE).

Os sprites de Pikachu, Eevee e Jigglypuff em `arte/pets/` vêm do
[PokeAPI sprites](https://github.com/PokeAPI/sprites) e são propriedade da Nintendo/Game Freak;
estão aqui como arte de fã, sem fins comerciais. Fontes usam licença OFL e os ícones são
[Phosphor](https://phosphoricons.com/) (MIT). AnyDesk é marca da AnyDesk Software GmbH; o NaView
não tem ligação com a empresa.
