from datetime import datetime, timedelta

from models.model import Notificacao, Usuario
from repositories.repository import NotificacaoRepository
from tests.test_seguranca import BaseTeste

HOJE = datetime(2026, 1, 20, 12, 0)


def criar_usuario(email):
    return Usuario(nome=email.split("@")[0], email=email, senha="hash", idade=30).salvar()


def notificar(id_usuario, mensagem, quando=HOJE, lida=False):
    return Notificacao(
        id_usuario=id_usuario, tipo="comentario", mensagem=mensagem, lida=lida, data_envio=quando,
    ).salvar()


class TestNotificacaoRepository(BaseTeste):

    def test_existe_acha_a_mesma_mensagem_do_mesmo_tipo(self):
        with self.app.app_context():
            ana = criar_usuario("notif.existe@repo.teste")
            notificar(ana.id_usuario, "Voce ganhou")
            achada = NotificacaoRepository.existe(ana.id_usuario, "comentario", "Voce ganhou")
            outra = NotificacaoRepository.existe(ana.id_usuario, "comentario", "Outra")
        self.assertIsNotNone(achada)
        self.assertIsNone(outra)

    def test_listar_do_usuario_do_mais_recente_e_respeita_o_limite(self):
        with self.app.app_context():
            ana = criar_usuario("notif.lista@repo.teste")
            notificar(ana.id_usuario, "Antiga", quando=HOJE - timedelta(days=2))
            notificar(ana.id_usuario, "Nova", quando=HOJE)
            notificar(ana.id_usuario, "Media", quando=HOJE - timedelta(days=1))
            linhas = NotificacaoRepository.listar_do_usuario(ana.id_usuario, limite=2)
        self.assertEqual([n["mensagem"] for n in linhas], ["Nova", "Media"])
        self.assertIs(linhas[0]["lida"], False)
        self.assertIsInstance(linhas[0]["data_envio"], datetime)

    def test_contar_nao_lidas_ignora_as_lidas(self):
        with self.app.app_context():
            ana = criar_usuario("notif.conta@repo.teste")
            notificar(ana.id_usuario, "Um")
            notificar(ana.id_usuario, "Dois")
            notificar(ana.id_usuario, "Lida", lida=True)
            total = NotificacaoRepository.contar_nao_lidas(ana.id_usuario)["total"]
        self.assertEqual(total, 2)

    def test_marcar_todas_lidas_so_mexe_nas_do_usuario(self):
        with self.app.app_context():
            ana = criar_usuario("notif.marca.a@repo.teste")
            bia = criar_usuario("notif.marca.b@repo.teste")
            notificar(ana.id_usuario, "Dela")
            notificar(bia.id_usuario, "Da Bia")
            NotificacaoRepository.marcar_todas_lidas(ana.id_usuario)
            ana_nao_lidas = NotificacaoRepository.contar_nao_lidas(ana.id_usuario)["total"]
            bia_nao_lidas = NotificacaoRepository.contar_nao_lidas(bia.id_usuario)["total"]
        self.assertEqual(ana_nao_lidas, 0)
        self.assertEqual(bia_nao_lidas, 1)
