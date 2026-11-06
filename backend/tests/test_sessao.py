import os
import unittest
from unittest import mock

from tests.test_seguranca import SENHA, BaseTeste

SENHA_NOVA = "novasenha456"


class TestTokenAposTrocaDeSenha(BaseTeste):

    def test_token_antigo_recusado_depois_da_troca_de_senha(self):
        usuario, token = self.criar_usuario_logado("Troca Senha")
        resposta = self.cli.put(
            f"/api/usuarios/{usuario['id']}",
            json={"senha": SENHA_NOVA, "senha_atual": SENHA},
            headers=self.auth(token),
        )
        self.assertEqual(resposta.status_code, 200, resposta.get_data(as_text=True))
        antigo = self.cli.get("/api/eu", headers=self.auth(token))
        self.assertEqual(antigo.status_code, 401)

    def test_token_devolvido_na_troca_de_senha_continua_valido(self):
        usuario, token = self.criar_usuario_logado("Troca Senha Novo")
        resposta = self.cli.put(
            f"/api/usuarios/{usuario['id']}",
            json={"senha": SENHA_NOVA, "senha_atual": SENHA},
            headers=self.auth(token),
        )
        novo_token = resposta.get_json()["token"]
        self.assertEqual(self.cli.get("/api/eu", headers=self.auth(novo_token)).status_code, 200)

    def test_login_com_senha_nova_funciona(self):
        usuario, token = self.criar_usuario_logado("Troca Login")
        self.cli.put(
            f"/api/usuarios/{usuario['id']}",
            json={"senha": SENHA_NOVA, "senha_atual": SENHA},
            headers=self.auth(token),
        )
        resposta = self.cli.post("/api/login", json={"email": usuario["email"], "senha": SENHA_NOVA})
        self.assertEqual(resposta.status_code, 200)


class TestLimiteDeLoginPorIp(BaseTeste):

    def setUp(self):
        super().setUp()
        self.usuario = self.cadastrar("Limite Ip")

    def tentar(self, senha, ip, xff=None):
        cabecalhos = {"X-Forwarded-For": xff} if xff else {}
        return self.cli.post(
            "/api/login",
            json={"email": self.usuario["email"], "senha": senha},
            headers=cabecalhos,
            environ_base={"REMOTE_ADDR": ip},
        )

    def test_bloqueio_do_ip_nao_bloqueia_o_mesmo_email_de_outro_ip(self):
        for _ in range(5):
            self.assertEqual(self.tentar("errada12345", "10.0.0.5").status_code, 401)
        self.assertEqual(self.tentar("errada12345", "10.0.0.5").status_code, 429)
        self.assertEqual(self.tentar(SENHA, "10.0.0.6").status_code, 200)

    def test_x_forwarded_for_e_ignorado_sem_trust_proxy(self):
        with mock.patch.dict(os.environ, {}):
            os.environ.pop("TRUST_PROXY", None)
            for indice in range(5):
                self.assertEqual(
                    self.tentar("errada12345", "10.0.0.5", xff=f"203.0.113.{indice}").status_code, 401
                )
            self.assertEqual(self.tentar("errada12345", "10.0.0.5", xff="203.0.113.99").status_code, 429)

    def test_x_forwarded_for_vale_quando_trust_proxy_esta_ligado(self):
        with mock.patch.dict(os.environ, {"TRUST_PROXY": "1"}):
            for _ in range(5):
                self.assertEqual(self.tentar("errada12345", "10.0.0.5", xff="203.0.113.7").status_code, 401)
            self.assertEqual(self.tentar("errada12345", "10.0.0.5", xff="203.0.113.7").status_code, 429)
            self.assertEqual(self.tentar("errada12345", "10.0.0.5", xff="203.0.113.8").status_code, 401)


if __name__ == "__main__":
    unittest.main()
