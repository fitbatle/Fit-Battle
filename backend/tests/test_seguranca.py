import io
import os
import shutil
import sys
import tempfile
import unittest
from datetime import date, timedelta
from unittest import mock

os.environ["DB_URI"] = "sqlite:///:memory:"
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import criar_app
from auth import gerar_token
from database import db
from models.model import Usuario
from services import resetar_limitador_login
from tests.apoio import CONSENTIMENTOS_OPCIONAIS_ACEITOS, criar_views_de_ranking

SENHA = "senhaforte123"
CAMPOS_PRIVADOS = {"email", "idade", "data_nascimento", "peso", "altura", "responsavel"}
CAMPOS_PUBLICOS = {"id", "nome", "cidade", "estado", "foto", "descricao", "nivel", "xp", "criado_em"}


def data_nascimento_para_idade(idade):
    hoje = date.today()
    try:
        nascimento = hoje.replace(year=hoje.year - idade)
    except ValueError:
        nascimento = hoje.replace(year=hoje.year - idade, month=3, day=1)
    return nascimento.isoformat()


class BaseTeste(unittest.TestCase):

    def setUp(self):
        resetar_limitador_login()
        self.app = criar_app()
        with self.app.app_context():
            criar_views_de_ranking(db)
        self.cli = self.app.test_client()

    def cadastrar(self, nome, email=None, idade=25, consentimentos=None, responsavel=None):
        email = email or nome.lower().replace(" ", ".") + "@teste.com"
        corpo = {
            "nome": nome,
            "email": email,
            "data_nascimento": data_nascimento_para_idade(idade),
            "senha": SENHA,
            "aceite_termos": True,
            "consentimentos": consentimentos if consentimentos is not None else CONSENTIMENTOS_OPCIONAIS_ACEITOS,
        }
        if responsavel:
            corpo["responsavel"] = responsavel
            corpo["autorizacao_responsavel"] = True
        resposta = self.cli.post("/api/usuarios", json=corpo)
        self.assertEqual(resposta.status_code, 201, resposta.get_data(as_text=True))
        return resposta.get_json()["usuario"]

    def entrar(self, email):
        resposta = self.cli.post("/api/login", json={"email": email, "senha": SENHA})
        self.assertEqual(resposta.status_code, 200)
        return resposta.get_json()["token"]

    def criar_usuario_logado(self, nome, **kwargs):
        usuario = self.cadastrar(nome, **kwargs)
        return usuario, self.entrar(usuario["email"])

    @staticmethod
    def auth(token):
        return {"Authorization": "Bearer " + token}

    def registrar_treino(self, usuario, token):
        resposta = self.cli.post(
            f"/api/usuarios/{usuario['id']}/atividades",
            json={"tipo": "musculacao", "titulo": "Peito", "tempo_min": 40},
            headers=self.auth(token),
        )
        self.assertEqual(resposta.status_code, 201)
        return resposta.get_json()["atividade"]


