"""Leitura/escrita simples do arquivo `.env` — usado pela UI para persistir as
chaves que o usuário digita (OpenRouter, WordPress) sem editar o arquivo à mão.

Preserva as linhas existentes (comentários incluídos); atualiza a chave se ela
já existe, ou acrescenta no fim se for nova.
"""

from __future__ import annotations

import re
from pathlib import Path

_LINE = re.compile(r"^\s*([A-Z0-9_]+)\s*=")


def update_env(path: str | Path, updates: dict[str, str]) -> None:
    path = Path(path)
    lines = path.read_text(encoding="utf-8").splitlines() if path.exists() else []
    seen: set[str] = set()
    out: list[str] = []
    for line in lines:
        m = _LINE.match(line)
        if m and m.group(1) in updates:
            key = m.group(1)
            out.append(f'{key} = "{updates[key]}"')
            seen.add(key)
        else:
            out.append(line)
    for key, value in updates.items():
        if key not in seen:
            out.append(f'{key} = "{value}"')
    path.write_text("\n".join(out) + "\n", encoding="utf-8")
