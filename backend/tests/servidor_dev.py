import os
import sys
from datetime import date, timedelta

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)

CAMINHO_BANCO = os.path.join(RAIZ, "dev.db").replace("\\", "/")
os.environ.setdefault("DB_URI", "sqlite:///" + CAMINHO_BANCO)

from app import criar_app
from database import db
from models.model import Atividade, Desafio, DesafioUsuario, Notificacao, Usuario
from services import (
    AlternarCurtidaService,
    CadastrarUsuarioService,
    CriarComentarioService,
    CriarGrupoService,
    CriarMetaService,
    EntrarGrupoPorCodigoService,
)
from services.atividade.apoio import calcular_pontuacao, nivel_por_xp
from tests.apoio import CONSENTIMENTOS_OPCIONAIS_ACEITOS, criar_views_de_ranking
from utils import agora, inicio_utc_do_dia_local

SENHA = "senhaforte123"
PRINCIPAL = "helena@fitbattle.dev"

USUARIOS = [
    ("Helena Duarte", PRINCIPAL, 29, "Belo Horizonte", "MG"),
    ("Lucas Ferreira", "lucas@fitbattle.dev", 26, "Belo Horizonte", "MG"),
    ("Marina Alves", "marina@fitbattle.dev", 24, "Belo Horizonte", "MG"),
    ("Bruno Teixeira", "bruno@fitbattle.dev", 31, "Belo Horizonte", "MG"),
    ("Carolina Pires", "carolina@fitbattle.dev", 27, "Belo Horizonte", "MG"),
    ("Diego Moreira", "diego@fitbattle.dev", 33, "Contagem", "MG"),
    ("Juliana Rocha", "juliana@fitbattle.dev", 35, "Belo Horizonte", "MG"),
    ("Rafael Nunes", "rafael@fitbattle.dev", 30, "Belo Horizonte", "MG"),
    ("Fernanda Lima", "fernanda@fitbattle.dev", 25, "Nova Lima", "MG"),
    ("Thiago Barros", "thiago@fitbattle.dev", 28, "Belo Horizonte", "MG"),
    ("Beatriz Correia", "beatriz@fitbattle.dev", 26, "Belo Horizonte", "MG"),
    ("Gustavo Melo", "gustavo@fitbattle.dev", 40, "Betim", "MG"),
]

TEXTOS_TREINO = {
    "Supino reto": "Supino reto com pausa de um segundo no peito. Última série até a falha técnica.",
    "Agachamento livre": "Agachamento livre com coluna neutra e descida até a linha do joelho.",
    "Levantamento terra": "Levantamento terra em séries pesadas, com foco em postura e pegada firme.",
    "Costas e bíceps": "Remada e puxada com foco em costas e bíceps. Descanso de 90 segundos entre as séries.",
    "Peito e tríceps": "Peito e tríceps mantendo a amplitude completa em todas as repetições.",
    "Pernas": "Agachamento, leg press e cadeira extensora. Reduzi a carga no último bloco.",
    "Ombros e abdômen": "Ombro e abdômen com execução lenta, sem balanço.",
    "Full body": "Corpo inteiro com carga moderada, todos os grupos musculares na mesma sessão.",
    "Corrida no parque": "Corrida leve no parque, ritmo constante e respiração controlada.",
    "Bike ergométrica": "Intervalado na bike: um minuto forte e um minuto leve, repetidos.",
    "Esteira intervalada": "Esteira em ritmo de tempo: aquecimento de 10 minutos e bloco forte no meio.",
    "Caminhada rápida": "Caminhada rápida na hora do almoço, 40 minutos.",
    "Yoga de recuperação": "Yoga de recuperação depois do treino pesado. Alongamento de quadril e costas.",
}

HELENA_SESSOES = [
    "Supino reto", "Corrida no parque", "Agachamento livre", "Costas e bíceps", "Supino reto",
    "Yoga de recuperação", "Levantamento terra", "Supino reto", "Bike ergométrica", "Agachamento livre",
    "Peito e tríceps", "Supino reto", "Caminhada rápida", "Costas e bíceps", "Agachamento livre",
    "Supino reto", "Esteira intervalada", "Levantamento terra", "Supino reto",
]
HELENA_TREINOS_POR_SEMANA = [2, 3, 1, 4, 2, 3, 1, 3]
HELENA_CARGA_INICIAL = {
    "Supino reto": (70, 2.5),
    "Agachamento livre": (60, 5),
    "Levantamento terra": (80, 2.5),
    "Costas e bíceps": (40, 2.5),
    "Peito e tríceps": (30, 2.5),
}
CARDIO_HELENA = ("Corrida no parque", "Bike ergométrica", "Esteira intervalada", "Caminhada rápida")

