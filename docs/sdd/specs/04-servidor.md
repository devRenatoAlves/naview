# 04: Servidor da equipe (em planejamento)

## Objetivo

Cada colaborador tem uma conta. O progresso fica no servidor, então nada se perde ao trocar ou
formatar o computador. Com isso, a equipe passa a ter **ranking e prêmios reais**.

## Requisitos

- R1. Login leve: usuário e senha, uma vez por computador. O app lembra o login (token).
- R2. As contas são criadas pelo administrador (o usuário). Não existe cadastro aberto.
- R3. Ao entrar em outro computador, a conta e o histórico vêm do servidor.
- R4. **Anti-trapaça:** como há prêmios reais, as regras e os sorteios rodam **no servidor**. O
  computador do colaborador só mostra o jogo e pede ações.
- R5. Os atendimentos são **conferidos pela API REST do AnyDesk**: sessão falsa ou curta não
  conta. Se a API não estiver disponível, usar o plano B.
- R6. Sem internet, o app de abas funciona normalmente. Os atendimentos ficam numa fila e são
  enviados depois. Abrir baú e comprar exigem conexão.
- R7. O progresso local atual do usuário é migrado para a conta dele.
- R8. Ranking da equipe e painel do administrador (contas, prêmios, relatório de atendimentos).
- R9. ~10 usuários. Precisa ser simples de manter.

## Design proposto

- **Servidor em Python, reaproveitando `jogo/progresso.py`:**
  - Um `Progresso` por colaborador. As regras não são reescritas.
  - Um banco SQLite no servidor basta para 10 pessoas.
  - API HTTP com JSON. O framework ainda vai ser escolhido; a ideia é algo leve, como FastAPI, ou
    só a biblioteca padrão.
- **Cliente:** uma classe `ProgressoRemoto` com os mesmos métodos públicos de `Progresso` (ver
  [03-jogo.md](03-jogo.md)). `app.py` e `jogo/tela.py` quase não mudam.
- **Senhas:** guardadas como hash forte (ex.: bcrypt ou scrypt). O token fica salvo no
  computador do colaborador.
- **HTTPS:** obrigatório na internet. Com domínio, usar Caddy ou nginx com Let's Encrypt. Só com
  IP, é preciso decidir outro caminho.
- **Conferência de atendimentos:** o servidor consulta a API do AnyDesk (lista de sessões com
  duração) e só credita as sessões confirmadas.
- **Plano B (sem API):** limite diário de atendimentos que contam e relatório para o
  administrador conferir.

## Hospedagem

- VPS do usuário, acessada por SSH a partir deste computador. Existe o arquivo `~/.ssh/minhavps`,
  provavelmente a chave. Não há `~/.ssh/config`.
- **Regra:** antes de qualquer comando que mude algo na VPS, explicar e pedir confirmação.
  Senhas, da VPS ou do AnyDesk, nunca passam pelo chat: vão direto para um arquivo de
  configuração na VPS.

## Pendências (aguardando o usuário)

- [ ] Plano do AnyDesk: o usuário respondeu "Advanced ou Ultimate" e está confirmando. A API REST
      depende do plano.
- [ ] Dados da VPS: endereço (IP ou domínio), usuário do SSH, sistema (ex.: Ubuntu ou Debian), o
      que já roda nela (site, Docker, nginx).
- [ ] Domínio para HTTPS: existe ou não?
- [ ] Prêmios reais: quais são e com que critério (posição no ranking, metas).

## Fases

1. Servidor e login: contas, progresso e sorteios no servidor; o app pede login.
2. Migração do progresso local do usuário.
3. Conferência de atendimentos pela API do AnyDesk.
4. Ranking, prêmios e painel do administrador.
