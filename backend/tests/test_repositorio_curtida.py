from models.model import Curtida, Usuario
from repositories.repository import CurtidaRepository
from tests.test_seguranca import BaseTeste


def criar_usuario(email):
    return Usuario(nome=email.split("@")[0], email=email, senha="hash", idade=30).salvar()


def curtir(id_usuario, tipo_alvo, id_alvo):
    return Curtida(id_usuario=id_usuario, tipo_alvo=tipo_alvo, id_alvo=id_alvo).salvar()


class TestCurtidaRepository(BaseTeste):

    def test_buscar_devolve_dict_da_curtida_ou_none(self):
        with self.app.app_context():
            ana = criar_usuario("curt.buscar@repo.teste")
            curtir(ana.id_usuario, "atividade", 900)
            encontrada = CurtidaRepository.buscar(ana.id_usuario, "atividade", 900)
            ausente = CurtidaRepository.buscar(ana.id_usuario, "atividade", 901)
        self.assertEqual(encontrada["id_alvo"], 900)
        self.assertEqual(encontrada["tipo_alvo"], "atividade")
        self.assertIsNone(ausente)

    def test_contar_conta_so_o_alvo_informado(self):
        with self.app.app_context():
            ana = criar_usuario("curt.contar.a@repo.teste")
            bia = criar_usuario("curt.contar.b@repo.teste")
            curtir(ana.id_usuario, "postagem", 910)
            curtir(bia.id_usuario, "postagem", 910)
            curtir(bia.id_usuario, "postagem", 911)
            total = CurtidaRepository.contar("postagem", 910)["total"]
        self.assertEqual(total, 2)

    def test_contar_em_lote_agrupa_por_alvo_e_ignora_outros_tipos(self):
        with self.app.app_context():
            ana = criar_usuario("curt.lote.a@repo.teste")
            bia = criar_usuario("curt.lote.b@repo.teste")
            curtir(ana.id_usuario, "atividade", 920)
            curtir(bia.id_usuario, "atividade", 920)
            curtir(ana.id_usuario, "atividade", 921)
            curtir(ana.id_usuario, "postagem", 920)
            lote = CurtidaRepository.contar_em_lote("atividade", [920, 921, 922])
        self.assertEqual(lote, {920: 2, 921: 1})
        self.assertIsInstance(lote[920], int)

    def test_contar_em_lote_sem_ids_nao_consulta(self):
        with self.app.app_context():
            self.assertEqual(CurtidaRepository.contar_em_lote("atividade", []), {})

    def test_curtidos_pelo_usuario_traz_so_os_alvos_que_ele_curtiu(self):
        with self.app.app_context():
            ana = criar_usuario("curt.quem.a@repo.teste")
            bia = criar_usuario("curt.quem.b@repo.teste")
            curtir(ana.id_usuario, "atividade", 930)
            curtir(ana.id_usuario, "atividade", 931)
            curtir(bia.id_usuario, "atividade", 932)
            linhas = CurtidaRepository.curtidos_pelo_usuario(ana.id_usuario, "atividade", [930, 932])
        self.assertEqual([linha["id_alvo"] for linha in linhas], [930])

    def test_curtidos_pelo_usuario_sem_ids_devolve_lista_vazia(self):
        with self.app.app_context():
            self.assertEqual(CurtidaRepository.curtidos_pelo_usuario(1, "atividade", []), [])

    def test_excluir_do_alvo_remove_so_as_curtidas_daquele_alvo(self):
        with self.app.app_context():
            ana = criar_usuario("curt.excl.alvo@repo.teste")
            curtir(ana.id_usuario, "postagem", 940)
            curtir(ana.id_usuario, "postagem", 941)
            CurtidaRepository.excluir_do_alvo("postagem", 940)
            self.assertIsNone(CurtidaRepository.buscar(ana.id_usuario, "postagem", 940))
            self.assertIsNotNone(CurtidaRepository.buscar(ana.id_usuario, "postagem", 941))

    def test_excluir_do_usuario_remove_todas_as_curtidas_dele(self):
        with self.app.app_context():
            ana = criar_usuario("curt.excl.user.a@repo.teste")
            bia = criar_usuario("curt.excl.user.b@repo.teste")
            curtir(ana.id_usuario, "atividade", 950)
            curtir(ana.id_usuario, "postagem", 951)
            curtir(bia.id_usuario, "atividade", 950)
            CurtidaRepository.excluir_do_usuario(ana.id_usuario)
            self.assertIsNone(CurtidaRepository.buscar(ana.id_usuario, "atividade", 950))
            self.assertIsNone(CurtidaRepository.buscar(ana.id_usuario, "postagem", 951))
            self.assertIsNotNone(CurtidaRepository.buscar(bia.id_usuario, "atividade", 950))