CATALOGO_OUTROS = [
    ("musculacao", "Pernas"),
    ("cardio", "Corrida no parque"),
    ("musculacao", "Ombros e abdômen"),
    ("yoga", "Yoga de recuperação"),
    ("musculacao", "Full body"),
    ("cardio", "Caminhada rápida"),
    ("musculacao", "Peito e tríceps"),
    ("cardio", "Esteira intervalada"),
    ("musculacao", "Costas e bíceps"),
    ("cardio", "Bike ergométrica"),
]

POSICOES_SEMANA = {1: [2], 2: [1, 4], 3: [0, 2, 4], 4: [0, 2, 4, 6]}
HORAS_DO_DIA = [18, 7, 12, 21]

VOLUME_OUTROS = {
    1: (20, 0.96),
    2: (18, 0.96),
    3: (17, 0.87),
    4: (15, 0.82),
    5: (13, 0.8),
    6: (11, 0.78),
    7: (10, 0.65),
    8: (9, 0.52),
    9: (8, 0.45),
    10: (8, 0.32),
    11: (8, 0.24),
}


def contagens_semanais(total, indice):
    contagens = [1] * 8
    posicao = indice
    extras = total - 8
    while extras > 0:
        if contagens[posicao % 8] < 4:
            contagens[posicao % 8] += 1
            extras -= 1
        posicao += 3
    return contagens


def momentos_da_semana(hoje, semanas_atras, quantidade):
    if semanas_atras == 0:
        dias = [hoje.weekday() - min(indice, hoje.weekday()) for indice in range(quantidade)]
    else:
        base = hoje.weekday() + 7 * semanas_atras
        dias = [base - posicao for posicao in POSICOES_SEMANA[quantidade]]
    vezes_no_dia = {}
    momentos = []
    for dia in dias:
        ordem = vezes_no_dia.get(dia, 0)
        vezes_no_dia[dia] = ordem + 1
        momentos.append((dia, HORAS_DO_DIA[ordem % len(HORAS_DO_DIA)]))
    return momentos


def treino_helena(exercicio, indice_carga, dias_atras):
    if exercicio in HELENA_CARGA_INICIAL:
        inicial, passo = HELENA_CARGA_INICIAL[exercicio]
        return {
            "tipo": "musculacao", "titulo": exercicio, "descricao": TEXTOS_TREINO[exercicio],
            "tempo_min": 50, "carga_kg": round(inicial + passo * indice_carga, 1), "repeticoes": 8,
            "dias_atras": dias_atras,
        }
    if exercicio in CARDIO_HELENA:
        return {
            "tipo": "cardio", "titulo": exercicio, "descricao": TEXTOS_TREINO[exercicio],
            "tempo_min": 35, "distancia_km": 4.0 + (indice_carga % 3) * 0.5, "dias_atras": dias_atras,
        }
    return {
        "tipo": "yoga", "titulo": exercicio, "descricao": TEXTOS_TREINO[exercicio],
        "tempo_min": 40, "dias_atras": dias_atras,
    }