class TestAutenticacao(BaseTeste):

    def test_login_devolve_token_e_usuario(self):
        self.cadastrar("Ana Silva", email="ana@teste.com")
        resposta = self.cli.post("/api/login", json={"email": "ana@teste.com", "senha": SENHA})
        corpo = resposta.get_json()
        self.assertEqual(resposta.status_code, 200)
        self.assertTrue(corpo["token"])
        self.assertEqual(corpo["usuario"]["email"], "ana@teste.com")

    def test_login_com_senha_errada_nao_devolve_token(self):
        self.cadastrar("Ana Silva", email="ana@teste.com")
        resposta = self.cli.post("/api/login", json={"email": "ana@teste.com", "senha": "errada123"})
        self.assertEqual(resposta.status_code, 401)
        self.assertNotIn("token", resposta.get_json())

    def test_rotas_protegidas_exigem_token(self):
        alvos = [
            ("get", "/api/eu"),
            ("get", "/api/feed"),
            ("get", "/api/ranking/global"),
            ("get", "/api/ranking/regional?cidade=x"),
            ("get", "/api/ranking/exercicio?titulo=Supino+Reto"),
            ("get", "/api/usuarios/busca?nome=ab"),
            ("get", "/api/usuarios/1"),
            ("put", "/api/usuarios/1"),
            ("delete", "/api/usuarios/1"),
            ("post", "/api/usuarios/1/foto"),
            ("get", "/api/usuarios/1/atividades"),
            ("post", "/api/usuarios/1/atividades"),
            ("get", "/api/atividades/1"),
            ("delete", "/api/atividades/1"),
            ("post", "/api/postagens"),
            ("delete", "/api/postagens/1"),
            ("post", "/api/feed/postagem/1/curtir"),
            ("get", "/api/feed/postagem/1/comentarios"),
            ("post", "/api/feed/postagem/1/comentarios"),
            ("delete", "/api/comentarios/1"),
            ("get", "/api/usuarios/1/ranking"),
            ("get", "/api/usuarios/1/consentimentos"),
            ("put", "/api/usuarios/1/consentimentos/ranking_publico"),
            ("post", "/api/grupos"),
            ("get", "/api/grupos"),
            ("get", "/api/grupos/1"),
            ("get", "/api/grupos/1/membros"),
            ("get", "/api/grupos/1/ranking"),
            ("get", "/api/grupos/1/convite"),
            ("post", "/api/grupos/1/convite/regenerar"),
            ("post", "/api/grupos/entrar"),
            ("get", "/api/grupos/1/busca-convidar?nome=ab"),
            ("post", "/api/grupos/1/convites"),
            ("get", "/api/convites"),
            ("put", "/api/convites/1"),
            ("post", "/api/metas"),
            ("get", "/api/metas"),
            ("get", "/api/metas/1"),
            ("put", "/api/metas/1"),
            ("delete", "/api/metas/1"),
        ]
        for metodo, caminho in alvos:
            with self.subTest(rota=f"{metodo.upper()} {caminho}"):
                resposta = getattr(self.cli, metodo)(caminho)
                self.assertEqual(resposta.status_code, 401)

    def test_rotas_publicas_continuam_abertas(self):
        self.assertEqual(self.cli.get("/api/estatisticas").status_code, 200)
        self.cadastrar("Ana Silva")

    def test_listagem_aberta_de_usuarios_foi_removida(self):
        self.cadastrar("Ana Silva")
        resposta = self.cli.get("/api/usuarios")
        self.assertEqual(resposta.status_code, 405)

    def test_token_adulterado_e_recusado(self):
        _, token = self.criar_usuario_logado("Ana Silva")
        adulterado = token[:-3] + ("aaa" if not token.endswith("aaa") else "bbb")
        resposta = self.cli.get("/api/eu", headers=self.auth(adulterado))
        self.assertEqual(resposta.status_code, 401)

    def test_cabecalhos_invalidos_sao_recusados(self):
        for cabecalho in ("Bearer", "Bearer ", "Basic abc", "abc", "Bearer nao.e.token"):
            with self.subTest(cabecalho=cabecalho):
                resposta = self.cli.get("/api/eu", headers={"Authorization": cabecalho})
                self.assertEqual(resposta.status_code, 401)

    def test_token_assinado_com_outra_chave_e_recusado(self):
        usuario, _ = self.criar_usuario_logado("Ana Silva")
        outro_app = criar_app()
        outro_app.config["SECRET_KEY"] = "outra-chave-qualquer"
        with outro_app.app_context():
            falso = gerar_token(usuario["id"])
        resposta = self.cli.get("/api/eu", headers=self.auth(falso))
        self.assertEqual(resposta.status_code, 401)

    def test_token_expirado_e_recusado(self):
        _, token = self.criar_usuario_logado("Ana Silva")
        with mock.patch("auth.VALIDADE_TOKEN_SEGUNDOS", -1):
            resposta = self.cli.get("/api/eu", headers=self.auth(token))
        self.assertEqual(resposta.status_code, 401)

    def test_token_de_usuario_excluido_e_recusado(self):
        usuario, token = self.criar_usuario_logado("Ana Silva")
        exclusao = self.cli.delete(f"/api/usuarios/{usuario['id']}", headers=self.auth(token))
        self.assertEqual(exclusao.status_code, 200)
        resposta = self.cli.get("/api/eu", headers=self.auth(token))
        self.assertEqual(resposta.status_code, 401)

    def test_eu_devolve_dados_atualizados_do_proprio_usuario(self):
        usuario, token = self.criar_usuario_logado("Ana Silva")
        self.registrar_treino(usuario, token)
        resposta = self.cli.get("/api/eu", headers=self.auth(token))
        corpo = resposta.get_json()["usuario"]
        self.assertEqual(corpo["id"], usuario["id"])
        self.assertGreater(corpo["xp"], 0)


