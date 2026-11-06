import io
import os
import re
import shutil
import tempfile
import threading
import time
import unittest
from unittest import mock

from services.usuario import _LimitadorLogin
from tests.test_seguranca import SENHA, BaseTeste, data_nascimento_para_idade


PNG_VALIDO = b"\x89PNG\r\n\x1a\n" + b"\x00" * 16
JPEG_VALIDO = b"\xff\xd8\xff\xe0" + b"\x00" * 16


class TestErrosEmJson(BaseTeste):

    def test_rota_inexistente_devolve_json(self):
        resposta = self.cli.get("/api/rota-que-nao-existe")
        self.assertEqual(resposta.status_code, 404)
        self.assertEqual(resposta.content_type, "application/json")
        self.assertIn("erro", resposta.get_json())

    def test_metodo_nao_permitido_devolve_json(self):
        resposta = self.cli.get("/api/usuarios")
        self.assertEqual(resposta.status_code, 405)
        self.assertIn("erro", resposta.get_json())

    def test_corpo_grande_demais_devolve_413_em_json(self):
        usuario, token = self.criar_usuario_logado("Ana Grande")
        conteudo = b"a" * (4 * 1024 * 1024)
        resposta = self.cli.post(
            f"/api/usuarios/{usuario['id']}/foto",
            data={"foto": (io.BytesIO(conteudo), "foto.png")},
            content_type="multipart/form-data",
            headers=self.auth(token),
        )
        self.assertEqual(resposta.status_code, 413)
        self.assertIn("erro", resposta.get_json())

    def test_erro_inesperado_nao_vaza_html(self):
        with mock.patch(
            "controllers.usuario_controller.ConsultarEstatisticasService.executar",
            side_effect=RuntimeError("falha simulada"),
        ):
            resposta = self.cli.get("/api/estatisticas")
        self.assertEqual(resposta.status_code, 500)
        self.assertEqual(resposta.content_type, "application/json")
        self.assertIn("erro", resposta.get_json())


class TestLimitesDeCampos(BaseTeste):

    def setUp(self):
        super().setUp()
        self.usuario, self.token = self.criar_usuario_logado("Ana Limite")

    def registrar(self, **campos):
        corpo = {"tipo": "musculacao", "tempo_min": 30}
        corpo.update(campos)
        return self.cli.post(
            f"/api/usuarios/{self.usuario['id']}/atividades",
            json=corpo,
            headers=self.auth(self.token),
        )

    def test_tempo_acima_do_limite_e_recusado(self):
        self.assertEqual(self.registrar(tempo_min=10000).status_code, 400)

    def test_carga_acima_do_limite_e_recusada(self):
        self.assertEqual(self.registrar(carga_kg=10000, repeticoes=5).status_code, 400)

    def test_repeticoes_acima_do_limite_e_recusada(self):
        self.assertEqual(self.registrar(carga_kg=50, repeticoes=5000).status_code, 400)

    def test_distancia_acima_do_limite_e_recusada(self):
        resposta = self.registrar(tipo="cardio", tempo_min=None, distancia_km=1000)
        self.assertEqual(resposta.status_code, 400)

    def test_valores_dentro_do_limite_sao_aceitos(self):
        resposta = self.registrar(carga_kg=100, repeticoes=10)
        self.assertEqual(resposta.status_code, 201)


class TestCorridaCadastroEmail(BaseTeste):

    def test_cadastro_concorrente_do_mesmo_email_nao_gera_500(self):
        email = "corrida@teste.com"
        corpo = {
            "nome": "Primeiro", "email": email, "data_nascimento": data_nascimento_para_idade(25), "senha": SENHA,
            "aceite_termos": True, "consentimentos": {},
        }
        with mock.patch("services.usuario.cadastrar_usuario.UsuarioRepository.buscar_por_email", return_value=None):
            primeira = self.cli.post("/api/usuarios", json=corpo)
            segunda = self.cli.post("/api/usuarios", json=dict(corpo, nome="Segundo"))

        self.assertEqual(primeira.status_code, 201)
        self.assertEqual(segunda.status_code, 409)
        self.assertIn("erro", segunda.get_json())


