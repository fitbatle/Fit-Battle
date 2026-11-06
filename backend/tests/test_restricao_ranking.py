from database import db
from models.model import Usuario
from tests.test_seguranca import BaseTeste

RESPONSAVEL = {"nome": "Responsavel Restricao", "email": "resp.restricao@teste.com"}


class TestRestricaoDeRankingPorIdade(BaseTeste):

    def situacao(self, usuario, token):
        resposta = self.cli.get(f"/api/usuarios/{usuario['id']}/ranking", headers=self.auth(token))
        self.assertEqual(resposta.status_code, 200, resposta.get_data(as_text=True))
        return resposta.get_json()

    def test_menor_de_idade_recebe_a_restricao(self):
        menor, token = self.criar_usuario_logado(
            "Menor Restricao", idade=15, responsavel=RESPONSAVEL, consentimentos={"ranking_publico": True}
        )
        self.assertEqual(self.situacao(menor, token)["restricao"], "menor_de_idade")

    def test_maior_de_idade_nao_recebe_restricao(self):
        adulto, token = self.criar_usuario_logado("Adulta Restricao", idade=25)
        self.assertIsNone(self.situacao(adulto, token)["restricao"])

    def test_usuario_sem_data_de_nascimento_nao_recebe_restricao(self):
        usuario, token = self.criar_usuario_logado("Sem Data Restricao", idade=25)
        with self.app.app_context():
            registro = db.session.get(Usuario, usuario["id"])
            registro.data_nascimento = None
            registro.idade = None
            db.session.commit()
        self.assertIsNone(self.situacao(usuario, token)["restricao"])

    def test_menor_de_idade_fica_fora_do_ranking_publico(self):
        menor, token = self.criar_usuario_logado(
            "Menor Fora Ranking", idade=15, responsavel=RESPONSAVEL, consentimentos={"ranking_publico": True}
        )
        ranking = self.cli.get("/api/ranking/global", headers=self.auth(token)).get_json()
        self.assertFalse(any(item["id_usuario"] == menor["id"] for item in ranking))
        self.assertEqual(self.situacao(menor, token)["restricao"], "menor_de_idade")