class TestDonoDoRecurso(BaseTeste):

    def setUp(self):
        super().setUp()
        self.ana, self.token_ana = self.criar_usuario_logado("Ana Silva")
        self.bia, self.token_bia = self.criar_usuario_logado("Bia Costa")

    def test_outro_usuario_nao_edita_nem_exclui_conta(self):
        alvo = f"/api/usuarios/{self.ana['id']}"
        editar = self.cli.put(alvo, json={"nome": "Invasor"}, headers=self.auth(self.token_bia))
        excluir = self.cli.delete(alvo, headers=self.auth(self.token_bia))
        self.assertEqual(editar.status_code, 403)
        self.assertEqual(excluir.status_code, 403)
        atual = self.cli.get("/api/eu", headers=self.auth(self.token_ana)).get_json()["usuario"]
        self.assertEqual(atual["nome"], "Ana Silva")

    def test_outro_usuario_nao_troca_foto(self):
        resposta = self.cli.post(
            f"/api/usuarios/{self.ana['id']}/foto", headers=self.auth(self.token_bia)
        )
        self.assertEqual(resposta.status_code, 403)

    def test_outro_usuario_nao_registra_nem_le_treinos_alheios(self):
        base = f"/api/usuarios/{self.ana['id']}/atividades"
        registrar = self.cli.post(
            base, json={"tipo": "cardio", "tempo_min": 30}, headers=self.auth(self.token_bia)
        )
        historico = self.cli.get(base, headers=self.auth(self.token_bia))
        self.assertEqual(registrar.status_code, 403)
        self.assertEqual(historico.status_code, 403)

    def test_outro_usuario_nao_mexe_em_consentimentos(self):
        base = f"/api/usuarios/{self.ana['id']}/consentimentos"
        ler = self.cli.get(base, headers=self.auth(self.token_bia))
        alterar = self.cli.put(
            base + "/ranking_publico", json={"aceito": False}, headers=self.auth(self.token_bia)
        )
        self.assertEqual(ler.status_code, 403)
        self.assertEqual(alterar.status_code, 403)

    def test_outro_usuario_ve_ranking_de_perfil_publico(self):
        resposta = self.cli.get(
            f"/api/usuarios/{self.ana['id']}/ranking", headers=self.auth(self.token_bia)
        )
        self.assertEqual(resposta.status_code, 200)
        self.assertIn("global", resposta.get_json())

    def test_outro_usuario_nao_ve_ranking_de_perfil_privado(self):
        self.cli.put(
            f"/api/usuarios/{self.ana['id']}/consentimentos/ranking_publico",
            json={"aceito": False},
            headers=self.auth(self.token_ana),
        )
        resposta = self.cli.get(
            f"/api/usuarios/{self.ana['id']}/ranking", headers=self.auth(self.token_bia)
        )
        self.assertEqual(resposta.status_code, 404)

    def test_dono_ve_o_proprio_ranking_mesmo_com_perfil_privado(self):
        self.cli.put(
            f"/api/usuarios/{self.ana['id']}/consentimentos/ranking_publico",
            json={"aceito": False},
            headers=self.auth(self.token_ana),
        )
        resposta = self.cli.get(
            f"/api/usuarios/{self.ana['id']}/ranking", headers=self.auth(self.token_ana)
        )
        self.assertEqual(resposta.status_code, 200)

    def test_dono_edita_e_exclui_o_proprio_recurso(self):
        alvo = f"/api/usuarios/{self.ana['id']}"
        editar = self.cli.put(alvo, json={"nome": "Ana Souza"}, headers=self.auth(self.token_ana))
        self.assertEqual(editar.status_code, 200)
        self.assertEqual(editar.get_json()["usuario"]["nome"], "Ana Souza")
        treino = self.registrar_treino(self.ana, self.token_ana)
        excluir = self.cli.delete(f"/api/atividades/{treino['id']}", headers=self.auth(self.token_ana))
        self.assertEqual(excluir.status_code, 200)

    def test_exclusao_anonima_de_treino_e_recusada(self):
        treino = self.registrar_treino(self.ana, self.token_ana)
        resposta = self.cli.delete(f"/api/atividades/{treino['id']}")
        self.assertEqual(resposta.status_code, 401)
        existe = self.cli.get(f"/api/atividades/{treino['id']}", headers=self.auth(self.token_ana))
        self.assertEqual(existe.status_code, 200)

    def test_outro_usuario_nao_exclui_treino_alheio_mesmo_forjando_o_id(self):
        treino = self.registrar_treino(self.ana, self.token_ana)
        resposta = self.cli.delete(
            f"/api/atividades/{treino['id']}",
            json={"id_usuario": self.ana["id"]},
            headers=self.auth(self.token_bia),
        )
        self.assertEqual(resposta.status_code, 403)
        existe = self.cli.get(f"/api/atividades/{treino['id']}", headers=self.auth(self.token_ana))
        self.assertEqual(existe.status_code, 200)

    def test_outro_usuario_nao_exclui_postagem_nem_comentario_alheios(self):
        postagem = self.cli.post(
            "/api/postagens", data={"texto": "Treino de hoje"}, headers=self.auth(self.token_ana)
        )
        self.assertEqual(postagem.status_code, 201)
        id_postagem = postagem.get_json()["postagem"]["id"]

        comentario = self.cli.post(
            f"/api/feed/postagem/{id_postagem}/comentarios",
            json={"texto": "Boa!"},
            headers=self.auth(self.token_ana),
        )
        id_comentario = comentario.get_json()["comentario"]["id"]

        apagar_postagem = self.cli.delete(
            f"/api/postagens/{id_postagem}", headers=self.auth(self.token_bia)
        )
        apagar_comentario = self.cli.delete(
            f"/api/comentarios/{id_comentario}", headers=self.auth(self.token_bia)
        )
        self.assertEqual(apagar_postagem.status_code, 403)
        self.assertEqual(apagar_comentario.status_code, 403)

    def test_id_enviado_no_corpo_e_ignorado(self):
        postagem = self.cli.post(
            "/api/postagens",
            data={"texto": "Postagem da Ana", "id_usuario": str(self.bia["id"])},
            headers=self.auth(self.token_ana),
        )
        self.assertEqual(postagem.get_json()["postagem"]["id_usuario"], self.ana["id"])

        id_postagem = postagem.get_json()["postagem"]["id"]
        comentario = self.cli.post(
            f"/api/feed/postagem/{id_postagem}/comentarios",
            json={"texto": "Comentario da Bia", "id_usuario": self.ana["id"]},
            headers=self.auth(self.token_bia),
        )
        self.assertEqual(comentario.get_json()["comentario"]["id_usuario"], self.bia["id"])

        curtida = self.cli.post(
            f"/api/feed/postagem/{id_postagem}/curtir",
            json={"id_usuario": self.ana["id"]},
            headers=self.auth(self.token_bia),
        )
        self.assertTrue(curtida.get_json()["curti"])

        feed_da_bia = self.cli.get("/api/feed", headers=self.auth(self.token_bia)).get_json()
        self.assertTrue(next(i for i in feed_da_bia if i["tipo_conteudo"] == "postagem")["curti"])
        feed_da_ana = self.cli.get("/api/feed", headers=self.auth(self.token_ana)).get_json()
        self.assertFalse(next(i for i in feed_da_ana if i["tipo_conteudo"] == "postagem")["curti"])


