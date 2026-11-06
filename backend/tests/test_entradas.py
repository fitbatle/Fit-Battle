import itertools
import json
import os
import re
import sys
import unittest
from datetime import date, timedelta
from unittest import mock

os.environ["DB_URI"] = "sqlite:///:memory:"
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tests.test_seguranca import BaseTeste, SENHA

ADMIN = "admin.varredura@teste.com"

VALORES = [123, 1.5, True, None, [], {}, "", "x" * 10000]

CORPOS_NAO_OBJETO = [[], "texto", 123, None]

CAMPOS = [
    "nome", "email", "senha", "data_nascimento", "aceite_termos", "consentimentos", "responsavel",
    "autorizacao_responsavel", "responsavel_nome", "responsavel_email", "responsavel_autorizado_em",
    "peso", "altura", "cidade", "estado", "descricao", "titulo", "tipo", "tipo_metrica", "exercicio",
    "valor_objetivo", "valor_partida", "data_final", "data_inicio", "data_fim", "recompensa_xp",
    "tempo_min", "distancia_km", "carga_kg", "repeticoes", "texto", "codigo", "aceito", "id_usuario",
    "tipo_conteudo", "rede_social", "id_atividade", "id_meta", "foto",
]


def data_para_idade(idade):
    hoje = date.today()
    try:
        return hoje.replace(year=hoje.year - idade).isoformat()
    except ValueError:
        return hoje.replace(year=hoje.year - idade, month=3, day=1).isoformat()


