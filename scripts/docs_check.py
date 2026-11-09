#!/usr/bin/env python3
"""Gate de documentação (regra inegociável do repo — herdada do oxossi).

Toda mudança de **código** precisa vir acompanhada de atualização de
**documentação** no mesmo commit. Se algum arquivo de código for commitado sem
ao menos um arquivo de documentação (`*.md`), o commit é bloqueado.

O que conta como CÓDIGO: `*.py` sob `src/` e os entrypoints da raiz
(`main.py`, `injector.py`). Testes (`tests/`) e tooling (`scripts/`) não exigem doc.

O que SATISFAZ a regra: qualquer arquivo `*.md` no commit — README, um ADR,
`docs/FLOWS.md`, `docs/MVP.md`, `CLAUDE.md`/`AGENTS.md`, etc.

Exceção consciente:
    SKIP=docs-check git commit ...
"""

from __future__ import annotations

import subprocess
import sys

CODE_ROOT_FILES = {"main.py", "injector.py"}


def staged_files() -> list[str]:
    out = subprocess.run(
        ["git", "diff", "--cached", "--name-only", "--diff-filter=ACMR"],
        capture_output=True,
        text=True,
        check=True,
    ).stdout
    return [line.strip() for line in out.splitlines() if line.strip()]


def is_code(path: str) -> bool:
    if path.endswith(".md"):
        return False
    if path in CODE_ROOT_FILES:
        return True
    return path.startswith("src/") and path.endswith(".py")


def is_doc(path: str) -> bool:
    return path.endswith(".md")


def main() -> int:
    files = staged_files()
    code = [f for f in files if is_code(f)]
    docs = [f for f in files if is_doc(f)]

    if code and not docs:
        print("\n\033[31m✖ docs-check: mudança de código sem atualização de documentação.\033[0m")
        print("  Arquivos de código no commit:")
        for f in code:
            print(f"    - {f}")
        print("  Inclua ao menos um arquivo .md (README de flow, ADR, docs/*).")
        print("  Exceção consciente: SKIP=docs-check git commit ...")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