class TestExposicaoDeDados(BaseTeste):

    def setUp(self):
        super().setUp()
        self.responsavel = {"nome": "Carlos Responsavel", "email": "carlos.resp@teste.com"}
        self.jovem, self.token_jovem = self.criar_usuario_logado(
            "Davi Menor", idade=15, responsavel=self.responsavel
        )
        self.ana, self.token_ana = self.criar_usuario_logado("Ana Silva")

    def assertSemDadosDoResponsavel(self, texto):
        self.assertNotIn("carlos.resp@teste.com", texto)
        self.assertNotIn("Carlos Responsavel", texto)
        self.assertNotIn("responsavel", texto)

    def test_dados_do_responsavel_nao_saem_em_nenhuma_resposta_do_proprio_menor(self):
        self.assertSemDadosDoResponsavel(str(self.jovem))
        respostas = [
            self.cli.post("/api/login", json={"email": self.jovem["email"], "senha": SENHA}),
            self.cli.get("/api/eu", headers=self.auth(self.token_jovem)),
            self.cli.get(f"/api/usuarios/{self.jovem['id']}", headers=self.auth(self.token_jovem)),
            self.cli.put(
                f"/api/usuarios/{self.jovem['id']}",
                json={"descricao": "oi"},
                headers=self.auth(self.token_jovem),
            ),
        ]
        for resposta in respostas:
            self.assertEqual(resposta.status_code, 200)
            self.assertSemDadosDoResponsavel(resposta.get_data(as_text=True))

    def test_perfil_alheio_devolve_so_campos_publicos(self):
        resposta = self.cli.get(f"/api/usuarios/{self.ana['id']}", headers=self.auth(self.token_jovem))
        corpo = resposta.get_json()
        self.assertEqual(resposta.status_code, 200)
        self.assertEqual(set(corpo), CAMPOS_PUBLICOS)
        self.assertEqual(corpo["nome"], "Ana Silva")

    def test_menor_de_idade_nao_aparece_no_perfil_publico_para_outro_usuario(self):
        resposta = self.cli.get(f"/api/usuarios/{self.jovem['id']}", headers=self.auth(self.token_ana))
        self.assertEqual(resposta.status_code, 404)

    def test_menor_de_idade_ve_o_proprio_perfil_normalmente(self):
        resposta = self.cli.get(f"/api/usuarios/{self.jovem['id']}", headers=self.auth(self.token_jovem))
        self.assertEqual(resposta.status_code, 200)
        self.assertEqual(resposta.get_json()["nome"], "Davi Menor")

    def test_perfil_proprio_devolve_campos_privados_do_usuario(self):
        resposta = self.cli.get(f"/api/usuarios/{self.ana['id']}", headers=self.auth(self.token_ana))
        self.assertEqual(resposta.get_json()["email"], "ana.silva@teste.com")

    def test_perfil_privado_fica_invisivel_para_terceiros(self):
        ocultar = self.cli.put(
            f"/api/usuarios/{self.ana['id']}/consentimentos/ranking_publico",
            json={"aceito": False},
            headers=self.auth(self.token_ana),
        )
        self.assertEqual(ocultar.status_code, 200)
        treino = self.registrar_treino(self.ana, self.token_ana)

        perfil = self.cli.get(f"/api/usuarios/{self.ana['id']}", headers=self.auth(self.token_jovem))
        atividade = self.cli.get(f"/api/atividades/{treino['id']}", headers=self.auth(self.token_jovem))
        propria = self.cli.get(f"/api/atividades/{treino['id']}", headers=self.auth(self.token_ana))
        self.assertEqual(perfil.status_code, 404)
        self.assertEqual(atividade.status_code, 404)
        self.assertEqual(propria.status_code, 200)

    def test_atividade_de_perfil_publico_e_visivel_para_logados(self):
        treino = self.registrar_treino(self.ana, self.token_ana)
        resposta = self.cli.get(f"/api/atividades/{treino['id']}", headers=self.auth(self.token_jovem))
        self.assertEqual(resposta.status_code, 200)


class TestBuscaRestrita(BaseTeste):

    def setUp(self):
        super().setUp()
        self.eu, self.token = self.criar_usuario_logado("Marcos Busca")
        self.cadastrar("Pedro Encontravel")
        self.cadastrar("Paula Sem Busca", consentimentos={"busca_perfil": False})
        self.cadastrar("Pablo Privado", consentimentos={"ranking_publico": False})

    def buscar(self, termo):
        return self.cli.get(
            "/api/usuarios/busca", query_string={"nome": termo}, headers=self.auth(self.token)
        )

    def test_exige_login(self):
        resposta = self.cli.get("/api/usuarios/busca", query_string={"nome": "pe"})
        self.assertEqual(resposta.status_code, 401)

    def test_exige_minimo_de_duas_letras(self):
        for termo in ("", " ", "p", " p "):
            with self.subTest(termo=termo):
                self.assertEqual(self.buscar(termo).status_code, 400)
        sem_parametro = self.cli.get("/api/usuarios/busca", headers=self.auth(self.token))
        self.assertEqual(sem_parametro.status_code, 400)
        self.assertEqual(self.buscar("pe").status_code, 200)

    def test_devolve_so_perfis_publicos_que_aceitaram_ser_encontrados(self):
        nomes = {u["nome"] for u in self.buscar("pe").get_json()}
        self.assertEqual(nomes, {"Pedro Encontravel"})
        self.assertEqual(self.buscar("Paula").get_json(), [])
        self.assertEqual(self.buscar("Pablo").get_json(), [])

    def test_devolve_so_campos_publicos(self):
        resultado = self.buscar("Pedro").get_json()[0]
        self.assertEqual(set(resultado), CAMPOS_PUBLICOS)

    def test_nao_devolve_o_proprio_usuario(self):
        self.assertEqual(self.buscar("Marcos").get_json(), [])

    def test_curingas_do_like_sao_tratados_como_texto(self):
        self.assertEqual(self.buscar("%%").get_json(), [])
        self.assertEqual(self.buscar("__").get_json(), [])

    def test_limita_a_20_resultados(self):
        for i in range(23):
            self.cadastrar(f"Zeca Numero {i:02d}")
        self.assertEqual(len(self.buscar("Zeca").get_json()), 20)

    def test_busca_por_cidade(self):
        usuario = self.cadastrar("Carlos Cidade")
        self.cli.put(
            f"/api/usuarios/{usuario['id']}", json={"cidade": "Uberlandia"},
            headers=self.auth(self.entrar(usuario["email"])),
        )
        nomes = {u["nome"] for u in self.buscar("Uberlandia").get_json()}
        self.assertEqual(nomes, {"Carlos Cidade"})

    def test_quem_revogou_ranking_publico_nao_aparece_em_lugar_nenhum(self):
        usuario, token = self.criar_usuario_logado("Revogado Depois")
        presente = {u["nome"] for u in self.buscar("Revogado").get_json()}
        self.assertEqual(presente, {"Revogado Depois"})

        self.cli.put(
            f"/api/usuarios/{usuario['id']}/consentimentos/ranking_publico",
            json={"aceito": False}, headers=self.auth(token),
        )

        self.assertEqual(self.buscar("Revogado").get_json(), [])
        perfil = self.cli.get(f"/api/usuarios/{usuario['id']}", headers=self.auth(self.token))
        self.assertEqual(perfil.status_code, 404)
        ranking = self.cli.get(f"/api/usuarios/{usuario['id']}/ranking", headers=self.auth(self.token))
        self.assertEqual(ranking.status_code, 404)

    def test_menor_de_idade_nao_aparece_na_busca(self):
        self.cadastrar(
            "Jovem Busca", idade=15,
            responsavel={"nome": "Resp Legal", "email": "resp.jovembusca@teste.com"},
        )
        self.assertEqual(self.buscar("Jovem Busca").get_json(), [])

    def test_perfil_alheio_nao_tem_email_idade_data_nascimento_peso_nem_altura(self):
        resultado = self.buscar("Pedro").get_json()[0]
        for campo in ("email", "idade", "data_nascimento", "peso", "altura", "responsavel"):
            self.assertNotIn(campo, resultado)


