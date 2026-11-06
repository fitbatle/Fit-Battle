from datetime import datetime

from models.model import Atividade, Grupo, GrupoMembro, Usuario
from repositories.repository import RankingRepository
from tests.test_seguranca import BaseTeste

HOJE = datetime(2026, 1, 20, 12, 0)


def criar_usuario(email, xp, cidade="Belo Horizonte", estado="MG"):
    return Usuario(
        nome=email.split("@")[0], email=email, senha="hash", idade=30, xp=xp,
        cidade=cidade, estado=estado, perfil_publico=True,
    ).salvar()


class TestRankingRepository(BaseTeste):

    def test_global_traz_ordem_de_posicao_e_respeita_o_limite(self):
        with self.app.app_context():
            criar_usuario("rank.global.a@repo.teste", xp=500)
            criar_usuario("rank.global.b@repo.teste", xp=900)
            criar_usuario("rank.global.c@repo.teste", xp=100)
            linhas = RankingRepository.global_(2)
        self.assertEqual(len(linhas), 2)
        self.assertEqual([l["posicao"] for l in linhas], [1, 2])
        self.assertGreaterEqual(linhas[0]["pontuacao_total"], linhas[1]["pontuacao_total"])
        self.assertIsInstance(linhas[0]["pontuacao_total"], int)

    def test_regional_todos_traz_todos_os_perfis_publicos(self):
        with self.app.app_context():
            criar_usuario("rank.reg.a@repo.teste", xp=10, cidade="Ouro Preto", estado="MG")
            linhas = RankingRepository.regional_todos()
        self.assertTrue(any(l["cidade"] == "Ouro Preto" for l in linhas))

    def test_por_exercicio_filtra_pelo_titulo_e_pela_cidade(self):
        with self.app.app_context():
            forte = criar_usuario("rank.ex.forte@repo.teste", xp=10, cidade="Itabira")
            fraco = criar_usuario("rank.ex.fraco@repo.teste", xp=10, cidade="Itabira")
            outra = criar_usuario("rank.ex.outra@repo.teste", xp=10, cidade="Sete Lagoas")
            Atividade(id_usuario=forte.id_usuario, tipo="musculacao", titulo="Rosca Exemplo",
                      carga_kg=40, pontuacao=10, data_registro=HOJE).salvar()
            Atividade(id_usuario=fraco.id_usuario, tipo="musculacao", titulo="Rosca Exemplo",
                      carga_kg=20, pontuacao=10, data_registro=HOJE).salvar()
            Atividade(id_usuario=outra.id_usuario, tipo="musculacao", titulo="Rosca Exemplo",
                      carga_kg=60, pontuacao=10, data_registro=HOJE).salvar()
            todos = RankingRepository.por_exercicio("  rosca exemplo ", None, 10)
            so_itabira = RankingRepository.por_exercicio("rosca exemplo", "Itabira", 10)
        nomes_todos = [l["nome"] for l in todos]
        self.assertIn("rank.ex.forte", nomes_todos)
        self.assertEqual([l["nome"] for l in so_itabira], ["rank.ex.forte", "rank.ex.fraco"])
        self.assertEqual(so_itabira[0]["carga_maxima"], 40.0)

    def test_minha_posicao_global_e_regional_devolvem_dict_ou_none(self):
        with self.app.app_context():
            ana = criar_usuario("rank.pos.a@repo.teste", xp=300, cidade="Caeté")
            posicao = RankingRepository.minha_posicao_global(ana.id_usuario)
            regional = RankingRepository.minha_posicao_regional(ana.id_usuario)
            ausente = RankingRepository.minha_posicao_global(999999)
        self.assertIsInstance(posicao["posicao"], int)
        self.assertEqual(regional["cidade"], "Caeté")
        self.assertIsNone(ausente)

    def test_grupo_ranking_so_com_os_membros_do_grupo(self):
        with self.app.app_context():
            dono = criar_usuario("rank.grupo.dono@repo.teste", xp=50)
            membro = criar_usuario("rank.grupo.membro@repo.teste", xp=70)
            fora = criar_usuario("rank.grupo.fora@repo.teste", xp=999)
            grupo = Grupo(nome="Grupo Ranking Repo", id_criador=dono.id_usuario,
                          codigo_convite="REPOGRP01").salvar()
            GrupoMembro(id_grupo=grupo.id_grupo, id_usuario=dono.id_usuario, papel="admin").salvar()
            GrupoMembro(id_grupo=grupo.id_grupo, id_usuario=membro.id_usuario, papel="membro").salvar()
            ids = [l["id_usuario"] for l in RankingRepository.grupo(grupo.id_grupo, 10)]
            esperados = sorted([dono.id_usuario, membro.id_usuario])
            id_fora = fora.id_usuario
        self.assertEqual(sorted(ids), esperados)
        self.assertNotIn(id_fora, ids)