class TestCorridaCurtida(BaseTeste):

    def test_curtida_concorrente_nao_gera_500(self):
        usuario, token = self.criar_usuario_logado("Ana Corrida")
        postagem = self.cli.post(
            "/api/postagens", data={"texto": "Treino"}, headers=self.auth(token)
        )
        id_postagem = postagem.get_json()["postagem"]["id"]

        with mock.patch("services.curtida.alternar_curtida.CurtidaRepository.buscar", return_value=None):
            primeira = self.cli.post(
                f"/api/feed/postagem/{id_postagem}/curtir", headers=self.auth(token)
            )
            segunda = self.cli.post(
                f"/api/feed/postagem/{id_postagem}/curtir", headers=self.auth(token)
            )

        self.assertEqual(primeira.status_code, 200)
        self.assertEqual(segunda.status_code, 200)
        self.assertTrue(primeira.get_json()["curti"])
        self.assertTrue(segunda.get_json()["curti"])
        self.assertEqual(segunda.get_json()["curtidas"], 1)


class TestLimpezaDeImagens(BaseTeste):

    def setUp(self):
        super().setUp()
        self.pasta_uploads = tempfile.mkdtemp()
        self.app.config["UPLOAD_FOLDER"] = self.pasta_uploads

    def tearDown(self):
        shutil.rmtree(self.pasta_uploads, ignore_errors=True)

    def _enviar_foto_de_perfil(self, usuario, token):
        resposta = self.cli.post(
            f"/api/usuarios/{usuario['id']}/foto",
            data={"foto": (io.BytesIO(PNG_VALIDO), "avatar.png")},
            content_type="multipart/form-data",
            headers=self.auth(token),
        )
        self.assertEqual(resposta.status_code, 200, resposta.get_data(as_text=True))
        return resposta.get_json()["usuario"]["foto"]

    def test_apaga_foto_de_perfil_ao_excluir_conta(self):
        usuario, token = self.criar_usuario_logado("Ana Foto")
        caminho = self._enviar_foto_de_perfil(usuario, token)
        nome_arquivo = os.path.basename(caminho)
        self.assertTrue(os.path.exists(os.path.join(self.pasta_uploads, nome_arquivo)))

        exclusao = self.cli.delete(f"/api/usuarios/{usuario['id']}", headers=self.auth(token))
        self.assertEqual(exclusao.status_code, 200)
        self.assertFalse(os.path.exists(os.path.join(self.pasta_uploads, nome_arquivo)))

    def test_apaga_fotos_das_postagens_ao_excluir_conta(self):
        usuario, token = self.criar_usuario_logado("Bia Foto")
        postagem = self.cli.post(
            "/api/postagens",
            data={"texto": "Treino com foto", "foto": (io.BytesIO(PNG_VALIDO), "post.png")},
            content_type="multipart/form-data",
            headers=self.auth(token),
        )
        self.assertEqual(postagem.status_code, 201, postagem.get_data(as_text=True))
        nome_arquivo = os.path.basename(postagem.get_json()["postagem"]["foto"])
        self.assertTrue(os.path.exists(os.path.join(self.pasta_uploads, nome_arquivo)))

        exclusao = self.cli.delete(f"/api/usuarios/{usuario['id']}", headers=self.auth(token))
        self.assertEqual(exclusao.status_code, 200)
        self.assertFalse(os.path.exists(os.path.join(self.pasta_uploads, nome_arquivo)))