class TestDataDeNascimento(BaseTeste):

    def _cadastrar_com_data(self, nome, data_nascimento, email=None, responsavel=None, autorizacao=None):
        email = email or nome.lower().replace(" ", ".") + "@teste.com"
        corpo = {
            "nome": nome,
            "email": email,
            "data_nascimento": data_nascimento,
            "senha": SENHA,
            "aceite_termos": True,
            "consentimentos": {},
        }
        if responsavel is not None:
            corpo["responsavel"] = responsavel
        if autorizacao is not None:
            corpo["autorizacao_responsavel"] = autorizacao
        return self.cli.post("/api/usuarios", json=corpo)

    def test_vespera_do_13o_aniversario_ainda_bloqueia(self):
        hoje = date.today()
        nascimento = hoje.replace(year=hoje.year - 13) + timedelta(days=1)
        resposta = self._cadastrar_com_data("Quase Treze", nascimento.isoformat())
        self.assertEqual(resposta.status_code, 400)
        self.assertIn("13 anos", resposta.get_json()["erro"])

    def test_dia_do_13o_aniversario_libera_o_cadastro_com_responsavel(self):
        hoje = date.today()
        nascimento = hoje.replace(year=hoje.year - 13)

        sem_responsavel = self._cadastrar_com_data("Treze Hoje", nascimento.isoformat())
        self.assertEqual(sem_responsavel.status_code, 400)

        responsavel = {"nome": "Resp Legal", "email": "resp.trezehoje@teste.com"}
        com_responsavel = self._cadastrar_com_data(
            "Treze Hoje Ok", nascimento.isoformat(),
            email="trezehoje.ok@teste.com", responsavel=responsavel, autorizacao=True,
        )
        self.assertEqual(com_responsavel.status_code, 201)
        self.assertEqual(com_responsavel.get_json()["usuario"]["idade"], 13)

    def test_vespera_do_18o_aniversario_ainda_exige_responsavel(self):
        hoje = date.today()
        nascimento = hoje.replace(year=hoje.year - 18) + timedelta(days=1)

        sem_responsavel = self._cadastrar_com_data("Quase Dezoito", nascimento.isoformat())
        self.assertEqual(sem_responsavel.status_code, 400)

        responsavel = {"nome": "Resp Legal", "email": "resp.quasedezoito@teste.com"}
        com_responsavel = self._cadastrar_com_data(
            "Quase Dezoito Ok", nascimento.isoformat(),
            email="quasedezoito.ok@teste.com", responsavel=responsavel, autorizacao=True,
        )
        self.assertEqual(com_responsavel.status_code, 201)
        self.assertEqual(com_responsavel.get_json()["usuario"]["idade"], 17)

    def test_dia_do_18o_aniversario_nao_exige_responsavel(self):
        hoje = date.today()
        nascimento = hoje.replace(year=hoje.year - 18)
        resposta = self._cadastrar_com_data("Dezoito Hoje", nascimento.isoformat())
        self.assertEqual(resposta.status_code, 201)
        self.assertEqual(resposta.get_json()["usuario"]["idade"], 18)

    def test_nascido_em_29_de_fevereiro(self):
        resposta = self._cadastrar_com_data("Bissexto", "2000-02-29")
        self.assertEqual(resposta.status_code, 201)
        self.assertGreaterEqual(resposta.get_json()["usuario"]["idade"], 18)

    def test_data_futura_e_rejeitada(self):
        amanha = (date.today() + timedelta(days=1)).isoformat()
        resposta = self._cadastrar_com_data("Futuro", amanha)
        self.assertEqual(resposta.status_code, 400)
        self.assertIn("futuro", resposta.get_json()["erro"])

    def test_formato_invalido_e_rejeitado(self):
        for valor in ["15/05/2000", "2000-13-40", "não é data", "", None]:
            resposta = self._cadastrar_com_data("Formato Invalido", valor, email=f"fmt{valor}@teste.com")
            self.assertEqual(resposta.status_code, 400, valor)

    def test_conta_antiga_so_com_idade_continua_funcionando(self):
        usuario, token = self.criar_usuario_logado("Conta Antiga")
        with self.app.app_context():
            registro = db.session.get(Usuario, usuario["id"])
            registro.data_nascimento = None
            registro.idade = 40
            db.session.commit()

        resposta = self.cli.get("/api/eu", headers=self.auth(token))
        self.assertEqual(resposta.status_code, 200)
        self.assertEqual(resposta.get_json()["usuario"]["idade"], 40)
        self.assertIsNone(resposta.get_json()["usuario"]["data_nascimento"])

    def test_data_de_nascimento_nao_aparece_para_outro_usuario(self):
        dono, token_dono = self.criar_usuario_logado("Dono Data")
        _, token_outro = self.criar_usuario_logado("Outro Data")

        perfil = self.cli.get(f"/api/usuarios/{dono['id']}", headers=self.auth(token_outro))
        self.assertEqual(perfil.status_code, 200)
        self.assertNotIn("data_nascimento", perfil.get_json())
        self.assertNotIn("idade", perfil.get_json())

        busca = self.cli.get("/api/usuarios/busca?nome=Dono+Data", headers=self.auth(token_outro))
        self.assertEqual(busca.status_code, 200)
        for resultado in busca.get_json():
            self.assertNotIn("data_nascimento", resultado)
            self.assertNotIn("idade", resultado)


