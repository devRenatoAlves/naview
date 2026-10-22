#!/usr/bin/env python3
"""Sobe o número da versão no arquivo VERSAO (formato AAAA.MM.DD.N, N recomeça em 1 a cada dia).

Uso: python3 ferramentas/nova_versao.py

Rodar antes de cada push que deva chegar aos usuários: o app só oferece a atualização quando o
número é maior que o instalado (ver docs/sdd/specs/07-atualizacao.md). Não faz commit.
"""
import datetime
from pathlib import Path

ARQUIVO = Path(__file__).resolve().parent.parent / "VERSAO"


def proxima(atual, hoje):
    """'2026.10.22.3' -> '2026.10.22.4' no mesmo dia; em outro dia, '<hoje>.1'."""
    partes = atual.strip().split(".")
    if ".".join(partes[:3]) == hoje:
        n = int(partes[3]) if len(partes) > 3 else 0
        return f"{hoje}.{n + 1}"
    return f"{hoje}.1"


def main():
    antiga = ARQUIVO.read_text().strip() if ARQUIVO.is_file() else ""
    nova = proxima(antiga, datetime.date.today().strftime("%Y.%m.%d"))
    ARQUIVO.write_text(nova + "\n")
    print(f"{antiga or '(nenhuma)'} -> {nova}")


if __name__ == "__main__":
    main()