class TestNomeDeArquivoDeImagem(BaseTeste):

    def setUp(self):
        super().setUp()
        self.pasta_uploads = tempfile.mkdtemp()
        self.app.config["UPLOAD_FOLDER"] = self.pasta_uploads

    def tearDown(self):
        shutil.rmtree(self.pasta_uploads, ignore_errors=True)

    def _enviar_foto_de_perfil(self, usuario, token, nome_arquivo="avatar.png", conteudo=PNG_VALIDO):
        resposta = self.cli.post(
            f"/api/usuarios/{usuario['id']}/foto",
            data={"foto": (io.BytesIO(conteudo), nome_arquivo)},
            content_type="multipart/form-data",
            headers=self.auth(token),
        )
        self.assertEqual(resposta.status_code, 200, resposta.get_data(as_text=True))
        return resposta.get_json()["usuario"]["foto"]

    def _enviar_postagem_com_foto(self, token, nome_arquivo="post.png", conteudo=PNG_VALIDO):
        resposta = self.cli.post(
            "/api/postagens",
            data={"texto": "Treino com foto", "foto": (io.BytesIO(conteudo), nome_arquivo)},
            content_type="multipart/form-data",
            headers=self.auth(token),
        )
        self.assertEqual(resposta.status_code, 201, resposta.get_data(as_text=True))
        return resposta.get_json()["postagem"]["foto"]

    def test_foto_de_perfil_gera_nome_com_prefixo_usuario_e_id(self):
        usuario, token = self.criar_usuario_logado("Ana Nome")
        caminho = self._enviar_foto_de_perfil(usuario, token)
        padrao = r"^/uploads/usuario_" + str(usuario["id"]) + r"_[0-9a-f]{16}\.png$"
        self.assertRegex(caminho, padrao)

    def test_foto_de_postagem_gera_nome_com_prefixo_postagem_e_id(self):
        usuario, token = self.criar_usuario_logado("Bia Nome")
        caminho = self._enviar_postagem_com_foto(token)
        padrao = r"^/uploads/postagem_" + str(usuario["id"]) + r"_[0-9a-f]{16}\.png$"
        self.assertRegex(caminho, padrao)

    def test_extensao_jpeg_e_normalizada_para_jpg_no_perfil(self):
        usuario, token = self.criar_usuario_logado("Cris Jpeg")
        caminho = self._enviar_foto_de_perfil(usuario, token, nome_arquivo="foto.jpeg", conteudo=JPEG_VALIDO)
        self.assertTrue(caminho.endswith(".jpg"))
        self.assertFalse(caminho.endswith(".jpeg"))

    def test_extensao_jpeg_e_normalizada_para_jpg_na_postagem(self):
        _, token = self.criar_usuario_logado("Davi Jpeg")
        caminho = self._enviar_postagem_com_foto(token, nome_arquivo="post.jpeg", conteudo=JPEG_VALIDO)
        self.assertTrue(caminho.endswith(".jpg"))
        self.assertFalse(caminho.endswith(".jpeg"))

    def test_nova_foto_de_perfil_substitui_a_anterior(self):
        usuario, token = self.criar_usuario_logado("Elis Troca")
        caminho_antigo = self._enviar_foto_de_perfil(usuario, token)
        nome_antigo = os.path.basename(caminho_antigo)
        self.assertTrue(os.path.exists(os.path.join(self.pasta_uploads, nome_antigo)))

        time.sleep(1.1)
        caminho_novo = self._enviar_foto_de_perfil(usuario, token, nome_arquivo="novo.png")
        nome_novo = os.path.basename(caminho_novo)

        self.assertNotEqual(nome_antigo, nome_novo)
        self.assertFalse(os.path.exists(os.path.join(self.pasta_uploads, nome_antigo)))
        self.assertTrue(os.path.exists(os.path.join(self.pasta_uploads, nome_novo)))

    def test_foto_de_postagem_nao_apaga_postagens_anteriores(self):
        usuario, token = self.criar_usuario_logado("Fabio Mantem")
        caminho_1 = self._enviar_postagem_com_foto(token, nome_arquivo="um.png")
        time.sleep(1.1)
        caminho_2 = self._enviar_postagem_com_foto(token, nome_arquivo="dois.png")

        nome_1 = os.path.basename(caminho_1)
        nome_2 = os.path.basename(caminho_2)
        self.assertNotEqual(nome_1, nome_2)
        self.assertTrue(os.path.exists(os.path.join(self.pasta_uploads, nome_1)))
        self.assertTrue(os.path.exists(os.path.join(self.pasta_uploads, nome_2)))