class TestConteudoDeMenores(BaseTeste):

    def setUp(self):
        super().setUp()
        self.menor, self.token_menor = self.criar_usuario_logado(
            "Miguel Menor", idade=15, responsavel={"nome": "Responsavel Teste", "email": "resp.menor@teste.com"}
        )
        self.adulto, self.token_adulto = self.criar_usuario_logado("Ana Adulta", idade=30)

    def registrar_treino(self, usuario, token, titulo):
        resposta = self.cli.post(
            f"/api/usuarios/{usuario['id']}/atividades",
            json={"tipo": "cardio", "titulo": titulo, "tempo_min": 20},
            headers={"Authorization": "Bearer " + token},
        )
        self.assertEqual(resposta.status_code, 201, resposta.get_data(as_text=True))
        return resposta.get_json()["atividade"]

    def feed(self, token):
        resposta = self.cli.get("/api/feed", headers={"Authorization": "Bearer " + token})
        self.assertEqual(resposta.status_code, 200)
        return resposta.get_json()

    def test_adulto_nao_le_treino_de_menor_por_id(self):
        atividade = self.registrar_treino(self.menor, self.token_menor, "Corrida do menor")
        resposta = self.cli.get(
            f"/api/atividades/{atividade['id']}", headers={"Authorization": "Bearer " + self.token_adulto}
        )
        self.assertEqual(resposta.status_code, 404)

    def test_feed_de_adulto_nao_traz_itens_do_menor(self):
        self.registrar_treino(self.menor, self.token_menor, "Corrida do menor")
        self.registrar_treino(self.adulto, self.token_adulto, "Treino da adulta")
        donos = {item["usuario"]["id"] for item in self.feed(self.token_adulto)}
        self.assertIn(self.adulto["id"], donos)
        self.assertNotIn(self.menor["id"], donos)

    def test_menor_ve_o_proprio_treino_por_id_e_no_feed(self):
        atividade = self.registrar_treino(self.menor, self.token_menor, "Corrida do menor")
        resposta = self.cli.get(
            f"/api/atividades/{atividade['id']}", headers={"Authorization": "Bearer " + self.token_menor}
        )
        self.assertEqual(resposta.status_code, 200)
        donos = {item["usuario"]["id"] for item in self.feed(self.token_menor)}
        self.assertIn(self.menor["id"], donos)

    def postar(self, token, texto):
        resposta = self.cli.post(
            "/api/postagens", data={"texto": texto},
            headers={"Authorization": "Bearer " + token}, content_type="multipart/form-data",
        )
        self.assertEqual(resposta.status_code, 201, resposta.get_data(as_text=True))
        postagem = resposta.get_json()["postagem"]
        return postagem.get("id") or postagem.get("id_postagem")

    def acao_de_adulto(self, metodo, caminho, corpo=None):
        return self.cli.open(caminho, method=metodo, json=corpo, headers=self.auth(self.token_adulto))

    def test_adulto_nao_curte_treino_de_menor(self):
        atividade = self.registrar_treino(self.menor, self.token_menor, "Corrida do menor")
        resposta = self.acao_de_adulto("POST", f"/api/feed/atividade/{atividade['id']}/curtir")
        self.assertEqual(resposta.status_code, 404)

    def test_adulto_nao_comenta_nem_lista_comentarios_de_treino_de_menor(self):
        atividade = self.registrar_treino(self.menor, self.token_menor, "Corrida do menor")
        caminho = f"/api/feed/atividade/{atividade['id']}/comentarios"
        self.assertEqual(self.acao_de_adulto("POST", caminho, {"texto": "Oi"}).status_code, 404)
        self.assertEqual(self.acao_de_adulto("GET", caminho).status_code, 404)

    def test_adulto_nao_curte_nem_comenta_postagem_de_menor(self):
        postagem = self.postar(self.token_menor, "Post do menor")
        self.assertEqual(
            self.acao_de_adulto("POST", f"/api/feed/postagem/{postagem}/curtir").status_code, 404
        )
        self.assertEqual(
            self.acao_de_adulto("POST", f"/api/feed/postagem/{postagem}/comentarios", {"texto": "Oi"}).status_code, 404
        )

    def test_adulto_nao_exclui_comentario_em_conteudo_de_menor(self):
        atividade = self.registrar_treino(self.menor, self.token_menor, "Corrida do menor")
        comentario = self.cli.post(
            f"/api/feed/atividade/{atividade['id']}/comentarios",
            json={"texto": "Comentario de teste"},
            headers=self.auth(self.token_menor),
        ).get_json()["comentario"]["id"]
        resposta = self.acao_de_adulto("DELETE", f"/api/comentarios/{comentario}")
        self.assertEqual(resposta.status_code, 404)

    def test_menor_curte_comenta_lista_e_exclui_o_proprio_conteudo(self):
        atividade = self.registrar_treino(self.menor, self.token_menor, "Corrida do menor")
        caminho = f"/api/feed/atividade/{atividade['id']}/comentarios"
        curtida = self.cli.post(
            f"/api/feed/atividade/{atividade['id']}/curtir", headers=self.auth(self.token_menor)
        )
        self.assertEqual(curtida.status_code, 200)
        comentario = self.cli.post(caminho, json={"texto": "Bom treino"}, headers=self.auth(self.token_menor))
        self.assertEqual(comentario.status_code, 201)
        lista = self.cli.get(caminho, headers=self.auth(self.token_menor)).get_json()
        self.assertIn("Bom treino", [c["texto"] for c in lista])
        excluido = self.cli.delete(
            f"/api/comentarios/{comentario.get_json()['comentario']['id']}", headers=self.auth(self.token_menor)
        )
        self.assertEqual(excluido.status_code, 200)

    def test_menor_ve_os_proprios_comentarios_em_postagem(self):
        postagem = self.postar(self.token_menor, "Post do menor")
        self.cli.post(
            f"/api/feed/postagem/{postagem}/comentarios", json={"texto": "Comentario no proprio post"},
            headers=self.auth(self.token_menor),
        )
        lista = self.cli.get(
            f"/api/feed/postagem/{postagem}/comentarios", headers=self.auth(self.token_menor)
        ).get_json()
        self.assertEqual(len(lista), 1)

    def test_postagem_de_menor_nao_aparece_no_feed_de_adulto(self):
        self.cli.post(
            "/api/postagens", data={"texto": "Post do menor"},
            headers={"Authorization": "Bearer " + self.token_menor}, content_type="multipart/form-data",
        )
        self.cli.post(
            "/api/postagens", data={"texto": "Post da adulta"},
            headers={"Authorization": "Bearer " + self.token_adulto}, content_type="multipart/form-data",
        )
        donos = {item["usuario"]["id"] for item in self.feed(self.token_adulto)}
        self.assertIn(self.adulto["id"], donos)
        self.assertNotIn(self.menor["id"], donos)


