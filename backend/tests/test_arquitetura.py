import ast
import os
import re
import tempfile
import unittest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

ARQUIVOS_ISENTOS_DA_REGRA_DE_CASO_DE_USO = {"__init__.py", "apoio.py", "limitador_login.py"}

ARQUIVOS_SOLTOS_PERMITIDOS_NA_RAIZ_DE_SERVICES = {"__init__.py", "comum.py"}


def _nomes_importados(caminho):
    with open(caminho, "r", encoding="utf-8") as arquivo:
        arvore = ast.parse(arquivo.read(), filename=caminho)
    nomes = []
    for nodo in ast.walk(arvore):
        if isinstance(nodo, ast.Import):
            nomes.extend(alias.name for alias in nodo.names)
        elif isinstance(nodo, ast.ImportFrom) and nodo.module:
            nomes.append(nodo.module)
    return nomes


def _arquivos_py_do_backend():
    arquivos = []
    for raiz, pastas, nomes in os.walk(RAIZ):
        pastas[:] = [p for p in pastas if p != "__pycache__"]
        for nome in nomes:
            if nome.endswith(".py"):
                arquivos.append(os.path.join(raiz, nome))
    return sorted(arquivos)


def _usa_db_session(caminho):
    with open(caminho, "r", encoding="utf-8") as arquivo:
        arvore = ast.parse(arquivo.read(), filename=caminho)
    for nodo in ast.walk(arvore):
        if (
            isinstance(nodo, ast.Attribute)
            and nodo.attr == "session"
            and isinstance(nodo.value, ast.Name)
            and nodo.value.id == "db"
        ):
            return True
    return False


def _arquivos_py(pasta):
    caminho_pasta = os.path.join(RAIZ, pasta)
    arquivos = []
    for raiz, pastas, nomes in os.walk(caminho_pasta):
        pastas[:] = [p for p in pastas if p != "__pycache__"]
        for nome in nomes:
            if nome.endswith(".py"):
                arquivos.append(os.path.join(raiz, nome))
    return sorted(arquivos)


def _comeca_com(nome, prefixos):
    return any(nome == prefixo or nome.startswith(prefixo + ".") for prefixo in prefixos)


def _pastas_de_area(caminho_services):
    return sorted(
        nome
        for nome in os.listdir(caminho_services)
        if nome != "__pycache__" and os.path.isdir(os.path.join(caminho_services, nome))
    )


def _areas_com_pacote(caminho_services):
    return {
        nome
        for nome in _pastas_de_area(caminho_services)
        if os.path.isfile(os.path.join(caminho_services, nome, "__init__.py"))
    }


def _caminho_relativo_a_services(caminho, caminho_services):
    return os.path.relpath(caminho, caminho_services).replace(os.sep, "/")


def _verificar_raiz_de_services_so_tem_arquivos_permitidos(caminho_services):
    permitidos = ARQUIVOS_SOLTOS_PERMITIDOS_NA_RAIZ_DE_SERVICES
    soltos = sorted(
        nome
        for nome in os.listdir(caminho_services)
        if nome.endswith(".py") and os.path.isfile(os.path.join(caminho_services, nome))
    )
    extras = [nome for nome in soltos if nome not in permitidos]
    if extras:
        return (
            f"services/ só pode ter {sorted(permitidos)} soltos na raiz; "
            f"encontrado(s) fora do padrão de caso de uso: {extras}"
        )
    return None


