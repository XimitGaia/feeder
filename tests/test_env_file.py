"""Teste do gravador de .env (atualiza existentes, acrescenta novas, preserva)."""

from __future__ import annotations

from src.core.env_file import update_env


def test_atualiza_existente_e_acrescenta_nova(tmp_path):
    env = tmp_path / ".env"
    env.write_text('# comentário\nOPENROUTER_API_KEY = ""\nOUTRA = "x"\n', encoding="utf-8")

    update_env(env, {"OPENROUTER_API_KEY": "sk-123", "WORDPRESS_URL": "https://site"})

    texto = env.read_text(encoding="utf-8")
    assert '# comentário' in texto  # preserva comentário
    assert 'OPENROUTER_API_KEY = "sk-123"' in texto  # atualiza existente
    assert 'OUTRA = "x"' in texto  # preserva outras
    assert 'WORDPRESS_URL = "https://site"' in texto  # acrescenta nova
    # não duplica a chave atualizada
    assert texto.count("OPENROUTER_API_KEY") == 1