class TestAssinaturaDeImagem(BaseTeste):

    def setUp(self):
        super().setUp()
        self.pasta_uploads = tempfile.mkdtemp()
        self.app.config["UPLOAD_FOLDER"] = self.pasta_uploads
        self.usuario, self.token = self.criar_usuario_logado("Gabi Assinatura")

    def tearDown(self):
        shutil.rmtree(self.pasta_uploads, ignore_errors=True)

    def _enviar(self, nome_arquivo, conteudo):
        return self.cli.post(
            f"/api/usuarios/{self.usuario['id']}/foto",
            data={"foto": (io.BytesIO(conteudo), nome_arquivo)},
            content_type="multipart/form-data",
            headers=self.auth(self.token),
        )

    def test_html_com_nome_de_png_e_rejeitado(self):
        resposta = self._enviar("ataque.png", b"<html><script>alert(1)</script></html>")
        self.assertEqual(resposta.status_code, 400)
        self.assertEqual(os.listdir(self.pasta_uploads), [])

    def test_png_com_extensao_jpg_e_rejeitado(self):
        resposta = self._enviar("disfarce.jpg", PNG_VALIDO)
        self.assertEqual(resposta.status_code, 400)

    def test_gif_valido_e_aceito(self):
        resposta = self._enviar("animado.gif", b"GIF89a" + b"\x00" * 16)
        self.assertEqual(resposta.status_code, 200)
        self.assertTrue(resposta.get_json()["usuario"]["foto"].endswith(".gif"))

    def test_webp_valido_e_aceito(self):
        resposta = self._enviar("imagem.webp", b"RIFF" + b"\x00" * 4 + b"WEBP" + b"\x00" * 8)
        self.assertEqual(resposta.status_code, 200)

    def test_cabecalho_nosniff_nas_respostas_de_uploads(self):
        resposta = self._enviar("avatar.png", PNG_VALIDO)
        caminho = resposta.get_json()["usuario"]["foto"]
        arquivo = self.cli.get(caminho)
        self.assertEqual(arquivo.status_code, 200)
        self.assertEqual(arquivo.headers.get("X-Content-Type-Options"), "nosniff")


