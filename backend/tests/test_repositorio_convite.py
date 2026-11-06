from datetime import datetime

from models.model import Convite, Grupo, GrupoMembro, Usuario
from repositories.repository import ConviteRepository
from tests.test_seguranca import BaseTeste

HOJE = datetime(2026, 1, 20, 12, 0)
ONTEM = datetime(2026, 1, 19, 12, 0)


def criar_usuario(nome, email):
    return Usuario(nome=nome, email=email, senha="hash", idade=30, perfil_publico=True).salvar()


def criar_grupo(dono, nome, codigo):
    grupo = Grupo(nome=nome, descricao=f"Descricao {nome}", id_criador=dono.id_usuario,
                  codigo_convite=codigo).salvar()
    GrupoMembro(id_grupo=grupo.id_grupo, id_usuario=dono.id_usuario, papel="admin").salvar()
    return grupo


class TestConviteRepository(BaseTeste):

    def test_buscar_pendente_so_acha_convite_em_aberto(self):
        with self.app.app_context():
            dono = criar_usuario("Dono Convite", "convite.dono@repo.teste")
            alvo = criar_usuario("Alvo Convite", "convite.alvo@repo.teste")
            grupo = criar_grupo(dono, "Grupo Convite", "CONVREPO001")
            convite = Convite(id_grupo=grupo.id_grupo, id_remetente=dono.id_usuario,
                              id_destinatario=alvo.id_usuario).salvar()
            id_convite = convite.id_convite
            pendente = ConviteRepository.buscar_pendente(grupo.id_grupo, alvo.id_usuario)
            convite.status = "recusado"
            convite.salvar()
            depois = ConviteRepository.buscar_pendente(grupo.id_grupo, alvo.id_usuario)
        self.assertEqual(pendente["id_convite"], id_convite)
        self.assertIsNone(depois)

    def test_listar_pendentes_recebidos_traz_grupo_e_remetente_em_dict(self):
        with self.app.app_context():
            dono = criar_usuario("Remetente Lista", "convite.lista.rem@repo.teste")
            alvo = criar_usuario("Destino Lista", "convite.lista.dest@repo.teste")
            grupo_novo = criar_grupo(dono, "Grupo Novo", "CONVREPO002")
            grupo_antigo = criar_grupo(dono, "Grupo Antigo", "CONVREPO003")
            Convite(id_grupo=grupo_antigo.id_grupo, id_remetente=dono.id_usuario,
                    id_destinatario=alvo.id_usuario, data_envio=ONTEM).salvar()
            Convite(id_grupo=grupo_novo.id_grupo, id_remetente=dono.id_usuario,
                    id_destinatario=alvo.id_usuario, data_envio=HOJE).salvar()
            linhas = ConviteRepository.listar_pendentes_recebidos(alvo.id_usuario)
        self.assertEqual([l["grupo_nome"] for l in linhas], ["Grupo Novo", "Grupo Antigo"])
        self.assertEqual(linhas[0]["remetente_nome"], "Remetente Lista")
        self.assertEqual(linhas[0]["grupo_descricao"], "Descricao Grupo Novo")
        self.assertEqual(linhas[0]["data_envio"], HOJE)

    def test_contar_enviados_pendentes_conta_so_convites_em_aberto_do_remetente(self):
        with self.app.app_context():
            dono = criar_usuario("Remetente Conta", "convite.conta.rem@repo.teste")
            alvo = criar_usuario("Destino Conta", "convite.conta.dest@repo.teste")
            grupo = criar_grupo(dono, "Grupo Conta", "CONVREPO004")
            Convite(id_grupo=grupo.id_grupo, id_remetente=dono.id_usuario,
                    id_destinatario=alvo.id_usuario).salvar()
            total = ConviteRepository.contar_enviados_pendentes(dono.id_usuario)["total"]
        self.assertEqual(total, 1)
