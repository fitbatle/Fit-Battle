import io
import unittest

from tests.test_seguranca import BaseTeste

PNG_VALIDO = b"\x89PNG\r\n\x1a\n" + b"\x00" * 16


class TestCabecalhosDaApi(BaseTeste):

    def afirmar_cabecalhos_basicos(self, resposta):
        self.assertEqual(resposta.headers.get("X-Content-Type-Options"), "nosniff")
        self.assertEqual(resposta.headers.get("X-Frame-Options"), "DENY")
        self.assertEqual(resposta.headers.get("Referrer-Policy"), "no-referrer")

    def test_resposta_publica_da_api_traz_cabecalhos_basicos(self):
        resposta = self.cli.post("/api/login", json={"email": "ninguem@teste.com", "senha": "errada123"})
        self.afirmar_cabecalhos_basicos(resposta)

    def test_resposta_autenticada_traz_cabecalhos_basicos_e_no_store(self):
        _, token = self.criar_usuario_logado("Cabecalho Teste")
        resposta = self.cli.get("/api/eu", headers=self.auth(token))
        self.assertEqual(resposta.status_code, 200)
        self.afirmar_cabecalhos_basicos(resposta)
        self.assertIn("no-store", resposta.headers.get("Cache-Control", ""))

    def test_erro_da_api_tambem_traz_cabecalhos_basicos(self):
        resposta = self.cli.get("/api/nao-existe")
        self.assertEqual(resposta.status_code, 404)
        self.afirmar_cabecalhos_basicos(resposta)

    def test_upload_continua_sendo_servido_como_imagem(self):
        usuario, token = self.criar_usuario_logado("Upload Cabecalho")
        envio = self.cli.post(
            f"/api/usuarios/{usuario['id']}/foto",
            data={"foto": (io.BytesIO(PNG_VALIDO), "avatar.png")},
            content_type="multipart/form-data",
            headers=self.auth(token),
        )
        self.assertEqual(envio.status_code, 200, envio.get_data(as_text=True))
        caminho = "/" + envio.get_json()["usuario"]["foto"].lstrip("/")
        resposta = self.cli.get(caminho)
        self.assertEqual(resposta.status_code, 200)
        self.assertEqual(resposta.mimetype, "image/png")
        self.assertEqual(resposta.headers.get("X-Content-Type-Options"), "nosniff")
        self.assertEqual(resposta.get_data(), PNG_VALIDO)


if __name__ == "__main__":
    unittest.main()