def _classe_e_metodo_do_caso_de_uso(caminho):
    with open(caminho, "r", encoding="utf-8") as arquivo:
        arvore = ast.parse(arquivo.read(), filename=caminho)

    classes = [
        nodo for nodo in arvore.body
        if isinstance(nodo, ast.ClassDef) and not nodo.name.startswith("_")
    ]
    if len(classes) != 1:
        return f"{caminho} deve ter exatamente uma classe pública, tem {len(classes)}"

    classe = classes[0]
    if not classe.name.endswith("Service"):
        return f"{caminho}: classe '{classe.name}' deveria terminar com 'Service'"

    metodos_publicos = [
        nodo for nodo in classe.body
        if isinstance(nodo, (ast.FunctionDef, ast.AsyncFunctionDef)) and not nodo.name.startswith("_")
    ]
    if len(metodos_publicos) != 1:
        return (
            f"{caminho}: classe '{classe.name}' deve ter exatamente um método público, "
            f"tem {len(metodos_publicos)}"
        )

    metodo = metodos_publicos[0]
    if metodo.name != "executar":
        return f"{caminho}: método público deveria se chamar 'executar', é '{metodo.name}'"

    decoradores = {d.id for d in metodo.decorator_list if isinstance(d, ast.Name)}
    if "staticmethod" not in decoradores:
        return f"{caminho}: 'executar' deveria ser @staticmethod"

    return None


class TestArquiteturaEmCamadas(unittest.TestCase):

    def test_services_nao_importam_database_ou_sqlalchemy(self):
        proibidos = ("database", "sqlalchemy")
        for caminho in _arquivos_py("services"):
            for nome in _nomes_importados(caminho):
                self.assertFalse(
                    _comeca_com(nome, proibidos),
                    f"{caminho} importa '{nome}', proibido para a camada de services",
                )

    def test_fora_de_models_e_repositories_ninguem_importa_sqlalchemy_nem_usa_db_session(self):
        pastas_permitidas = {"models", "repositories", "tests"}
        for caminho in _arquivos_py_do_backend():
            relativo = os.path.relpath(caminho, RAIZ).split(os.sep)
            if relativo[0] in pastas_permitidas:
                continue
            with self.subTest(arquivo=caminho):
                for nome in _nomes_importados(caminho):
                    self.assertFalse(
                        _comeca_com(nome, ("sqlalchemy",)),
                        f"{caminho} importa '{nome}', só models/ e repositories/ acessam SQLAlchemy",
                    )
                self.assertFalse(
                    _usa_db_session(caminho),
                    f"{caminho} usa db.session, só models/ e repositories/ acessam a sessão",
                )

    def test_controllers_nao_importam_repositories_ou_models(self):
        proibidos = ("repositories", "models")
        for caminho in _arquivos_py("controllers"):
            for nome in _nomes_importados(caminho):
                self.assertFalse(
                    _comeca_com(nome, proibidos),
                    f"{caminho} importa '{nome}', proibido para a camada de controllers",
                )

    def test_repositories_nao_importam_services_ou_controllers(self):
        proibidos = ("services", "controllers")
        for caminho in _arquivos_py("repositories"):
            for nome in _nomes_importados(caminho):
                self.assertFalse(
                    _comeca_com(nome, proibidos),
                    f"{caminho} importa '{nome}', proibido para a camada de repositories",
                )


