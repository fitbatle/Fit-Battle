import io
import os
import unittest
from contextlib import redirect_stderr
from unittest import mock

os.environ["DB_URI"] = "sqlite:///:memory:"

from app import uri_do_banco

VARIAVEIS_DE_BANCO = ("DB_URI", "DB_PASSWORD", "DB_USER", "DB_HOST", "DB_PORT", "DB_NAME", "FITBATTLE_ENV")


def ambiente_sem_banco(**extras):
    limpo = {chave: valor for chave, valor in os.environ.items() if chave not in VARIAVEIS_DE_BANCO}
    limpo.update(extras)
    return mock.patch.dict(os.environ, limpo, clear=True)


class TestConfiguracaoDoBanco(unittest.TestCase):

    def test_desenvolvimento_sem_senha_usa_padrao_e_imprime_aviso(self):
        with ambiente_sem_banco():
            aviso = io.StringIO()
            with redirect_stderr(aviso):
                uri = uri_do_banco()
        self.assertIn("Fitbattle%40123", uri)
        self.assertIn("AVISO", aviso.getvalue())
        self.assertIn("DB_PASSWORD", aviso.getvalue())

    def test_producao_sem_senha_recusa_iniciar_com_mensagem_clara(self):
        with ambiente_sem_banco(FITBATTLE_ENV="production"):
            with self.assertRaises(RuntimeError) as contexto:
                uri_do_banco()
        self.assertIn("DB_PASSWORD", str(contexto.exception))

    def test_com_senha_definida_usa_a_variavel_sem_aviso(self):
        with ambiente_sem_banco(DB_PASSWORD="senha-do-ambiente", FITBATTLE_ENV="production"):
            aviso = io.StringIO()
            with redirect_stderr(aviso):
                uri = uri_do_banco()
        self.assertIn("senha-do-ambiente", uri)
        self.assertNotIn("Fitbattle%40123", uri)
        self.assertEqual(aviso.getvalue(), "")

    def test_db_uri_completa_dispensa_a_senha_mesmo_em_producao(self):
        with ambiente_sem_banco(DB_URI="sqlite:///:memory:", FITBATTLE_ENV="production"):
            self.assertEqual(uri_do_banco(), "sqlite:///:memory:")


if __name__ == "__main__":
    unittest.main()
