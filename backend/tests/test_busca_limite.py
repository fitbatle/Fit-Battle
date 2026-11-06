import unittest

from tests.test_seguranca import BaseTeste

CONSENTIMENTOS_BUSCA = {"busca_perfil": True, "ranking_publico": True}
RESPONSAVEL = {"nome": "Responsavel Busca", "email": "responsavel.busca@teste.com"}


class TestBuscaAplicaFiltrosAntesDoLimite(BaseTeste):

    def setUp(self):
        super().setUp()
        self.quem_busca, self.token = self.criar_usuario_logado("Quem Busca")

    def buscar(self, termo):
        resposta = self.cli.get("/api/usuarios/busca", query_string={"nome": termo}, headers=self.auth(self.token))
        self.assertEqual(resposta.status_code, 200, resposta.get_data(as_text=True))
        return resposta.get_json()

    def test_mais_de_vinte_menores_nao_ocupam_as_vagas_dos_adultos(self):
        for indice in range(25):
            self.cadastrar(
                f"Busca Lote 0 Menor {indice:02d}", email=f"menor.busca.{indice}@teste.com", idade=15,
                consentimentos=CONSENTIMENTOS_BUSCA, responsavel=RESPONSAVEL,
            )
        adultos = []
        for letra in ("A", "B"):
            adultos.append(self.cadastrar(f"Busca Lote Z Adulta {letra}", email=f"adulta.busca.{letra}@teste.com", idade=30, consentimentos=CONSENTIMENTOS_BUSCA))
        resultados = self.buscar("Busca Lote")
        nomes = [r["nome"] for r in resultados]
        self.assertEqual(sorted(nomes), sorted(a["nome"] for a in adultos), nomes)

    def test_mais_de_vinte_perfis_revogados_nao_ocupam_as_vagas_dos_publicos(self):
        for indice in range(22):
            usuario = self.cadastrar(
                f"Busca Lote 0 Revogada {indice:02d}", email=f"revogada.busca.{indice}@teste.com", idade=30,
                consentimentos=CONSENTIMENTOS_BUSCA,
            )
            resposta = self.cli.put(
                f"/api/usuarios/{usuario['id']}/consentimentos/busca_perfil",
                json={"aceito": False},
                headers=self.auth(self.token_de(usuario)),
            )
            self.assertEqual(resposta.status_code, 200, resposta.get_data(as_text=True))
        publicos = [
            self.cadastrar(f"Busca Lote Z Publica {letra}", email=f"publica.busca.{letra}@teste.com", idade=30, consentimentos=CONSENTIMENTOS_BUSCA)
            for letra in ("A", "B")
        ]
        resultados = self.buscar("Busca Lote")
        nomes = [r["nome"] for r in resultados]
        self.assertEqual(sorted(nomes), sorted(p["nome"] for p in publicos), nomes)

    def token_de(self, usuario):
        return self.entrar(usuario["email"])


if __name__ == "__main__":
    unittest.main()
