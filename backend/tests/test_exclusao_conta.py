import unittest

from database import db
from models.model import Usuario
from tests.test_seguranca import BaseTeste


class TestFluxoExclusaoConta(BaseTeste):

    def setUp(self):
        super().setUp()
        self.ana, self.token_ana = self.criar_usuario_logado("Ana Silva")
        self.bia, self.token_bia = self.criar_usuario_logado("Bia Costa")

    def _existe(self, id_usuario):
        with self.app.app_context():
            return Usuario.query.filter_by(id_usuario=id_usuario).first() is not None

    def test_usuario_apaga_a_propria_conta_e_ela_some_do_banco(self):
        exclusao = self.cli.delete(f"/api/usuarios/{self.ana['id']}", headers=self.auth(self.token_ana))
        self.assertEqual(exclusao.status_code, 200)
        self.assertFalse(self._existe(self.ana["id"]))
        self.assertTrue(self._existe(self.bia["id"]))

    def test_token_antigo_deixa_de_funcionar_depois_da_exclusao(self):
        self.cli.delete(f"/api/usuarios/{self.ana['id']}", headers=self.auth(self.token_ana))
        resposta = self.cli.get("/api/eu", headers=self.auth(self.token_ana))
        self.assertEqual(resposta.status_code, 401)

    def test_login_com_a_conta_excluida_e_recusado(self):
        self.cli.delete(f"/api/usuarios/{self.ana['id']}", headers=self.auth(self.token_ana))
        resposta = self.cli.post("/api/login", json={"email": self.ana["email"], "senha": "senhaforte123"})
        self.assertNotEqual(resposta.status_code, 200)

    def test_outro_usuario_recebe_403_e_a_conta_permanece(self):
        resposta = self.cli.delete(f"/api/usuarios/{self.ana['id']}", headers=self.auth(self.token_bia))
        self.assertEqual(resposta.status_code, 403)
        self.assertTrue(self._existe(self.ana["id"]))
        self.assertEqual(self.cli.get("/api/eu", headers=self.auth(self.token_ana)).status_code, 200)


if __name__ == "__main__":
    unittest.main()