class TestCamposDoPerfil(BaseTeste):

    def setUp(self):
        super().setUp()
        self.pasta_uploads = tempfile.mkdtemp()
        self.app.config["UPLOAD_FOLDER"] = self.pasta_uploads
        self.usuario, self.token = self.criar_usuario_logado("Ana Campos", idade=30)

    def tearDown(self):
        shutil.rmtree(self.pasta_uploads, ignore_errors=True)
        super().tearDown()

    def atualizar(self, corpo, token=None):
        return self.cli.put(
            f"/api/usuarios/{self.usuario['id']}", json=corpo, headers=self.auth(token or self.token)
        )

    def eu(self):
        return self.cli.get("/api/eu", headers=self.auth(self.token)).get_json()["usuario"]

    def test_foto_com_url_arbitraria_e_recusada(self):
        resposta = self.atualizar({"foto": "http://x.example/a'); \"><img src=x onerror=\"window.__xss=1\">"})
        self.assertEqual(resposta.status_code, 400)
        self.assertIsNone(self.eu()["foto"])

    def test_foto_com_caminho_de_upload_e_recusada_pelo_perfil(self):
        resposta = self.atualizar({"foto": f"/uploads/usuario_{self.usuario['id']}_0123456789abcdef.png"})
        self.assertEqual(resposta.status_code, 400)

    def test_foto_nula_no_perfil_e_ignorada(self):
        resposta = self.atualizar({"foto": None, "nome": "Ana Campos"})
        self.assertEqual(resposta.status_code, 200, resposta.get_data(as_text=True))
        self.assertIsNone(self.eu()["foto"])

    def test_upload_de_foto_continua_gravando_no_formato_esperado(self):
        png = b"\x89PNG\r\n\x1a\n" + b"\x00" * 16
        resposta = self.cli.post(
            f"/api/usuarios/{self.usuario['id']}/foto",
            data={"foto": (io.BytesIO(png), "rosto.png")},
            headers=self.auth(self.token),
            content_type="multipart/form-data",
        )
        self.assertEqual(resposta.status_code, 200, resposta.get_data(as_text=True))
        caminho = resposta.get_json()["usuario"]["foto"]
        self.assertRegex(caminho, rf"^/uploads/usuario_{self.usuario['id']}_[0-9a-f]{{16}}\.png$")

    def test_campos_que_o_cliente_nao_define_sao_ignorados(self):
        resposta = self.atualizar({
            "xp": 999999, "nivel": "elite", "admin": True, "id_usuario": 999,
            "perfil_publico": False, "senha_hash": "x",
        })
        self.assertEqual(resposta.status_code, 200)
        dados = self.eu()
        self.assertEqual(dados["xp"], 0)
        self.assertFalse(dados["admin"])
        self.assertEqual(dados["id"], self.usuario["id"])


