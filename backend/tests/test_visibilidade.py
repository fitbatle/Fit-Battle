import os
import sys
import unittest

os.environ["DB_URI"] = "sqlite:///:memory:"
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tests.test_seguranca import BaseTeste, data_nascimento_para_idade


class TestVisibilidadeDoFeedEAcoes(BaseTeste):

    def setUp(self):
        super().setUp()
        self.ana, self.token_ana = self.criar_usuario_logado("Ana Publica", idade=30)
        self.bia, self.token_bia = self.criar_usuario_logado("Bia Privada", idade=31)
        self.lia, self.token_lia = self.criar_usuario_logado(
            "Lia Menor", idade=15, responsavel={"nome": "Responsavel Teste", "email": "resp.lia@teste.com"}
        )
        self.carla, self.token_carla = self.criar_usuario_logado("Carla Comum", idade=28)
        self.duda, self.token_duda = self.criar_usuario_logado("Duda Membro", idade=29)
        self.revogar_ranking_publico(self.bia, self.token_bia)
        self.entrar_no_grupo_da_ana()
        self.conteudos = {}
        for dono, token in ((self.ana, self.token_ana), (self.bia, self.token_bia), (self.lia, self.token_lia)):
            self.conteudos[dono["id"]] = self.criar_conteudo(dono, token)

    def revogar_ranking_publico(self, usuario, token):
        resposta = self.cli.put(
            f"/api/usuarios/{usuario['id']}/consentimentos/ranking_publico",
            json={"aceito": False}, headers=self.auth(token),
        )
        self.assertEqual(resposta.status_code, 200, resposta.get_data(as_text=True))

    def entrar_no_grupo_da_ana(self):
        grupo = self.cli.post("/api/grupos", json={"nome": "Turma Teste"}, headers=self.auth(self.token_ana))
        self.assertEqual(grupo.status_code, 201, grupo.get_data(as_text=True))
        id_grupo = grupo.get_json()["grupo"]["id"]
        codigo = self.cli.get(f"/api/grupos/{id_grupo}/convite", headers=self.auth(self.token_ana)).get_json()["codigo"]
        entrada = self.cli.post("/api/grupos/entrar", json={"codigo": codigo}, headers=self.auth(self.token_duda))
        self.assertEqual(entrada.status_code, 200, entrada.get_data(as_text=True))

    def criar_conteudo(self, dono, token):
        treino = self.cli.post(
            f"/api/usuarios/{dono['id']}/atividades",
            json={"tipo": "cardio", "titulo": "Corrida teste", "tempo_min": 20},
            headers=self.auth(token),
        )
        self.assertEqual(treino.status_code, 201, treino.get_data(as_text=True))
        postagem = self.cli.post(
            "/api/postagens", data={"texto": "Post teste"},
            headers=self.auth(token), content_type="multipart/form-data",
        )
        self.assertEqual(postagem.status_code, 201, postagem.get_data(as_text=True))
        return {
            "atividade": treino.get_json()["atividade"]["id"],
            "postagem": postagem.get_json()["postagem"].get("id") or postagem.get_json()["postagem"].get("id_postagem"),
        }

    def itens_do_feed(self, token):
        resposta = self.cli.get("/api/feed?limite=100", headers=self.auth(token))
        self.assertEqual(resposta.status_code, 200)
        return {(item["tipo_conteudo"], item["id"]) for item in resposta.get_json()}

    def acoes(self, token, tipo, id_conteudo):
        caminho = f"/api/feed/{tipo}/{id_conteudo}"
        curtir = self.cli.post(f"{caminho}/curtir", headers=self.auth(token)).status_code
        comentar = self.cli.post(
            f"{caminho}/comentarios", json={"texto": "Comentario de visitante"}, headers=self.auth(token),
        ).status_code
        listar = self.cli.get(f"{caminho}/comentarios", headers=self.auth(token)).status_code
        return curtir, comentar, listar

    def test_tela_entrega_o_conteudo_se_e_so_se_as_acoes_funcionam(self):
        visitantes = {
            "dono": (self.ana, self.token_ana),
            "outro usuario comum": (self.carla, self.token_carla),
            "membro do mesmo grupo": (self.duda, self.token_duda),
        }
        entregues = []
        donos = {"adulto com perfil publico": self.ana, "adulto com perfil privado": self.bia, "menor de idade": self.lia}
        for nome_dono, dono in donos.items():
            for nome_visitante, (visitante, token) in visitantes.items():
                itens = self.itens_do_feed(token)
                conteudos = self.conteudos[dono["id"]]
                for tipo, id_conteudo in conteudos.items():
                    with self.subTest(dono=nome_dono, visitante=nome_visitante, conteudo=tipo):
                        entregue = (tipo_feed(tipo), id_conteudo) in itens
                        curtir, comentar, listar = self.acoes(token, tipo_feed(tipo), id_conteudo)
                        entregues.append(entregue)
                        if entregue:
                            self.assertEqual((curtir, comentar, listar), (200, 201, 200))
                        else:
                            self.assertEqual((curtir, comentar, listar), (404, 404, 404))
        self.assertIn(True, entregues)
        self.assertIn(False, entregues)


def tipo_feed(tipo):
    return "atividade" if tipo == "atividade" else "postagem"


if __name__ == "__main__":
    unittest.main()
