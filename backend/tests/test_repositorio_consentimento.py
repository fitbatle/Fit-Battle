from models.model import Consentimento, Usuario
from repositories.repository import ConsentimentoRepository
from tests.test_seguranca import BaseTeste


def criar_usuario(email):
    return Usuario(nome=email.split("@")[0], email=email, senha="hash", idade=30).salvar()


def registrar(id_usuario, chave, aceito=True, obrigatorio=False):
    return Consentimento(
        id_usuario=id_usuario, chave=chave, descricao=chave, obrigatorio=obrigatorio, aceito=aceito,
    ).salvar()


class TestConsentimentoRepository(BaseTeste):

    def test_listar_traz_os_obrigatorios_primeiro(self):
        with self.app.app_context():
            ana = criar_usuario("cons.listar@repo.teste")
            registrar(ana.id_usuario, "ranking_publico", obrigatorio=False)
            registrar(ana.id_usuario, "conta_autenticacao", obrigatorio=True)
            chaves = [c["chave"] for c in ConsentimentoRepository.listar_do_usuario(ana.id_usuario)]
        self.assertEqual(chaves, ["conta_autenticacao", "ranking_publico"])

    def test_listar_devolve_dict_com_booleanos_normalizados(self):
        with self.app.app_context():
            ana = criar_usuario("cons.tipos@repo.teste")
            registrar(ana.id_usuario, "notificacoes", aceito=False)
            linha = ConsentimentoRepository.listar_do_usuario(ana.id_usuario)[0]
        self.assertIsInstance(linha, dict)
        self.assertIs(linha["aceito"], False)
        self.assertIs(linha["obrigatorio"], False)

    def test_listar_nao_traz_consentimentos_de_outro_usuario(self):
        with self.app.app_context():
            ana = criar_usuario("cons.dono@repo.teste")
            bia = criar_usuario("cons.outra@repo.teste")
            registrar(ana.id_usuario, "chat_publico")
            registrar(bia.id_usuario, "chat_publico")
            chaves = [c["chave"] for c in ConsentimentoRepository.listar_do_usuario(ana.id_usuario)]
        self.assertEqual(chaves, ["chat_publico"])

    def test_buscar_devolve_dict_pela_chave(self):
        with self.app.app_context():
            ana = criar_usuario("cons.buscar@repo.teste")
            criado = registrar(ana.id_usuario, "busca_perfil", aceito=True)
            id_criado = criado.id_consentimento
            achado = ConsentimentoRepository.buscar(ana.id_usuario, "busca_perfil")
            outra_chave = ConsentimentoRepository.buscar(ana.id_usuario, "localizacao")
        self.assertEqual(achado["id_consentimento"], id_criado)
        self.assertIs(achado["aceito"], True)
        self.assertIsNone(outra_chave)
