from datetime import date, datetime, timedelta

from models.model import Postagem, Usuario
from repositories.repository import PostagemRepository
from tests.test_seguranca import BaseTeste

HOJE = datetime(2026, 1, 20, 12, 0)


def criar_usuario(email, perfil_publico=True, data_nascimento=None, idade=30):
    return Usuario(
        nome=email.split("@")[0], email=email, senha="hash", idade=idade,
        data_nascimento=data_nascimento, perfil_publico=perfil_publico,
    ).salvar()


def publicar(id_usuario, texto, quando=HOJE, foto=None):
    return Postagem(id_usuario=id_usuario, texto=texto, foto=foto, data_registro=quando).salvar()


class TestPostagemRepository(BaseTeste):

    def test_listar_publicas_so_de_perfis_publicos_e_adultos(self):
        with self.app.app_context():
            publico = criar_usuario("post.publica@repo.teste")
            privado = criar_usuario("post.privada@repo.teste", perfil_publico=False)
            menor = criar_usuario(
                "post.menor@repo.teste",
                data_nascimento=date.today().replace(year=date.today().year - 15),
            )
            publicar(publico.id_usuario, "Texto publico")
            publicar(privado.id_usuario, "Texto privado")
            publicar(menor.id_usuario, "Texto menor")
            textos = {p["texto"] for p in PostagemRepository.listar_publicas(50)}
        self.assertIn("Texto publico", textos)
        self.assertNotIn("Texto privado", textos)
        self.assertNotIn("Texto menor", textos)

    def test_listar_publicas_mostra_a_propria_postagem_de_menor_para_o_dono(self):
        with self.app.app_context():
            menor = criar_usuario(
                "post.menor.dono@repo.teste",
                data_nascimento=date.today().replace(year=date.today().year - 15),
            )
            publicar(menor.id_usuario, "Minha postagem menor")
            textos = {p["texto"] for p in PostagemRepository.listar_publicas(50, menor.id_usuario)}
        self.assertIn("Minha postagem menor", textos)

    def test_listar_publicas_ordena_do_mais_novo_e_respeita_o_limite(self):
        with self.app.app_context():
            dono = criar_usuario("post.ordem@repo.teste")
            publicar(dono.id_usuario, "Antiga", quando=HOJE - timedelta(days=3))
            publicar(dono.id_usuario, "Nova", quando=HOJE)
            publicar(dono.id_usuario, "Media", quando=HOJE - timedelta(days=1))
            textos = [p["texto"] for p in PostagemRepository.listar_publicas(2, dono.id_usuario)]
        self.assertEqual(textos, ["Nova", "Media"])

    def test_listar_do_usuario_devolve_so_as_postagens_dele_como_dict(self):
        with self.app.app_context():
            dono = criar_usuario("post.dono@repo.teste")
            outro = criar_usuario("post.outro@repo.teste")
            publicar(dono.id_usuario, "Do dono", foto="uploads/foto.png")
            publicar(outro.id_usuario, "De outro")
            linhas = PostagemRepository.listar_do_usuario(dono.id_usuario)
        self.assertEqual([p["texto"] for p in linhas], ["Do dono"])
        self.assertIsInstance(linhas[0], dict)
        self.assertEqual(linhas[0]["foto"], "uploads/foto.png")
        self.assertIsInstance(linhas[0]["data_registro"], datetime)
