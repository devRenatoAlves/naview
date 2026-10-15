# Visão

## Problema

A equipe de suporte atende muitos clientes por dia pelo AnyDesk. Cada conexão abre uma janela
separada, e alternar entre elas é lento e confuso.

## Solução

1. **App de abas:** junta as conexões do AnyDesk em abas, numa única janela, com a lista de
   contatos ao lado.
2. **Temas:** aparência personalizável, de cores simples a temas completos com fonte e arte.
3. **Jogo:** coleção de cartas, baús, pet e loja. Os atendimentos rendem recompensas, de forma
   **lenta de propósito**, porque a demanda de trabalho é alta.
4. **Servidor da equipe (planejado):** conta de cada colaborador, ranking e prêmios reais.

## Quem usa

- Cerca de **10 colaboradores** do suporte.
- O dono do projeto (usuário) administra e decide as regras e os prêmios.

## Ambiente

- Linux com KDE Plasma em Wayland (máquina do usuário). Também deve rodar no GNOME e nos outros
  ambientes, em Wayland ou X11: o app e o AnyDesk rodam pelo X11/XWayland (`GDK_BACKEND=x11`).
  Só o desfoque do tema vidro é do KDE.
- AnyDesk 8.1.0 (GTK3).
- Python 3.14 e PyGObject (GTK 3). Também são usados WebKit2 4.1, GStreamer 1.0 e libnotify 0.7.
- O projeto fica em `/home/renato/Documentos/dev-projects/naview`. Não é um repositório
  git.

## Restrições

- **Sem instalar nada no sistema:** fontes e ícones são carregados só para o app.
- Toda a interface fica em português e não usa emojis. Os ícones são Phosphor.
- A arte e os sons são originais, gerados pelos scripts de `ferramentas/`.
- O app não pode pesar enquanto há uma sessão aberta. O GTK3 desenha tudo no processador, por
  isso as animações ficam só na tela inicial.
- O AnyDesk não pode ser modificado. O app só lê `~/.anydesk/user.conf`.
- Com prêmios reais em jogo, **nenhuma regra pode depender só do computador do colaborador**
  (ver [specs/04-servidor.md](specs/04-servidor.md)).

## Preferências de trabalho do usuário

- Responder sempre em PT-BR e evitar jargão em inglês sem tradução.
- Antes de rodar um comando, explicar em 1 ou 2 linhas o que ele faz.
- Manter este SDD e as tarefas atualizados a cada progresso, sem esperar pedido.
