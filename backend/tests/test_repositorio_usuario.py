from models.model import Consentimento, Usuario
from repositories.repository import UsuarioRepository
from tests.test_seguranca import BaseTeste


def criar_usuario(nome, email, cidade="Belo Horizonte", perfil_publico=True, idade=30):
    return Usuario(
        nome=nome, email=email, senha="hash", idade=idade, cidade=cidade,
        perfil_publico=perfil_publico,
    ).salvar()


def permitir_busca(id_usuario):
    Consentimento(
        id_usuario=id_usuario, chave="busca_perfil", descricao="Busca", obrigatorio=False, aceito=True,
    ).salvar()


class TestUsuarioRepositoryListar(BaseTeste):

    def test_sem_filtro_traz_todos_em_ordem_de_nome(self):
        with self.app.app_context():
            criar_usuario("Carla", "carla@repo.teste")
            criar_usuario("Ana", "ana@repo.teste")
            nomes = [u["nome"] for u in UsuarioRepository.listar()]
        self.assertEqual(nomes, sorted(nomes))
        self.assertIn("Ana", nomes)
        self.assertIn("Carla", nomes)

    def test_com_filtro_traz_so_quem_contem_o_trecho(self):
        with self.app.app_context():
            criar_usuario("Marina Zeta", "marina.zeta@repo.teste")
            criar_usuario("Bruno Teste", "bruno.teste@repo.teste")
            nomes = [u["nome"] for u in UsuarioRepository.listar("Zeta")]
        self.assertEqual(nomes, ["Marina Zeta"])

    def test_linhas_chegam_como_dict_com_tipos_normalizados(self):
        with self.app.app_context():
            criar_usuario("Tipos Repo", "tipos.repo@repo.teste")
            usuario = UsuarioRepository.listar("Tipos Repo")[0]
        self.assertIsInstance(usuario, dict)
        self.assertIs(usuario["perfil_publico"], True)
        self.assertIsNotNone(usuario["criado_em"])
        self.assertIsNone(usuario["criado_em"].tzinfo)


class TestUsuarioRepositoryBuscaPublica(BaseTeste):

    def test_so_aparece_quem_tem_perfil_publico_e_consentimento_de_busca(self):
        with self.app.app_context():
            com_consentimento = criar_usuario("Liberado Busca", "liberado.busca@repo.teste")
            permitir_busca(com_consentimento.id_usuario)
            sem_consentimento = criar_usuario("Liberado Oculto", "oculto.busca@repo.teste")
            privado = criar_usuario("Liberado Privado", "privado.busca@repo.teste", perfil_publico=False)
            permitir_busca(privado.id_usuario)

            nomes = [u["nome"] for u in UsuarioRepository.buscar_publicos("Liberado", 0)]

        self.assertIn("Liberado Busca", nomes)
        self.assertNotIn("Liberado Oculto", nomes)
        self.assertNotIn("Liberado Privado", nomes)
        self.assertIsNotNone(sem_consentimento)

    def test_busca_tambem_casa_com_a_cidade(self):
        with self.app.app_context():
            usuario = criar_usuario("Sem Relacao", "cidade.busca@repo.teste", cidade="Ouro Preto")
            permitir_busca(usuario.id_usuario)
            nomes = [u["nome"] for u in UsuarioRepository.buscar_publicos("Ouro", 0)]
        self.assertIn("Sem Relacao", nomes)

    def test_exclui_o_proprio_usuario_pelo_id(self):
        with self.app.app_context():
            usuario = criar_usuario("Excluido Eu", "excluido.eu@repo.teste")
            permitir_busca(usuario.id_usuario)
            nomes = [u["nome"] for u in UsuarioRepository.buscar_publicos("Excluido", usuario.id_usuario)]
        self.assertEqual(nomes, [])

    def test_percentual_e_sublinhado_do_termo_sao_texto_literal(self):
        with self.app.app_context():
            usuario = criar_usuario("Taxa 100% Real", "taxa.repo@repo.teste")
            permitir_busca(usuario.id_usuario)
            outro = criar_usuario("Taxa Sem Sinal", "taxa.sem@repo.teste")
            permitir_busca(outro.id_usuario)
            com_porcentagem = [u["nome"] for u in UsuarioRepository.buscar_publicos("100%", 0)]
            com_sublinhado = [u["nome"] for u in UsuarioRepository.buscar_publicos("Taxa_Sem", 0)]
        self.assertEqual(com_porcentagem, ["Taxa 100% Real"])
        self.assertEqual(com_sublinhado, [])


class TestUsuarioRepositoryBuscarPorEmail(BaseTeste):

    def test_devolve_dict_do_usuario_com_o_email(self):
        with self.app.app_context():
            criado = criar_usuario("Por Email", "por.email@repo.teste")
            id_criado = criado.id_usuario
            achado = UsuarioRepository.buscar_por_email("por.email@repo.teste")
        self.assertEqual(achado["id_usuario"], id_criado)
        self.assertEqual(achado["nome"], "Por Email")

    def test_email_inexistente_devolve_none(self):
        with self.app.app_context():
            self.assertIsNone(UsuarioRepository.buscar_por_email("nao.existe@repo.teste"))
