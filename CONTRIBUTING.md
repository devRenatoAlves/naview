# Contribuindo com o NaView

Obrigado pelo interesse! Projeto pequeno, mantido por pouca gente, então o fluxo é simples.

## Antes de abrir um PR

- **Abra uma issue primeiro** para mudanças que não sejam correção pequena — alinhar a ideia
  evita trabalho perdido.
- **Teste em mais de um sistema sempre que possível.** O NaView roda em vários Linux (GNOME, KDE)
  e em Windows; evite qualquer caminho, usuário, ambiente de desktop ou atalho fixo de uma
  máquina só. Se não puder testar num dos sistemas, diga isso no PR.
- **Leve e fluido**: o app fica aberto o dia todo com sessões remotas em aba. Nada de animação
  contínua sem necessidade, timer que repinta a tela parada, ou efeito caro (desfoque grande,
  sombra grande, gradiente radial). Anime só quando a tela está visível.
- **Arte e sons originais** (scripts em `ferramentas/`), exceto os três pets de Pokémon em
  `arte/pets/` (arte de fã, ver aviso no README) — não adicione mais sprites de propriedade de
  terceiros sem marcar a licença/origem.
- Interface em português, sem emoji; ícones são [Phosphor](https://phosphoricons.com/).

## Rodando localmente

```
python3 app.py
```

Veja o README para dependências (GTK3/PyGObject, WebKit2, GStreamer) e a versão Qt em teste.

## Testes

Veja `ferramentas/` para os scripts de geração de arte/economia do jogo. Se mudar um número da
economia do jogo, rode `python3 ferramentas/simular_economia.py` e confira o resultado.

## Estilo de commit

Mensagens curtas, descrevendo o efeito da mudança (`tipo: o que mudou`), em português, como o
restante do histórico do projeto.

## Dúvidas

Abra uma issue.