class TestTrocaDeEmailESenha(BaseTeste):

    def setUp(self):
        super().setUp()
        self.usuario, self.token = self.criar_usuario_logado("Dora Troca", idade=30)
        self.outro, self.token_outro = self.criar_usuario_logado("Eva Outra", idade=30)

    def atualizar(self, corpo, token=None):
        return self.cli.put(
            f"/api/usuarios/{self.usuario['id']}", json=corpo, headers=self.auth(token or self.token)
        )

    def login(self, email, senha=SENHA):
        return self.cli.post("/api/login", json={"email": email, "senha": senha})

    def test_trocar_email_sem_senha_atual_recebe_400(self):
        resposta = self.atualizar({"email": "nova.dora@teste.com"})
        self.assertEqual(resposta.status_code, 400)
        self.assertEqual(self.login(self.usuario["email"]).status_code, 200)

    def test_trocar_email_com_senha_atual_errada_recebe_403(self):
        resposta = self.atualizar({"email": "nova.dora@teste.com", "senha_atual": "errada123"})
        self.assertEqual(resposta.status_code, 403)
        self.assertEqual(self.login(self.usuario["email"]).status_code, 200)

    def test_trocar_email_com_senha_atual_correta_funciona(self):
        resposta = self.atualizar({"email": "nova.dora@teste.com", "senha_atual": SENHA})
        self.assertEqual(resposta.status_code, 200, resposta.get_data(as_text=True))
        self.assertEqual(self.login("nova.dora@teste.com").status_code, 200)

    def test_trocar_senha_sem_senha_atual_recebe_400(self):
        resposta = self.atualizar({"senha": "novasenha123"})
        self.assertEqual(resposta.status_code, 400)
        self.assertEqual(self.login(self.usuario["email"], SENHA).status_code, 200)

    def test_trocar_senha_com_senha_atual_errada_recebe_403(self):
        resposta = self.atualizar({"senha": "novasenha123", "senha_atual": "errada123"})
        self.assertEqual(resposta.status_code, 403)
        self.assertEqual(self.login(self.usuario["email"], SENHA).status_code, 200)

    def test_trocar_senha_com_senha_atual_correta_funciona(self):
        resposta = self.atualizar({"senha": "novasenha123", "senha_atual": SENHA})
        self.assertEqual(resposta.status_code, 200, resposta.get_data(as_text=True))
        self.assertEqual(self.login(self.usuario["email"], "novasenha123").status_code, 200)
        self.assertEqual(self.login(self.usuario["email"], SENHA).status_code, 401)

    def test_email_duplicado_recebe_409_e_nunca_500(self):
        resposta = self.atualizar({"email": self.outro["email"], "senha_atual": SENHA})
        self.assertEqual(resposta.status_code, 409)

    def test_email_duplicado_que_chega_so_no_banco_recebe_409(self):
        from repositories.repository import UsuarioRepository
        with mock.patch.object(UsuarioRepository, "buscar_por_email", return_value=None):
            resposta = self.atualizar({"email": self.outro["email"], "senha_atual": SENHA})
        self.assertEqual(resposta.status_code, 409)

    def test_mesmo_email_sem_senha_atual_nao_exige_confirmacao(self):
        resposta = self.atualizar({"email": self.usuario["email"], "nome": "Dora Renomeada"})
        self.assertEqual(resposta.status_code, 200, resposta.get_data(as_text=True))

    def test_alterar_so_o_nome_nao_exige_senha_atual(self):
        resposta = self.atualizar({"nome": "Dora Sem Senha"})
        self.assertEqual(resposta.status_code, 200, resposta.get_data(as_text=True))


class TestAutorizacaoDoResponsavel(BaseTeste):

    def setUp(self):
        super().setUp()
        self.menor, self.token_menor = self.criar_usuario_logado(
            "Lia Menor", idade=15, responsavel={"nome": "Responsavel Teste", "email": "resp.lia@teste.com"}
        )
        self.adulto, self.token_adulto = self.criar_usuario_logado("Bia Adulta", idade=30)

    def atualizar(self, usuario, token, corpo):
        return self.cli.put(f"/api/usuarios/{usuario['id']}", json=corpo, headers=self.auth(token))

    def test_menor_nao_se_autoautoriza_pelo_perfil(self):
        resposta = self.atualizar(self.menor, self.token_menor, {
            "data_nascimento": data_nascimento_para_idade(14),
            "responsavel": {"nome": "Eu Mesma", "email": "eu@teste.com"},
            "autorizacao_responsavel": True,
        })
        self.assertEqual(resposta.status_code, 400)

    def test_menor_nao_grava_autorizacao_do_responsavel_direto(self):
        resposta = self.atualizar(self.menor, self.token_menor, {
            "responsavel_autorizado_em": "2020-01-01T00:00:00+00:00",
        })
        self.assertEqual(resposta.status_code, 400)

    def test_menor_nao_vira_adulto_pela_data_de_nascimento(self):
        resposta = self.atualizar(self.menor, self.token_menor, {
            "data_nascimento": data_nascimento_para_idade(30),
        })
        self.assertEqual(resposta.status_code, 400)
        self.assertIn("menor", resposta.get_json()["erro"].lower())

    def test_adulto_nao_vira_menor_pela_data_de_nascimento(self):
        resposta = self.atualizar(self.adulto, self.token_adulto, {
            "data_nascimento": data_nascimento_para_idade(15),
            "responsavel": {"nome": "Responsavel Teste", "email": "resp.bia@teste.com"},
            "autorizacao_responsavel": True,
        })
        self.assertEqual(resposta.status_code, 400)

    def test_menor_corrige_data_dentro_da_faixa_de_menor(self):
        resposta = self.atualizar(self.menor, self.token_menor, {
            "data_nascimento": data_nascimento_para_idade(16),
        })
        self.assertEqual(resposta.status_code, 200, resposta.get_data(as_text=True))


if __name__ == "__main__":
    unittest.main()
