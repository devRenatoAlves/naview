# SDD: NaView

Documentação no estilo SDD (desenvolvimento guiado por especificação). Cada parte do sistema tem
uma especificação com **requisitos** (o que precisa fazer), **design** (como foi feito) e
**situação** (o que já funciona e o que falta). As tarefas ficam numa lista única.

**Regra:** a cada progresso, atualizar a especificação afetada, `tarefas.md` e, se houve escolha
importante, `decisoes.md`. Uma sessão nova deve conseguir continuar o trabalho só lendo esta
pasta.

## Índice

| Arquivo | Conteúdo |
|---|---|
| [visao.md](visao.md) | Para que serve, quem usa, ambiente, restrições |
| [specs/01-app-abas.md](specs/01-app-abas.md) | App de abas: encaixe do AnyDesk, contatos, teclado |
| [specs/02-temas.md](specs/02-temas.md) | Temas, aparência e desempenho |
| [specs/03-jogo.md](specs/03-jogo.md) | Jogo: cartas, baús, pet, loja, níveis e a economia (números) |
| [specs/04-servidor.md](specs/04-servidor.md) | Servidor da equipe: login, ranking, prêmios (**em planejamento**) |
| [specs/05-landing.md](specs/05-landing.md) | Página de apresentação com download (**pronta, falta publicar**) |
| [specs/06-windows.md](specs/06-windows.md) | NaView no Windows, idêntico ao do Linux (**em planejamento**, fase 0) |
| [specs/07-atualizacao.md](specs/07-atualizacao.md) | Atualização automática do app (Linux e Windows), manifesto `versao.json` |
| [decisoes.md](decisoes.md) | Registro de decisões e o porquê de cada uma |
| [tarefas.md](tarefas.md) | Lista de tarefas com situação |
| [testes.md](testes.md) | Como testar sem mexer nos dados e na tela do usuário |

## Situação geral (atualizado em 22/10/2026)

- **Atualização automática:** pronta e enviada na versão `2026.10.22.1`; falta testar no Windows e
  no Qt. Ver [specs/07-atualizacao.md](specs/07-atualizacao.md).

- App de abas e temas: prontos e em uso. Falta testar com sessões remotas reais.
- Jogo fase 1 (local): pronto. Economia ajustada para ritmo lento.
- **Próximo passo:** servidor da equipe na VPS do usuário (login, progresso no servidor, sorteios
  no servidor, ranking e prêmios). Aguardando: confirmação do plano do AnyDesk e dados da VPS.
  Ver [specs/04-servidor.md](specs/04-servidor.md), que também planeja o perfil dos colegas (ver inventário uns dos outros).
- **Windows:** o usuário quer o programa idêntico. Falta rodar o teste de viabilidade
  (`ferramentas/teste_windows.py`) num PC com Windows. Ver [specs/06-windows.md](specs/06-windows.md).
