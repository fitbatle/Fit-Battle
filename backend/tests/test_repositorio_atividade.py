from datetime import date, datetime, timedelta

from models.model import Atividade, Usuario
from repositories.repository import AtividadeRepository
from tests.test_seguranca import BaseTeste


def criar_usuario(email, perfil_publico=True, data_nascimento=None, idade=30):
    return Usuario(
        nome=email.split("@")[0], email=email, senha="hash", idade=idade,
        data_nascimento=data_nascimento, perfil_publico=perfil_publico,
    ).salvar()


def registrar(id_usuario, quando, tipo="musculacao", titulo="Supino Reto", carga=None,
              distancia=None, tempo=30, pontuacao=40, repeticoes=None):
    return Atividade(
        id_usuario=id_usuario, tipo=tipo, titulo=titulo, tempo_min=tempo,
        distancia_km=distancia, carga_kg=carga, repeticoes=repeticoes,
        pontuacao=pontuacao, data_registro=quando,
    ).salvar()


ONTEM = datetime(2026, 1, 10, 12, 0)
ANTES = datetime(2026, 1, 5, 12, 0)
HOJE = datetime(2026, 1, 20, 12, 0)


class TestAtividadeRepositoryListagens(BaseTeste):

    def test_listar_do_usuario_do_mais_recente_para_o_mais_antigo(self):
        with self.app.app_context():
            dono = criar_usuario("lista.dono@repo.teste")
            registrar(dono.id_usuario, ANTES, titulo="Antigo")
            registrar(dono.id_usuario, HOJE, titulo="Recente")
            titulos = [a["titulo"] for a in AtividadeRepository.listar_do_usuario(dono.id_usuario)]
        self.assertEqual(titulos, ["Recente", "Antigo"])

    def test_listar_do_usuario_devolve_dict_com_tipos_normalizados(self):
        with self.app.app_context():
            dono = criar_usuario("tipos.atv@repo.teste")
            registrar(dono.id_usuario, HOJE, distancia=5.5, carga=80, repeticoes=8)
            linha = AtividadeRepository.listar_do_usuario(dono.id_usuario)[0]
        self.assertIsInstance(linha, dict)
        self.assertEqual(linha["distancia_km"], 5.5)
        self.assertIsInstance(linha["distancia_km"], float)
        self.assertIsInstance(linha["data_registro"], datetime)
        self.assertIsNone(linha["data_registro"].tzinfo)

    def test_listar_publicas_esconde_perfil_privado_e_menor_de_idade(self):
        with self.app.app_context():
            publico = criar_usuario("publica.atv@repo.teste")
            privado = criar_usuario("privada.atv@repo.teste", perfil_publico=False)
            menor = criar_usuario(
                "menor.atv@repo.teste",
                data_nascimento=date.today().replace(year=date.today().year - 15),
            )
            registrar(publico.id_usuario, HOJE, titulo="Publica")
            registrar(privado.id_usuario, HOJE, titulo="Privada")
            registrar(menor.id_usuario, HOJE, titulo="Menor")
            titulos = {a["titulo"] for a in AtividadeRepository.listar_publicas(50)}
        self.assertIn("Publica", titulos)
        self.assertNotIn("Privada", titulos)
        self.assertNotIn("Menor", titulos)

    def test_listar_publicas_mostra_o_proprio_menor_para_o_dono(self):
        with self.app.app_context():
            menor = criar_usuario(
                "menor.dono@repo.teste",
                data_nascimento=date.today().replace(year=date.today().year - 15),
            )
            registrar(menor.id_usuario, HOJE, titulo="Meu Treino Menor")
            titulos = {a["titulo"] for a in AtividadeRepository.listar_publicas(50, menor.id_usuario)}
        self.assertIn("Meu Treino Menor", titulos)

    def test_listar_publicas_respeita_o_limite(self):
        with self.app.app_context():
            dono = criar_usuario("limite.atv@repo.teste")
            for i in range(4):
                registrar(dono.id_usuario, HOJE + timedelta(minutes=i), titulo=f"Limite {i}")
            self.assertEqual(len(AtividadeRepository.listar_publicas(2)), 2)