def treino_de_outro(i, g, dias_atras, fator):
    tipo, titulo = CATALOGO_OUTROS[(i * 4 + g) % len(CATALOGO_OUTROS)]
    descricao = TEXTOS_TREINO[titulo]
    if tipo == "musculacao":
        return {
            "tipo": tipo, "titulo": titulo, "descricao": descricao,
            "tempo_min": max(5, round((40 + (g % 3) * 5) * fator)),
            "carga_kg": round((30 + ((i + g) % 6) * 5 + (g // 4) * 2.5) * fator, 1),
            "repeticoes": 8 + g % 3, "dias_atras": dias_atras,
        }
    if tipo == "cardio":
        return {
            "tipo": tipo, "titulo": titulo, "descricao": descricao,
            "tempo_min": max(5, round((25 + (g % 3) * 5) * fator)),
            "distancia_km": round((2.5 + (g % 4) * 0.5) * fator, 1),
            "dias_atras": dias_atras,
        }
    return {
        "tipo": tipo, "titulo": titulo, "descricao": descricao,
        "tempo_min": max(5, round((35 + (g % 2) * 10) * fator)), "dias_atras": dias_atras,
    }


def planos_de_treino(hoje):
    planos = {}

    momentos = []
    for semanas_atras in range(7, -1, -1):
        quantidade = HELENA_TREINOS_POR_SEMANA[7 - semanas_atras]
        momentos.extend(momentos_da_semana(hoje, semanas_atras, quantidade))
    momentos.sort(key=lambda momento: (-momento[0], momento[1]))
    assert len(momentos) == len(HELENA_SESSOES)

    contagem_carga = {}
    treinos_helena = []
    for exercicio, (dias, hora) in zip(HELENA_SESSOES, momentos):
        indice = contagem_carga.get(exercicio, 0)
        contagem_carga[exercicio] = indice + 1
        treino = treino_helena(exercicio, indice, dias)
        treino["hora"] = hora
        treinos_helena.append(treino)
    planos[PRINCIPAL] = treinos_helena

    for i, (_, email, _, _, _) in enumerate(USUARIOS[1:], start=1):
        total, fator = VOLUME_OUTROS[i]
        contagens = contagens_semanais(total, i)
        treinos = []
        g = 0
        for semanas_atras in range(7, -1, -1):
            for dias, hora in momentos_da_semana(hoje, semanas_atras, contagens[7 - semanas_atras]):
                treino = treino_de_outro(i, g, dias, fator)
                treino["hora"] = hora
                treinos.append(treino)
                g += 1
        planos[email] = treinos
    return planos


def registrar_treinos_historicos(ids, hoje):
    primeira = None
    for email, treinos in planos_de_treino(hoje).items():
        uid = ids[email]
        xp = 0
        for treino in treinos:
            dias_atras = treino.pop("dias_atras")
            hora = treino.pop("hora")
            dados = dict(treino)
            dados["pontuacao"] = calcular_pontuacao(dados)
            atividade = Atividade(id_usuario=uid, **dados).salvar()
            atividade.data_registro = inicio_utc_do_dia_local(hoje - timedelta(days=dias_atras)) + timedelta(hours=hora)
            db.session.commit()
            xp += atividade.pontuacao
            primeira = primeira or atividade.id_atividade
        usuario = Usuario.buscar_por_id(uid)
        usuario.xp = xp
        usuario.nivel = nivel_por_xp(xp)
        usuario.salvar()
    return primeira


def espalhar_notificacoes():
    momento = agora()
    notificacoes = Notificacao.query.order_by(Notificacao.id_notif).all()
    for indice, notificacao in enumerate(notificacoes):
        notificacao.data_envio = momento - timedelta(hours=1 + (indice * 7) % 30 + (indice // 3) * 9)
    db.session.commit()


def data_nascimento_para_idade(idade):
    hoje = date.today()
    try:
        nascimento = hoje.replace(year=hoje.year - idade)
    except ValueError:
        nascimento = hoje.replace(year=hoje.year - idade, month=3, day=1)
    return nascimento.isoformat()


def popular(hoje=None):
    if Usuario.query.count() > 0:
        return
    hoje = hoje or date.today()
    ids = {}
    for nome, email, idade, cidade, estado in USUARIOS:
        usuario = CadastrarUsuarioService.executar({
            "nome": nome, "email": email,
            "data_nascimento": data_nascimento_para_idade(idade), "senha": SENHA,
            "aceite_termos": True, "consentimentos": CONSENTIMENTOS_OPCIONAIS_ACEITOS,
        })
        usuario.cidade = cidade
        usuario.estado = estado
        db.session.commit()
        ids[email] = usuario.id_usuario

    primeira = registrar_treinos_historicos(ids, hoje)

    CriarComentarioService.executar(ids["carolina@fitbattle.dev"], "atividade", primeira, "Mandou bem demais!")
    CriarComentarioService.executar(ids["lucas@fitbattle.dev"], "atividade", primeira, "Bora pra cima!")
    AlternarCurtidaService.executar(ids["lucas@fitbattle.dev"], "atividade", primeira)
    AlternarCurtidaService.executar(ids["diego@fitbattle.dev"], "atividade", primeira)

    grupo = CriarGrupoService.executar(ids[PRINCIPAL], {
        "nome": "Turma do Parque", "descricao": "Grupo para treinar junto e acompanhar a evolução.",
    })
    EntrarGrupoPorCodigoService.executar(ids["lucas@fitbattle.dev"], grupo.codigo_convite)
    CriarMetaService.executar(ids[PRINCIPAL], {
        "titulo": "Supino 120 kg", "tipo": "curto_prazo", "tipo_metrica": "carga_maxima",
        "exercicio": "supino reto", "valor_objetivo": 120, "data_final": "2030-12-31",
    })

    inicio_semana = hoje - timedelta(days=hoje.weekday())
    desafio = Desafio(**{
        "nome": "Desafio: 5 treinos em 7 dias",
        "descricao": "Registre 5 treinos em um período de 7 dias para ganhar 100 XP de bônus.",
        "exercicio": "livre",
        "tipo_metrica": "treinos",
        "valor_objetivo": 5,
        "data_inicio": inicio_semana,
        "data_fim": inicio_semana + timedelta(days=6),
        "recompensa_xp": 100,
    }).salvar()
    DesafioUsuario(id_desafio=desafio.id_desafio, id_usuario=ids[PRINCIPAL], status="inscrito").salvar()
    espalhar_notificacoes()


def preparar():
    app = criar_app()
    with app.app_context():
        criar_views_de_ranking(db)
        popular()
    return app


if __name__ == "__main__":
    preparar().run(
        host=os.environ.get("HOST", "127.0.0.1"),
        port=int(os.environ.get("PORT", "5000")),
        debug=False,
    )