class TestServicesPorCasoDeUso(unittest.TestCase):

    def test_arquivos_de_caso_de_uso_tem_uma_classe_service_com_um_metodo_executar(self):
        caminho_services = os.path.join(RAIZ, "services")
        for nome_area in _pastas_de_area(caminho_services):
            caminho_area = os.path.join(caminho_services, nome_area)
            for nome_arquivo in sorted(os.listdir(caminho_area)):
                if not nome_arquivo.endswith(".py"):
                    continue
                if nome_arquivo in ARQUIVOS_ISENTOS_DA_REGRA_DE_CASO_DE_USO:
                    continue
                caminho = os.path.join(caminho_area, nome_arquivo)
                erro = _classe_e_metodo_do_caso_de_uso(caminho)
                self.assertIsNone(erro, erro)

    def test_verificacao_de_caso_de_uso_reprova_duas_classes_publicas(self):
        with tempfile.TemporaryDirectory() as pasta:
            caminho = os.path.join(pasta, "exemplo_invalido.py")
            with open(caminho, "w", encoding="utf-8") as arquivo:
                arquivo.write(
                    "class UmService:\n"
                    "    @staticmethod\n"
                    "    def executar():\n"
                    "        pass\n"
                    "\n"
                    "class DoisService:\n"
                    "    @staticmethod\n"
                    "    def executar():\n"
                    "        pass\n"
                )
            self.assertIsNotNone(_classe_e_metodo_do_caso_de_uso(caminho))

    def test_verificacao_de_caso_de_uso_reprova_dois_metodos_publicos(self):
        with tempfile.TemporaryDirectory() as pasta:
            caminho = os.path.join(pasta, "exemplo_invalido.py")
            with open(caminho, "w", encoding="utf-8") as arquivo:
                arquivo.write(
                    "class ExemploService:\n"
                    "    @staticmethod\n"
                    "    def executar():\n"
                    "        pass\n"
                    "\n"
                    "    @staticmethod\n"
                    "    def outro():\n"
                    "        pass\n"
                )
            self.assertIsNotNone(_classe_e_metodo_do_caso_de_uso(caminho))

    def test_services_nao_importam_pacote_de_area_direto(self):
        caminho_services = os.path.join(RAIZ, "services")
        areas = _areas_com_pacote(caminho_services)
        caminho_init_raiz = os.path.normpath(os.path.join(caminho_services, "__init__.py"))
        for caminho in _arquivos_py("services"):
            if os.path.normpath(caminho) == caminho_init_raiz:
                continue
            for nome in _nomes_importados(caminho):
                partes = nome.split(".")
                if len(partes) == 2 and partes[0] == "services" and partes[1] in areas:
                    self.fail(
                        f"{caminho} importa '{nome}' (pacote de área); "
                        "importe o módulo completo, ex.: services.<area>.apoio"
                    )

    def test_services_so_tem_init_e_comum_soltos_na_raiz(self):
        caminho_services = os.path.join(RAIZ, "services")
        erro = _verificar_raiz_de_services_so_tem_arquivos_permitidos(caminho_services)
        self.assertIsNone(erro, erro)

    def test_verificacao_de_raiz_de_services_reprova_arquivo_solto_extra(self):
        with tempfile.TemporaryDirectory() as pasta:
            for nome in ("__init__.py", "comum.py", "legado.py"):
                with open(os.path.join(pasta, nome), "w", encoding="utf-8") as arquivo:
                    arquivo.write("")
            erro = _verificar_raiz_de_services_so_tem_arquivos_permitidos(pasta)
            self.assertIsNotNone(erro)


def _classes_do_modulo(caminho):
    with open(caminho, "r", encoding="utf-8") as arquivo:
        arvore = ast.parse(arquivo.read(), filename=caminho)
    return [nodo for nodo in arvore.body if isinstance(nodo, ast.ClassDef)]


def _nome_de_arquivo_esperado(nome_classe):
    return re.sub(r"(?<!^)(?=[A-Z])", "_", nome_classe).lower() + ".py"


def _bases_da_classe(classe):
    return [base.id for base in classe.bases if isinstance(base, ast.Name)]


ARQUIVOS_DE_APOIO_EM_MODELS = {"__init__.py", "base.py", "model.py"}


class TestUmaClassePorArquivoEmModels(unittest.TestCase):

    def test_cada_model_fica_em_arquivo_proprio_com_nome_da_classe(self):
        for caminho in _arquivos_py("models"):
            nome = os.path.basename(caminho)
            if nome in ARQUIVOS_DE_APOIO_EM_MODELS:
                continue
            with self.subTest(arquivo=nome):
                classes = _classes_do_modulo(caminho)
                self.assertEqual(len(classes), 1, f"{nome} deve ter uma classe, tem {len(classes)}")
                self.assertEqual(_bases_da_classe(classes[0]), ["ModeloBase"])
                self.assertEqual(nome, _nome_de_arquivo_esperado(classes[0].name))

    def test_base_e_model_py_nao_definem_model(self):
        classes_da_base = _classes_do_modulo(os.path.join(RAIZ, "models", "base.py"))
        self.assertEqual([classe.name for classe in classes_da_base], ["ModeloBase"])
        self.assertEqual(_classes_do_modulo(os.path.join(RAIZ, "models", "model.py")), [])


ARQUIVOS_DE_APOIO_EM_CONTROLLERS = {"__init__.py", "apoio.py", "controller.py"}


