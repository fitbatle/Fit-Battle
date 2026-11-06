import os
import unittest
from unittest import mock

from database import db
from models.model import Usuario
from services.email import EnviarEmailService
from tests.test_seguranca import BaseTeste

CONFIG_SMTP = {
    "SMTP_HOST": "smtp.teste.local",
    "SMTP_PORT": "2525",
    "SMTP_USER": "envio@teste.local",
    "SMTP_PASSWORD": "senha-de-teste",
    "SMTP_FROM": "FitBattle <envio@teste.local>",
}


class TestEnviarEmailService(BaseTeste):

    def setUp(self):
        super().setUp()
        self.contexto = self.app.app_context()
        self.contexto.push()
        usuario = Usuario(nome="Envio Teste", email="envio.destino@exemplo.com", senha="hash")
        usuario.salvar()
        self.id_usuario = usuario.id_usuario

    def tearDown(self):
        db.session.remove()
        self.contexto.pop()
        super().tearDown()

    def test_sem_smtp_configurado_nao_tenta_enviar_e_devolve_false(self):
        with mock.patch.dict("os.environ", {}, clear=False):
            os.environ.pop("SMTP_HOST", None)
            with mock.patch("smtplib.SMTP") as smtp_mock:
                resultado = EnviarEmailService.executar(self.id_usuario, "Olá")
        self.assertFalse(resultado)
        smtp_mock.assert_not_called()

    def test_envio_com_sucesso_usa_login_e_devolve_true(self):
        with mock.patch.dict("os.environ", CONFIG_SMTP):
            with mock.patch("smtplib.SMTP") as smtp_mock:
                resultado = EnviarEmailService.executar(self.id_usuario, "Você ganhou uma medalha")
        self.assertTrue(resultado)
        smtp_mock.assert_called_once_with("smtp.teste.local", 2525, timeout=5)
        servidor = smtp_mock.return_value.__enter__.return_value
        servidor.starttls.assert_called_once()
        servidor.login.assert_called_once_with("envio@teste.local", "senha-de-teste")
        servidor.send_message.assert_called_once()
        mensagem = servidor.send_message.call_args[0][0]
        self.assertEqual(mensagem["To"], "envio.destino@exemplo.com")
        self.assertEqual(mensagem["From"], "FitBattle <envio@teste.local>")
        self.assertEqual(mensagem["Subject"], "FitBattle")
        self.assertIn("Você ganhou uma medalha", mensagem.get_content())

    def test_envio_sem_credenciais_nao_faz_login(self):
        config = {chave: valor for chave, valor in CONFIG_SMTP.items() if chave not in ("SMTP_USER", "SMTP_PASSWORD")}
        with mock.patch.dict("os.environ", config):
            os.environ.pop("SMTP_USER", None)
            os.environ.pop("SMTP_PASSWORD", None)
            with mock.patch("smtplib.SMTP") as smtp_mock:
                resultado = EnviarEmailService.executar(self.id_usuario, "Olá")
        self.assertTrue(resultado)
        servidor = smtp_mock.return_value.__enter__.return_value
        servidor.starttls.assert_not_called()
        servidor.login.assert_not_called()

    def test_falha_no_envio_nao_levanta_erro_e_devolve_false(self):
        with mock.patch.dict("os.environ", CONFIG_SMTP):
            with mock.patch("smtplib.SMTP", side_effect=OSError("timeout")):
                resultado = EnviarEmailService.executar(self.id_usuario, "Olá")
        self.assertFalse(resultado)

    def test_usuario_inexistente_nao_envia(self):
        with mock.patch.dict("os.environ", CONFIG_SMTP):
            with mock.patch("smtplib.SMTP") as smtp_mock:
                resultado = EnviarEmailService.executar(999999, "Olá")
        self.assertFalse(resultado)
        smtp_mock.assert_not_called()


if __name__ == "__main__":
    unittest.main()
