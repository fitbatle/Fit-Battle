import unittest
from datetime import date

from database import db
from models.model import (
    Atividade,
    Comentario,
    Compartilhamento,
    Consentimento,
    Convite,
    Curtida,
    Desafio,
    DesafioUsuario,
    Grupo,
    GrupoMembro,
    Meta,
    Notificacao,
    Postagem,
    Usuario,
)
from tests.test_seguranca import BaseTeste
from utils import ConflitoDeDados

FABRICAS = {
    Usuario: (
        lambda uid: {"nome": "Modelo Teste", "email": "modelo.teste@exemplo.com", "senha": "hash"},
        {"nome": "Nome Alterado"},
    ),
    Atividade: (
        lambda uid: {"id_usuario": uid, "tipo": "cardio", "tempo_min": 30, "pontuacao": 50},
        {"titulo": "Corrida"},
    ),
    Postagem: (
        lambda uid: {"id_usuario": uid, "texto": "Primeira postagem"},
        {"texto": "Postagem editada"},
    ),
    Curtida: (
        lambda uid: {"id_usuario": uid, "tipo_alvo": "atividade", "id_alvo": 1},
        {"id_alvo": 2},
    ),
    Comentario: (
        lambda uid: {"id_usuario": uid, "tipo_alvo": "atividade", "id_alvo": 1, "texto": "Bom treino"},
        {"texto": "Ótimo treino"},
    ),
    Grupo: (
        lambda uid: {"nome": "Turma Teste", "id_criador": uid},
        {"nome": "Turma Renomeada"},
    ),
    GrupoMembro: (
        lambda uid: {"id_grupo": 1, "id_usuario": uid},
        {"papel": "admin"},
    ),
    Convite: (
        lambda uid: {"id_grupo": 1, "id_remetente": uid, "id_destinatario": uid},
        {"status": "aceito"},
    ),
    Meta: (
        lambda uid: {
            "id_usuario": uid,
            "descricao": "Correr",
            "tipo_metrica": "treinos",
            "valor_objetivo": 5,
            "data_inicio": date(2026, 1, 1),
        },
        {"descricao": "Correr mais"},
    ),
    Notificacao: (
        lambda uid: {"id_usuario": uid, "tipo": "teste", "mensagem": "Olá"},
        {"lida": True},
    ),
    Desafio: (
        lambda uid: {"nome": "Desafio Teste", "data_inicio": date(2026, 1, 1), "data_fim": date(2026, 2, 1)},
        {"nome": "Desafio Renomeado"},
    ),
    DesafioUsuario: (
        lambda uid: {"id_desafio": 1, "id_usuario": uid},
        {"status": "concluido"},
    ),
    Compartilhamento: (
        lambda uid: {"id_usuario": uid, "tipo_conteudo": "recorde"},
        {"rede_social": "whatsapp"},
    ),
    Consentimento: (
        lambda uid: {"id_usuario": uid, "chave": "teste", "descricao": "Teste"},
        {"aceito": False},
    ),
}


def chave_de(modelo, objeto):
    valores = tuple(getattr(objeto, coluna.key) for coluna in modelo.__mapper__.primary_key)
    return valores[0] if len(valores) == 1 else valores


def chave_inexistente(modelo):
    tamanho = len(modelo.__mapper__.primary_key)
    return 999999 if tamanho == 1 else tuple([999999] * tamanho)


class TestModeloBase(BaseTeste):

    def setUp(self):
        super().setUp()
        self.contexto = self.app.app_context()
        self.contexto.push()
        base = Usuario(nome="Base", email="base@exemplo.com", senha="hash")
        base.salvar()
        self.uid = base.id_usuario

    def tearDown(self):
        db.session.remove()
        self.contexto.pop()
        super().tearDown()

    def criar(self, modelo):
        return modelo(**FABRICAS[modelo][0](self.uid)).salvar()

    def test_todas_as_models_herdam_da_classe_base(self):
        from models.base import ModeloBase

        self.assertEqual(len(FABRICAS), 14)
        for modelo in FABRICAS:
            with self.subTest(modelo=modelo.__name__):
                self.assertTrue(issubclass(modelo, ModeloBase))
                self.assertTrue(issubclass(modelo, db.Model))

    def test_salvar_persiste_o_registro(self):
        for modelo in FABRICAS:
            with self.subTest(modelo=modelo.__name__):
                objeto = self.criar(modelo)
                self.assertIsNotNone(modelo.buscar_por_id(chave_de(modelo, objeto)))

    def test_buscar_por_id_devolve_none_quando_nao_existe(self):
        for modelo in FABRICAS:
            with self.subTest(modelo=modelo.__name__):
                self.assertIsNone(modelo.buscar_por_id(chave_inexistente(modelo)))

    def test_buscar_por_id_encontra_o_registro_salvo(self):
        for modelo in FABRICAS:
            with self.subTest(modelo=modelo.__name__):
                objeto = self.criar(modelo)
                encontrado = modelo.buscar_por_id(chave_de(modelo, objeto))
                self.assertEqual(chave_de(modelo, encontrado), chave_de(modelo, objeto))

    def test_listar_todos_inclui_o_registro_salvo(self):
        for modelo in FABRICAS:
            with self.subTest(modelo=modelo.__name__):
                objeto = self.criar(modelo)
                chaves = [chave_de(modelo, item) for item in modelo.listar_todos()]
                self.assertIn(chave_de(modelo, objeto), chaves)

    def test_atualizar_altera_so_campos_existentes_e_preserva_a_chave(self):
        for modelo, (_, alteracao) in FABRICAS.items():
            with self.subTest(modelo=modelo.__name__):
                objeto = self.criar(modelo)
                chave = chave_de(modelo, objeto)
                chaves_primarias = {coluna.key: 999 for coluna in modelo.__mapper__.primary_key}
                campos = {**alteracao, **chaves_primarias, "campo_inexistente": 1}
                objeto.atualizar(campos)
                db.session.expire_all()
                recarregado = modelo.buscar_por_id(chave)
                nome, valor = next(iter(alteracao.items()))
                self.assertEqual(getattr(recarregado, nome), valor)
                self.assertEqual(chave_de(modelo, recarregado), chave)
                self.assertNotIn("campo_inexistente", recarregado.__dict__)

    def test_deletar_remove_o_registro(self):
        for modelo in FABRICAS:
            with self.subTest(modelo=modelo.__name__):
                objeto = self.criar(modelo)
                chave = chave_de(modelo, objeto)
                objeto.deletar()
                self.assertIsNone(modelo.buscar_por_id(chave))

    def test_erro_de_banco_faz_rollback_e_relanca(self):
        postagem_sem_texto = Postagem(id_usuario=self.uid)
        with self.assertRaises(ConflitoDeDados):
            postagem_sem_texto.salvar()
        self.assertIsNotNone(Usuario.buscar_por_id(self.uid))
        self.assertEqual(Postagem.listar_todos(), [])