class TestUmaClassePorArquivoEmControllers(unittest.TestCase):

    def test_cada_controller_fica_em_arquivo_proprio_com_nome_da_classe(self):
        for caminho in _arquivos_py("controllers"):
            nome = os.path.basename(caminho)
            if nome in ARQUIVOS_DE_APOIO_EM_CONTROLLERS:
                continue
            with self.subTest(arquivo=nome):
                classes = _classes_do_modulo(caminho)
                self.assertEqual(len(classes), 1, f"{nome} deve ter uma classe, tem {len(classes)}")
                self.assertTrue(classes[0].name.endswith("Controller"))
                self.assertEqual(nome, _nome_de_arquivo_esperado(classes[0].name))

    def test_controller_py_e_apoio_nao_definem_controller(self):
        self.assertEqual(_classes_do_modulo(os.path.join(RAIZ, "controllers", "controller.py")), [])
        self.assertEqual(_classes_do_modulo(os.path.join(RAIZ, "controllers", "apoio.py")), [])


ARQUIVOS_DE_APOIO_EM_REPOSITORIES = {"__init__.py", "apoio.py", "repository.py"}


class TestUmaClassePorArquivoEmRepositories(unittest.TestCase):

    def test_cada_repository_fica_em_arquivo_proprio_com_nome_da_classe(self):
        for caminho in _arquivos_py("repositories"):
            nome = os.path.basename(caminho)
            if nome in ARQUIVOS_DE_APOIO_EM_REPOSITORIES:
                continue
            with self.subTest(arquivo=nome):
                classes = _classes_do_modulo(caminho)
                self.assertEqual(len(classes), 1, f"{nome} deve ter uma classe, tem {len(classes)}")
                self.assertTrue(classes[0].name.endswith("Repository"))
                self.assertEqual(nome, _nome_de_arquivo_esperado(classes[0].name))

    def test_repository_py_e_apoio_nao_definem_repository(self):
        self.assertEqual(_classes_do_modulo(os.path.join(RAIZ, "repositories", "repository.py")), [])
        self.assertEqual(_classes_do_modulo(os.path.join(RAIZ, "repositories", "apoio.py")), [])


METODOS_DE_CRUD_SIMPLES = {
    "criar", "criar_varios", "buscar_por_id", "salvar", "atualizar", "excluir",
    "inscrever", "adicionar_membro", "curtir", "descurtir", "marcar_lida", "listar_todos",
}

OPERACOES_DIRETAS_NA_SESSAO = {"add", "add_all", "delete", "commit", "rollback", "flush"}


class TestRepositoriesSemCrudSimples(unittest.TestCase):

    def test_repositories_nao_definem_crud_simples(self):
        for caminho in _arquivos_py("repositories"):
            nome = os.path.basename(caminho)
            if nome in ARQUIVOS_DE_APOIO_EM_REPOSITORIES:
                continue
            for classe in _classes_do_modulo(caminho):
                metodos = {
                    nodo.name for nodo in classe.body
                    if isinstance(nodo, (ast.FunctionDef, ast.AsyncFunctionDef))
                }
                with self.subTest(arquivo=nome):
                    self.assertFalse(
                        metodos & METODOS_DE_CRUD_SIMPLES,
                        f"{nome} define CRUD simples: {sorted(metodos & METODOS_DE_CRUD_SIMPLES)}; "
                        "use os métodos de ModeloBase",
                    )

    def test_repositories_nao_gravam_direto_na_sessao(self):
        for caminho in _arquivos_py("repositories"):
            nome = os.path.basename(caminho)
            with open(caminho, "r", encoding="utf-8") as arquivo:
                arvore = ast.parse(arquivo.read(), filename=caminho)
            for nodo in ast.walk(arvore):
                if (
                    isinstance(nodo, ast.Attribute)
                    and nodo.attr in OPERACOES_DIRETAS_NA_SESSAO
                    and isinstance(nodo.value, ast.Attribute)
                    and nodo.value.attr == "session"
                ):
                    self.fail(
                        f"{nome} chama db.session.{nodo.attr}; grave pelos métodos de ModeloBase "
                        "ou use efetivar() de models.base"
                    )


if __name__ == "__main__":
    unittest.main()