class TestLimiteDeTentativasDeLogin(BaseTeste):

    def test_bloqueia_apos_tentativas_demais_e_devolve_429(self):
        usuario = self.cadastrar("Ana Login", email="ana.login@teste.com")

        for _ in range(5):
            resposta = self.cli.post(
                "/api/login", json={"email": usuario["email"], "senha": "errada"}
            )
            self.assertEqual(resposta.status_code, 401)

        bloqueado = self.cli.post(
            "/api/login", json={"email": usuario["email"], "senha": SENHA}
        )
        self.assertEqual(bloqueado.status_code, 429)
        self.assertIn("erro", bloqueado.get_json())

    def test_contador_nao_se_corrompe_sob_concorrencia(self):
        chave = "ataque.concorrente@teste.com"
        NUM_THREADS = 20
        barreira = threading.Barrier(NUM_THREADS)

        def falhar():
            barreira.wait()
            _LimitadorLogin.registrar_falha(chave)

        threads = [threading.Thread(target=falhar) for _ in range(NUM_THREADS)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        registro = _LimitadorLogin._tentativas[chave]
        self.assertIsNotNone(registro["bloqueado_ate"])
        self.assertGreater(registro["bloqueado_ate"], time.time())

    def test_login_correto_reseta_o_contador_de_falhas(self):
        usuario = self.cadastrar("Bia Login", email="bia.login@teste.com")

        for _ in range(3):
            self.cli.post("/api/login", json={"email": usuario["email"], "senha": "errada"})

        correto = self.cli.post("/api/login", json={"email": usuario["email"], "senha": SENHA})
        self.assertEqual(correto.status_code, 200)

        for _ in range(3):
            resposta = self.cli.post(
                "/api/login", json={"email": usuario["email"], "senha": "errada"}
            )
            self.assertEqual(resposta.status_code, 401)

    def test_bloqueio_e_por_email_e_nao_afeta_outras_contas(self):
        self.cadastrar("Cris Login", email="cris.login@teste.com")
        outro = self.cadastrar("Davi Login", email="davi.login@teste.com")

        for _ in range(5):
            self.cli.post("/api/login", json={"email": "cris.login@teste.com", "senha": "errada"})

        resposta = self.cli.post("/api/login", json={"email": outro["email"], "senha": SENHA})
        self.assertEqual(resposta.status_code, 200)


if __name__ == "__main__":
    unittest.main()


class TestTetoDePontuacao(BaseTeste):

    def setUp(self):
        super().setUp()
        self.usuario, self.token = self.criar_usuario_logado("Ana Teto")

    def registrar(self, **campos):
        corpo = {"tipo": "musculacao", "tempo_min": 30}
        corpo.update(campos)
        return self.cli.post(
            f"/api/usuarios/{self.usuario['id']}/atividades",
            json=corpo,
            headers={"Authorization": "Bearer " + self.token},
        )

    def test_treino_acima_do_teto_por_treino_e_rejeitado(self):
        resposta = self.registrar(tipo="cardio", tempo_min=600, distancia_km=500)
        self.assertEqual(resposta.status_code, 400)
        self.assertIn("por treino", resposta.get_json()["erro"])

    def test_treino_realista_pesado_passa(self):
        resposta = self.registrar(tipo="musculacao", tempo_min=180, carga_kg=150, repeticoes=300)
        self.assertEqual(resposta.status_code, 201)

    def test_ultra_de_100_km_passa(self):
        resposta = self.registrar(tipo="cardio", tempo_min=600, distancia_km=100)
        self.assertEqual(resposta.status_code, 201)

    def test_limite_diario_bloqueia_treino_que_estouraria_o_dia(self):
        self.assertEqual(self.registrar(tipo="cardio", tempo_min=600, distancia_km=100).status_code, 201)
        resposta = self.registrar(tipo="cardio", tempo_min=600, distancia_km=100)
        self.assertEqual(resposta.status_code, 400)
        self.assertIn("diário", resposta.get_json()["erro"])

    def test_treino_pequeno_continua_passando_abaixo_do_limite_diario(self):
        self.assertEqual(self.registrar(tipo="cardio", tempo_min=600, distancia_km=100).status_code, 201)
        self.assertEqual(self.registrar(tipo="musculacao", tempo_min=10).status_code, 201)

    def test_limite_diario_nao_vale_no_dia_seguinte(self):
        from datetime import timedelta
        from utils import agora

        self.assertEqual(self.registrar(tipo="cardio", tempo_min=600, distancia_km=100).status_code, 201)
        amanha = agora() + timedelta(days=1)
        with mock.patch("services.atividade.apoio.agora", return_value=amanha):
            resposta = self.registrar(tipo="cardio", tempo_min=600, distancia_km=100)
        self.assertEqual(resposta.status_code, 201)


class TestNumerosInvalidos(BaseTeste):

    def setUp(self):
        super().setUp()
        self.usuario, self.token = self.criar_usuario_logado("Ana Numeros")
        self.cabecalho = {"Authorization": "Bearer " + self.token}

    def test_treino_com_nan_e_400(self):
        resposta = self.cli.post(
            f"/api/usuarios/{self.usuario['id']}/atividades",
            json={"tipo": "cardio", "tempo_min": "nan"},
            headers=self.cabecalho,
        )
        self.assertEqual(resposta.status_code, 400)

    def test_perfil_com_peso_nan_e_400(self):
        resposta = self.cli.put(
            f"/api/usuarios/{self.usuario['id']}", json={"peso": "nan"}, headers=self.cabecalho
        )
        self.assertEqual(resposta.status_code, 400)

    def test_perfil_com_altura_infinita_e_400(self):
        resposta = self.cli.put(
            f"/api/usuarios/{self.usuario['id']}", json={"altura": "inf"}, headers=self.cabecalho
        )
        self.assertEqual(resposta.status_code, 400)

    def test_meta_com_valor_objetivo_nan_e_400(self):
        resposta = self.cli.post(
            "/api/metas",
            json={"tipo": "curto_prazo", "tipo_metrica": "carga_maxima", "exercicio": "supino",
                  "titulo": "Meta", "valor_objetivo": "nan", "data_final": "2030-12-31"},
            headers=self.cabecalho,
        )
        self.assertEqual(resposta.status_code, 400)

    def test_meta_com_valor_objetivo_acima_do_maximo_e_400(self):
        resposta = self.cli.post(
            "/api/metas",
            json={"tipo": "curto_prazo", "tipo_metrica": "carga_maxima", "exercicio": "supino",
                  "titulo": "Meta", "valor_objetivo": 1e308, "data_final": "2030-12-31"},
            headers=self.cabecalho,
        )
        self.assertEqual(resposta.status_code, 400)

    def test_ranking_do_grupo_aceita_limite_invalido(self):
        grupo = self.cli.post("/api/grupos", json={"nome": "Grupo Numeros"}, headers=self.cabecalho).get_json()["grupo"]
        resposta = self.cli.get(f"/api/grupos/{grupo['id']}/ranking?limite=abc", headers=self.cabecalho)
        self.assertEqual(resposta.status_code, 200)


class TestExclusaoRemoveComentariosECurtidas(BaseTeste):

    def setUp(self):
        super().setUp()
        self.ana, self.token_ana = self.criar_usuario_logado("Ana Exclusao")
        self.bia, self.token_bia = self.criar_usuario_logado("Bia Exclusao")
        resposta = self.cli.post(
            f"/api/usuarios/{self.ana['id']}/atividades",
            json={"tipo": "cardio", "titulo": "Treino da Ana", "tempo_min": 20},
            headers=self.auth(self.token_ana),
        )
        self.atividade = resposta.get_json()["atividade"]

    def _item_do_feed(self):
        itens = self.cli.get("/api/feed", headers=self.auth(self.token_ana)).get_json()
        return next(i for i in itens if i["tipo_conteudo"] == "atividade" and i["id"] == self.atividade["id"])

    def test_excluir_conta_remove_comentarios_e_curtidas_do_usuario(self):
        self.cli.post(
            f"/api/feed/atividade/{self.atividade['id']}/comentarios",
            json={"texto": "Mandou bem"}, headers=self.auth(self.token_bia),
        )
        self.cli.post(
            f"/api/feed/atividade/{self.atividade['id']}/curtir", headers=self.auth(self.token_bia),
        )
        antes = self._item_do_feed()
        self.assertEqual((antes["comentarios"], antes["curtidas"]), (1, 1))

        exclusao = self.cli.delete(f"/api/usuarios/{self.bia['id']}", headers=self.auth(self.token_bia))
        self.assertEqual(exclusao.status_code, 200)

        depois = self._item_do_feed()
        self.assertEqual((depois["comentarios"], depois["curtidas"]), (0, 0))

    def test_excluir_conta_remove_conteudo_alheio_sobre_os_treinos_do_usuario(self):
        self.cli.post(
            f"/api/feed/atividade/{self.atividade['id']}/comentarios",
            json={"texto": "Comentario de outra pessoa"}, headers=self.auth(self.token_bia),
        )
        self.cli.post(
            f"/api/feed/atividade/{self.atividade['id']}/curtir", headers=self.auth(self.token_bia),
        )
        exclusao = self.cli.delete(f"/api/usuarios/{self.ana['id']}", headers=self.auth(self.token_ana))
        self.assertEqual(exclusao.status_code, 200)

        from database import db
        from models.model import Comentario, Curtida
        with self.app.app_context():
            self.assertEqual(Comentario.query.filter_by(tipo_alvo="atividade", id_alvo=self.atividade["id"]).count(), 0)
            self.assertEqual(Curtida.query.filter_by(tipo_alvo="atividade", id_alvo=self.atividade["id"]).count(), 0)
