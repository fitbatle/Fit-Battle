import unittest

from tests.test_seguranca import BaseTeste

ORIGEM_LOCAL = "http://127.0.0.1:5500"
ORIGEM_REDE_LOCAL = "http://192.168.0.10:5500"
ORIGEM_EXTERNA = "https://site-externo.exemplo"
CABECALHOS_PERMITIDOS = "Authorization, Content-Type"


class TestCors(BaseTeste):

    def pre_requisicao(self, origem, caminho="/api/eu"):
        return self.cli.open(
            caminho,
            method="OPTIONS",
            headers={
                "Origin": origem,
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": CABECALHOS_PERMITIDOS,
            },
        )

    def requisicao_real(self, origem):
        usuario, token = self.criar_usuario_logado("Cors Teste")
        return self.cli.get(
            "/api/eu",
            headers={"Origin": origem, "Authorization": "Bearer " + token},
        )

    def test_pre_requisicao_de_localhost_com_authorization_e_content_type_e_aceita(self):
        resposta = self.pre_requisicao(ORIGEM_LOCAL)
        self.assertIn(resposta.status_code, (200, 204))
        self.assertEqual(resposta.headers.get("Access-Control-Allow-Origin"), ORIGEM_LOCAL)
        cabecalhos = resposta.headers.get("Access-Control-Allow-Headers", "").lower()
        self.assertIn("authorization", cabecalhos)
        self.assertIn("content-type", cabecalhos)

    def test_requisicao_real_de_localhost_recebe_origem_de_volta(self):
        resposta = self.requisicao_real(ORIGEM_LOCAL)
        self.assertEqual(resposta.status_code, 200)
        self.assertEqual(resposta.headers.get("Access-Control-Allow-Origin"), ORIGEM_LOCAL)

    def test_pre_requisicao_de_rede_local_192_168_e_aceita(self):
        resposta = self.pre_requisicao(ORIGEM_REDE_LOCAL)
        self.assertIn(resposta.status_code, (200, 204))
        self.assertEqual(resposta.headers.get("Access-Control-Allow-Origin"), ORIGEM_REDE_LOCAL)

    def test_requisicao_real_de_rede_local_192_168_recebe_origem_de_volta(self):
        resposta = self.requisicao_real(ORIGEM_REDE_LOCAL)
        self.assertEqual(resposta.status_code, 200)
        self.assertEqual(resposta.headers.get("Access-Control-Allow-Origin"), ORIGEM_REDE_LOCAL)

    def test_pre_requisicao_de_origem_externa_nao_recebe_permissao(self):
        resposta = self.pre_requisicao(ORIGEM_EXTERNA)
        self.assertNotEqual(resposta.headers.get("Access-Control-Allow-Origin"), ORIGEM_EXTERNA)
        self.assertNotEqual(resposta.headers.get("Access-Control-Allow-Origin"), "*")

    def test_requisicao_real_de_origem_externa_nao_recebe_permissao(self):
        resposta = self.requisicao_real(ORIGEM_EXTERNA)
        self.assertNotEqual(resposta.headers.get("Access-Control-Allow-Origin"), ORIGEM_EXTERNA)
        self.assertNotEqual(resposta.headers.get("Access-Control-Allow-Origin"), "*")


if __name__ == "__main__":
    unittest.main()