class TestAtividadeRepositoryAgregados(BaseTeste):

    def test_maior_carga_usa_titulo_sem_diferenca_de_caixa(self):
        with self.app.app_context():
            dono = criar_usuario("carga.atv@repo.teste")
            registrar(dono.id_usuario, ONTEM, titulo="Supino Reto", carga=60)
            registrar(dono.id_usuario, HOJE, titulo="SUPINO RETO", carga=75)
            maior = AtividadeRepository.maior_carga(dono.id_usuario, "supino reto")["maior_carga"]
        self.assertEqual(maior, 75.0)
        self.assertIsInstance(maior, float)

    def test_maior_carga_sem_registros_devolve_none(self):
        with self.app.app_context():
            dono = criar_usuario("sem.carga@repo.teste")
            self.assertIsNone(AtividadeRepository.maior_carga(dono.id_usuario, "nada")["maior_carga"])

    def test_contar_desde_conta_so_a_partir_da_data(self):
        with self.app.app_context():
            dono = criar_usuario("desde.atv@repo.teste")
            registrar(dono.id_usuario, ANTES)
            registrar(dono.id_usuario, HOJE)
            total = AtividadeRepository.contar_desde(dono.id_usuario, ONTEM)["total"]
        self.assertEqual(total, 1)

    def test_contar_no_periodo_com_e_sem_titulo(self):
        with self.app.app_context():
            dono = criar_usuario("periodo.atv@repo.teste")
            registrar(dono.id_usuario, ONTEM, titulo="Corrida")
            registrar(dono.id_usuario, ONTEM, titulo="Remada")
            registrar(dono.id_usuario, HOJE, titulo="Corrida")
            fora = datetime(2026, 2, 1)
            total = AtividadeRepository.contar_no_periodo(dono.id_usuario, datetime(2026, 1, 1), fora)["total"]
            so_corrida = AtividadeRepository.contar_no_periodo(
                dono.id_usuario, datetime(2026, 1, 1), fora, "corrida"
            )["total"]
        self.assertEqual(total, 3)
        self.assertEqual(so_corrida, 2)

    def test_maior_carga_no_periodo_respeita_a_janela(self):
        with self.app.app_context():
            dono = criar_usuario("janela.atv@repo.teste")
            registrar(dono.id_usuario, ANTES, titulo="Leg Press", carga=200)
            registrar(dono.id_usuario, ONTEM, titulo="Leg Press", carga=120)
            maior = AtividadeRepository.maior_carga_no_periodo(
                dono.id_usuario, datetime(2026, 1, 8), datetime(2026, 1, 31), "leg press"
            )["maior_carga"]
        self.assertEqual(maior, 120.0)

    def test_listar_do_usuario_por_titulo_so_musculacao_em_ordem_crescente(self):
        with self.app.app_context():
            dono = criar_usuario("titulo.atv@repo.teste")
            registrar(dono.id_usuario, HOJE, titulo="Agachamento", carga=90)
            registrar(dono.id_usuario, ANTES, titulo="Agachamento", carga=80)
            registrar(dono.id_usuario, ONTEM, titulo="Agachamento", tipo="cardio", carga=None)
            cargas = [a["carga_kg"] for a in AtividadeRepository.listar_do_usuario_por_titulo(
                dono.id_usuario, "agachamento"
            )]
        self.assertEqual(cargas, [80.0, 90.0])

    def test_pontuacao_total_desde_soma_e_zera_sem_registros(self):
        with self.app.app_context():
            dono = criar_usuario("pontos.atv@repo.teste")
            outro = criar_usuario("pontos.outro@repo.teste")
            registrar(dono.id_usuario, HOJE, pontuacao=30)
            registrar(dono.id_usuario, HOJE, pontuacao=20)
            registrar(outro.id_usuario, HOJE, pontuacao=999)
            total = AtividadeRepository.pontuacao_total_desde(dono.id_usuario, ONTEM)["total"]
            zero = AtividadeRepository.pontuacao_total_desde(outro.id_usuario, datetime(2030, 1, 1))["total"]
        self.assertEqual(total, 50)
        self.assertEqual(zero, 0)

    def test_pontuacoes_desde_traz_data_e_pontuacao(self):
        with self.app.app_context():
            dono = criar_usuario("pontuacoes.atv@repo.teste")
            registrar(dono.id_usuario, HOJE, pontuacao=45)
            linhas = AtividadeRepository.pontuacoes_desde(dono.id_usuario, ONTEM)
        self.assertEqual([(l["data_registro"], l["pontuacao"]) for l in linhas], [(HOJE, 45)])

    def test_distribuicao_por_tipo_conta_cada_tipo(self):
        with self.app.app_context():
            dono = criar_usuario("tipos.dist@repo.teste")
            registrar(dono.id_usuario, HOJE, tipo="musculacao")
            registrar(dono.id_usuario, HOJE, tipo="musculacao")
            registrar(dono.id_usuario, HOJE, tipo="yoga", titulo="Yoga")
            distribuicao = AtividadeRepository.distribuicao_por_tipo(dono.id_usuario)
        self.assertEqual(distribuicao, {"musculacao": 2, "yoga": 1})

    def test_datas_registro_traz_uma_linha_por_treino(self):
        with self.app.app_context():
            dono = criar_usuario("datas.atv@repo.teste")
            registrar(dono.id_usuario, ANTES)
            registrar(dono.id_usuario, HOJE)
            datas = sorted(l["data_registro"] for l in AtividadeRepository.datas_registro(dono.id_usuario))
        self.assertEqual(datas, [ANTES, HOJE])

    def test_totais_conta_treinos_e_soma_tempo(self):
        with self.app.app_context():
            dono = criar_usuario("totais.atv@repo.teste")
            registrar(dono.id_usuario, HOJE, tempo=20)
            registrar(dono.id_usuario, HOJE, tempo=35)
            totais = AtividadeRepository.totais(dono.id_usuario)
        self.assertEqual(totais, {"treinos": 2, "tempo_min": 55})

    def test_titulos_distintos_ignora_cardio_sem_carga_e_vem_ordenado(self):
        with self.app.app_context():
            dono = criar_usuario("titulos.atv@repo.teste")
            registrar(dono.id_usuario, HOJE, titulo="Supino", carga=50)
            registrar(dono.id_usuario, HOJE, titulo="Supino", carga=55)
            registrar(dono.id_usuario, HOJE, titulo="Agachamento", carga=70)
            registrar(dono.id_usuario, HOJE, titulo="Esteira", tipo="cardio", carga=None)
            titulos = [l["titulo"] for l in AtividadeRepository.titulos_distintos(dono.id_usuario)]
        self.assertEqual(titulos, ["Agachamento", "Supino"])
