import unittest

from tests.test_seguranca import BaseTeste


class TestRankingRegionalNormalizado(BaseTeste):

    def criar_com_local(self, nome, cidade, estado):
        usuario, token = self.criar_usuario_logado(nome)
        resposta = self.cli.put(
            f"/api/usuarios/{usuario['id']}",
            json={"cidade": cidade, "estado": estado},
            headers=self.auth(token),
        )
        self.assertEqual(resposta.status_code, 200, resposta.get_data(as_text=True))
        return usuario

    def nomes(self, query):
        _, token = self.criar_usuario_logado("Consulta " + str(abs(hash(str(query))))[:6])
        resposta = self.cli.get("/api/ranking/regional", query_string=query, headers=self.auth(token))
        self.assertEqual(resposta.status_code, 200, resposta.get_data(as_text=True))
        return [item["nome"] for item in resposta.get_json()]

    def setUp(self):
        super().setUp()
        self.sp_a = self.criar_com_local("Regional Paulista A", "São Paulo", "SP")
        self.sp_b = self.criar_com_local("Regional Paulista B", "sao paulo ", "SP")
        self.sp_c = self.criar_com_local("Regional Paulista C", "SÃO PAULO", "sp")
        self.campinas = self.criar_com_local("Regional Campineira", "Campinas", "SP")
        self.mineira = self.criar_com_local("Regional Mineira", "Belo Horizonte", "MG")

    def test_cidade_casa_ignorando_caixa_acentos_e_espacos_nas_pontas(self):
        nomes = self.nomes({"cidade": "sao paulo"})
        self.assertEqual(sorted(nomes), sorted(["Regional Paulista A", "Regional Paulista B", "Regional Paulista C"]), nomes)

    def test_cidade_com_acento_e_caixa_diferentes_casa_a_mesma_cidade(self):
        nomes = self.nomes({"cidade": "  são PAULO  "})
        self.assertEqual(len(nomes), 3, nomes)

    def test_outra_cidade_nao_entra_no_ranking(self):
        nomes = self.nomes({"cidade": "Campinas"})
        self.assertEqual(nomes, ["Regional Campineira"], nomes)

    def test_filtro_por_estado_ignora_caixa_e_inclui_todas_as_cidades_do_estado(self):
        nomes = self.nomes({"estado": "sp"})
        self.assertEqual(
            sorted(nomes),
            sorted(["Regional Paulista A", "Regional Paulista B", "Regional Paulista C", "Regional Campineira"]),
            nomes,
        )

    def test_filtro_por_estado_nao_traz_outro_estado(self):
        nomes = self.nomes({"estado": "MG"})
        self.assertEqual(nomes, ["Regional Mineira"], nomes)

    def test_sem_cidade_nem_estado_devolve_400(self):
        _, token = self.criar_usuario_logado("Sem Parametro")
        resposta = self.cli.get("/api/ranking/regional", headers=self.auth(token))
        self.assertEqual(resposta.status_code, 400)

    def test_posicao_e_recalculada_dentro_do_grupo_normalizado(self):
        _, token = self.criar_usuario_logado("Posicao Consulta")
        resposta = self.cli.get("/api/ranking/regional", query_string={"cidade": "sao paulo"}, headers=self.auth(token))
        posicoes = [item["posicao"] for item in resposta.get_json()]
        self.assertEqual(len(posicoes), 3, posicoes)
        self.assertEqual(sorted(set(posicoes)), [1], posicoes)


if __name__ == "__main__":
    unittest.main()
