from datetime import datetime

from models.model import Grupo, GrupoMembro, Usuario
from repositories.repository import GrupoRepository
from tests.test_seguranca import BaseTeste


def criar_usuario(nome, email):
    return Usuario(nome=nome, email=email, senha="hash", idade=30, perfil_publico=True).salvar()


def criar_grupo(dono, nome, codigo):
    grupo = Grupo(nome=nome, id_criador=dono.id_usuario, codigo_convite=codigo).salvar()
    GrupoMembro(id_grupo=grupo.id_grupo, id_usuario=dono.id_usuario, papel="admin").salvar()
    return grupo


class TestGrupoRepository(BaseTeste):

    def test_buscar_por_codigo_devolve_dict_ou_none(self):
        with self.app.app_context():
            dono = criar_usuario("Dono Codigo", "grupo.codigo@repo.teste")
            grupo = criar_grupo(dono, "Grupo Codigo", "CODREPO001")
            id_grupo = grupo.id_grupo
            achado = GrupoRepository.buscar_por_codigo("CODREPO001")
            ausente = GrupoRepository.buscar_por_codigo("NAOEXISTE00")
        self.assertEqual(achado["id_grupo"], id_grupo)
        self.assertIsNone(ausente)

    def test_listar_do_usuario_traz_o_papel_e_ordena_por_nome(self):
        with self.app.app_context():
            ana = criar_usuario("Ana Grupos", "grupo.lista.ana@repo.teste")
            bia = criar_usuario("Bia Grupos", "grupo.lista.bia@repo.teste")
            criar_grupo(ana, "Zeta Grupo", "LISTAZETA01")
            outro = criar_grupo(bia, "Alfa Grupo", "LISTAALFA01")
            GrupoMembro(id_grupo=outro.id_grupo, id_usuario=ana.id_usuario, papel="membro").salvar()
            linhas = GrupoRepository.listar_do_usuario(ana.id_usuario)
        self.assertEqual([l["nome"] for l in linhas], ["Alfa Grupo", "Zeta Grupo"])
        self.assertEqual([l["papel"] for l in linhas], ["membro", "admin"])
        self.assertIsInstance(linhas[0]["data_criacao"], datetime)

    def test_contar_membros_devolve_total(self):
        with self.app.app_context():
            dono = criar_usuario("Dono Contagem", "grupo.conta@repo.teste")
            grupo = criar_grupo(dono, "Grupo Contagem", "CONTREPO001")
            outra = criar_usuario("Outra Contagem", "grupo.conta.outra@repo.teste")
            GrupoMembro(id_grupo=grupo.id_grupo, id_usuario=outra.id_usuario, papel="membro").salvar()
            total = GrupoRepository.contar_membros(grupo.id_grupo)["total"]
        self.assertEqual(total, 2)

    def test_papel_do_membro_devolve_o_papel_ou_none(self):
        with self.app.app_context():
            dono = criar_usuario("Dono Papel", "grupo.papel@repo.teste")
            estranho = criar_usuario("Estranho Papel", "grupo.papel.est@repo.teste")
            grupo = criar_grupo(dono, "Grupo Papel", "PAPELREPO01")
            admin = GrupoRepository.papel_do_membro(grupo.id_grupo, dono.id_usuario)
            nao_membro = GrupoRepository.papel_do_membro(grupo.id_grupo, estranho.id_usuario)
        self.assertEqual(admin["papel"], "admin")
        self.assertIsNone(nao_membro)

    def test_listar_membros_ordena_por_papel_e_depois_nome(self):
        with self.app.app_context():
            dono = criar_usuario("Dono Lista", "grupo.membros.dono@repo.teste")
            zoe = criar_usuario("Zoe Membro", "grupo.membros.zoe@repo.teste")
            abel = criar_usuario("Abel Membro", "grupo.membros.abel@repo.teste")
            grupo = criar_grupo(dono, "Grupo Membros", "MEMBREPO001")
            GrupoMembro(id_grupo=grupo.id_grupo, id_usuario=zoe.id_usuario, papel="membro").salvar()
            GrupoMembro(id_grupo=grupo.id_grupo, id_usuario=abel.id_usuario, papel="membro").salvar()
            linhas = GrupoRepository.listar_membros(grupo.id_grupo)
        self.assertEqual([l["nome"] for l in linhas], ["Dono Lista", "Abel Membro", "Zoe Membro"])
        self.assertEqual(linhas[0]["papel"], "admin")

    def test_ids_membros_traz_um_registro_por_membro(self):
        with self.app.app_context():
            dono = criar_usuario("Dono Ids", "grupo.ids@repo.teste")
            outro = criar_usuario("Outro Ids", "grupo.ids.outro@repo.teste")
            grupo = criar_grupo(dono, "Grupo Ids", "IDSREPO0001")
            GrupoMembro(id_grupo=grupo.id_grupo, id_usuario=outro.id_usuario, papel="membro").salvar()
            ids = sorted(l["id_usuario"] for l in GrupoRepository.ids_membros(grupo.id_grupo))
            esperados = sorted([dono.id_usuario, outro.id_usuario])
        self.assertEqual(ids, esperados)
