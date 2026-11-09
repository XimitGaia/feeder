"""Escolha do modo de execução (prod/test), espelhando o padrão do oxossi.

Em runtime, o `Injector` devolve o initializer ativo. Em testes, o
`tests/__init__.py` chama `set_test_injector()` para bindar stubs sem I/O real.
Ver docs/adr/0003.
"""

from __future__ import annotations

from src import initializer


class Injector:
    _injector = initializer

    @classmethod
    def set_test_injector(cls):
        try:
            from tests import test_initializer  # noqa: PLC0415 — só no modo teste

            cls._injector = test_initializer
        except ImportError:
            pass

    @classmethod
    def get_injector(cls):
        return cls._injector