class TestEntradasInvalidas(BaseTeste):

    def setUp(self):
        super().setUp()
        ambiente = mock.patch.dict(os.environ, {"ADMIN_EMAILS": ADMIN})
        ambiente.start()
        self.addCleanup(ambiente.stop)
        self.usuario, self.token = self.criar_usuario_logado("Ana Varredura", idade=30)
        self.outro, self.token_outro = self.criar_usuario_logado("Bia Varredura", idade=31)
        self.admin, self.token_admin = self.criar_usuario_logado(
            "Admin Varredura", idade=40, email=ADMIN
        )
        self.ids = self.criar_objetos()
        self.contador = itertools.count()

    def criar_objetos(self):
        atividade = self.cli.post(
            f"/api/usuarios/{self.usuario['id']}/atividades",
            json={"tipo": "cardio", "titulo": "Corrida", "tempo_min": 20},
            headers=self.auth(self.token),
        )
        self.assertEqual(atividade.status_code, 201, atividade.get_data(as_text=True))
        meta = self.cli.post("/api/metas", json={
            "titulo": "Meta varredura", "tipo": "curto_prazo", "tipo_metrica": "carga_maxima",
            "exercicio": "supino", "valor_objetivo": 50, "data_final": "2031-01-01",
        }, headers=self.auth(self.token))
        self.assertEqual(meta.status_code, 201, meta.get_data(as_text=True))
        grupo = self.cli.post("/api/grupos", json={"nome": "Grupo varredura"}, headers=self.auth(self.token))
        self.assertEqual(grupo.status_code, 201, grupo.get_data(as_text=True))
        id_grupo = grupo.get_json()["grupo"]["id"]
        convite = self.cli.post(
            f"/api/grupos/{id_grupo}/convites", json={"id_usuario": self.outro["id"]},
            headers=self.auth(self.token),
        )
        self.assertEqual(convite.status_code, 201, convite.get_data(as_text=True))
        desafio = self.cli.post("/api/desafios", json={
            "nome": "Desafio varredura", "exercicio": "livre", "tipo_metrica": "treinos",
            "valor_objetivo": 5, "data_inicio": date.today().isoformat(),
            "data_fim": (date.today() + timedelta(days=10)).isoformat(), "recompensa_xp": 10,
        }, headers=self.auth(self.token_admin))
        self.assertEqual(desafio.status_code, 201, desafio.get_data(as_text=True))
        postagem = self.cli.post(
            "/api/postagens", data={"texto": "Post varredura"},
            headers=self.auth(self.token), content_type="multipart/form-data",
        )
        self.assertEqual(postagem.status_code, 201, postagem.get_data(as_text=True))
        dados_postagem = postagem.get_json()["postagem"]
        return {
            "id_usuario": self.usuario["id"],
            "outro": self.outro["id"],
            "id_grupo": id_grupo,
            "id_meta": meta.get_json()["meta"]["id"],
            "id_desafio": desafio.get_json()["id"] if "id" in desafio.get_json() else 1,
            "id_atividade": atividade.get_json()["atividade"]["id"],
            "id_postagem": dados_postagem.get("id") or dados_postagem.get("id_postagem"),
            "id_convite": convite.get_json()["id"],
        }

    def preencher(self, regra):
        i = self.ids
        mapa = {
            "id_usuario": i["id_usuario"], "id_grupo": i["id_grupo"], "id_meta": i["id_meta"],
            "id_desafio": i["id_desafio"], "id_atividade": i["id_atividade"], "id_postagem": i["id_postagem"],
            "id_convite": i["id_convite"], "id_comentario": 1, "id_notificacao": 1,
            "tipo_alvo": "atividade", "id_alvo": i["id_atividade"], "chave": "compartilhamento",
        }
        return re.sub(r"<(?:int:|path:)?(\w+)>", lambda m: str(mapa.get(m.group(1), 1)), regra)

    def base_do_corpo(self, metodo, regra):
        ana = self.ids["id_usuario"]
        atividade = self.ids["id_atividade"]
        chaves = {
            ("POST", "/api/usuarios"): {
                "nome": "Novo Varredura", "email": "novo.varredura@teste.com",
                "data_nascimento": data_para_idade(30), "senha": SENHA, "aceite_termos": True,
                "consentimentos": {},
            },
            ("POST", "/api/login"): {"email": "ana.varredura@teste.com", "senha": SENHA},
            ("PUT", "/api/usuarios/<int:id_usuario>"): {"nome": "Ana Varredura"},
            ("POST", "/api/usuarios/<int:id_usuario>/atividades"): {"tipo": "cardio", "titulo": "Corrida", "tempo_min": 20},
            ("POST", "/api/metas"): {
                "titulo": "Meta", "tipo": "curto_prazo", "tipo_metrica": "carga_maxima",
                "exercicio": "supino", "valor_objetivo": 50, "data_final": "2031-01-01",
            },
            ("PUT", "/api/metas/<int:id_meta>"): {"titulo": "Meta renomeada"},
            ("POST", "/api/grupos"): {"nome": "Grupo"},
            ("POST", "/api/grupos/entrar"): {"codigo": "ZZZZZZZZ"},
            ("PUT", "/api/convites/<int:id_convite>"): {"aceito": True},
            ("POST", "/api/desafios"): {
                "nome": "Desafio", "exercicio": "livre", "tipo_metrica": "treinos", "valor_objetivo": 5,
                "data_inicio": date.today().isoformat(),
                "data_fim": (date.today() + timedelta(days=10)).isoformat(), "recompensa_xp": 10,
            },
            ("PUT", "/api/desafios/<int:id_desafio>"): {"nome": "Desafio renomeado"},
            ("POST", "/api/compartilhamentos"): {"tipo_conteudo": "atividade", "rede_social": "whatsapp", "id_atividade": atividade},
            ("POST", "/api/feed/<tipo_alvo>/<int:id_alvo>/comentarios"): {"texto": "Oi"},
            ("PUT", "/api/usuarios/<int:id_usuario>/consentimentos/<chave>"): {"aceito": False},
            ("POST", "/api/grupos/<int:id_grupo>/convites"): {"id_usuario": self.ids["outro"]},
            ("PUT", "/api/desafios/<int:id_desafio>/encerrar"): {},
            ("POST", "/api/feed/<tipo_alvo>/<int:id_alvo>/curtir"): {},
        }
        return dict(chaves.get((metodo, regra), {}))

    def rotas_de_escrita(self):
        for regra in self.app.url_map.iter_rules():
            if not regra.rule.startswith("/api/"):
                continue
            for metodo in sorted(regra.methods & {"POST", "PUT"}):
                yield metodo, regra.rule

    def token_para(self, regra):
        if regra.startswith("/api/desafios"):
            return self.token_admin
        if regra.startswith("/api/convites/"):
            return self.token_outro
        return self.token

    def respostas_de_escrita(self):
        for metodo, regra in self.rotas_de_escrita():
            caminho = self.preencher(regra)
            token = self.token_para(regra)
            base = self.base_do_corpo(metodo, regra)
            if "/postagens" in regra:
                for valor in VALORES:
                    if valor is None:
                        continue
                    dados = {"texto": valor if isinstance(valor, str) else str(valor)}
                    yield (metodo, regra, "form", repr(valor)[:30], self.cli.open(
                        caminho, method=metodo, data=dados, headers=self.auth(token),
                        content_type="multipart/form-data",
                    ))
                continue
            for campo in CAMPOS:
                for valor in VALORES:
                    corpo = dict(base)
                    if (metodo, regra) == ("POST", "/api/usuarios") and campo != "email":
                        corpo["email"] = f"novo{next(self.contador)}@teste.com"
                    corpo[campo] = valor
                    yield (metodo, regra, campo, repr(valor)[:30], self.cli.open(
                        caminho, method=metodo, json=corpo, headers=self.auth(token),
                    ))
            for valor in CORPOS_NAO_OBJETO:
                yield (metodo, regra, "corpo", repr(valor)[:30], self.cli.open(
                    caminho, method=metodo, data=json.dumps(valor), headers=self.auth(token),
                    content_type="application/json",
                ))

    def test_corpo_que_nao_e_objeto_recebe_400(self):
        for metodo, caminho in (
            ("POST", "/api/login"),
            ("POST", "/api/usuarios"),
            ("POST", "/api/metas"),
            ("PUT", f"/api/usuarios/{self.usuario['id']}"),
            ("POST", f"/api/usuarios/{self.usuario['id']}/atividades"),
        ):
            for valor in CORPOS_NAO_OBJETO:
                with self.subTest(metodo=metodo, caminho=caminho, corpo=valor):
                    resposta = self.cli.open(
                        caminho, method=metodo, data=json.dumps(valor),
                        headers=self.auth(self.token), content_type="application/json",
                    )
                    self.assertEqual(resposta.status_code, 400)

    def test_responsavel_de_menor_em_formato_invalido_recebe_400(self):
        for indice, responsavel in enumerate((123, [], "texto")):
            with self.subTest(responsavel=responsavel):
                resposta = self.cli.post("/api/usuarios", json={
                    "nome": "Menor Formato", "email": f"formato{indice}@teste.com",
                    "data_nascimento": data_para_idade(15), "senha": SENHA, "aceite_termos": True,
                    "consentimentos": {}, "responsavel": responsavel, "autorizacao_responsavel": True,
                })
                self.assertEqual(resposta.status_code, 400)

    def test_data_de_nascimento_vazia_no_perfil_recebe_400(self):
        for valor in ("", [], {}):
            with self.subTest(valor=valor):
                resposta = self.cli.put(
                    f"/api/usuarios/{self.usuario['id']}", json={"data_nascimento": valor},
                    headers=self.auth(self.token),
                )
                self.assertEqual(resposta.status_code, 400)

    def test_nenhuma_rota_de_escrita_responde_500_com_entrada_invalida(self):
        falhas = []
        for metodo, regra, campo, valor, resposta in self.respostas_de_escrita():
            if resposta.status_code >= 500:
                falhas.append(f"{metodo} {regra} [{campo}={valor}] -> {resposta.status_code}")
        self.assertEqual(falhas, [], "\n".join(falhas[:40]))


if __name__ == "__main__":
    unittest.main()
