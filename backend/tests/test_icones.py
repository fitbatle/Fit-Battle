import os
import re
import unittest

RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PASTA_FRONTEND = os.path.join(RAIZ, "frontend")
PASTA_MOCKUPS = os.path.join(PASTA_FRONTEND, "mockups")
ARQUIVO_ICONES = os.path.join(PASTA_FRONTEND, "icones.js")
SIMBOLOS_SUBSTITUIDOS = {0x2713, 0x2715, 0x270E, 0x2709, 0x2694}


def _arquivos_do_frontend():
    for raiz, pastas, nomes in os.walk(PASTA_FRONTEND):
        if raiz.startswith(PASTA_MOCKUPS):
            pastas[:] = []
            continue
        for nome in nomes:
            if nome.endswith((".js", ".html")):
                yield os.path.join(raiz, nome)


def _texto(caminho):
    with open(caminho, "r", encoding="utf-8") as arquivo:
        return arquivo.read()


def _nomes_usados_nas_telas():
    usados = set()
    for caminho in _arquivos_do_frontend():
        conteudo = _texto(caminho)
        usados.update(re.findall(r"criarIcone\(\s*['\"](\w+)['\"]", conteudo))
        usados.update(re.findall(r"montarComIcone\(\s*['\"](\w+)['\"]", conteudo))
        usados.update(re.findall(r"data-icone=\"(\w+)\"", conteudo))
    return usados


class TestIcones(unittest.TestCase):

    def test_todo_nome_usado_existe_no_conjunto(self):
        codigo = _texto(ARQUIVO_ICONES)
        existentes = set(re.findall(r"^  (\w+): \[", codigo, re.M))
        mapa = re.search(r"const ICONE_POR_TIPO = \{(.*?)\};", codigo, re.S).group(1)
        usados = _nomes_usados_nas_telas() | set(re.findall(r"'(\w+)'", mapa))
        faltando = sorted(usados - existentes)
        self.assertEqual(faltando, [], f"Ícones usados sem definição em icones.js: {faltando}")

    def test_nomes_globais_de_icones_nao_colidem_com_outros_scripts(self):
        nomes = set(re.findall(r"^(?:const|let|var|function) (\w+)", _texto(ARQUIVO_ICONES), re.M))
        colisoes = []
        for caminho in _arquivos_do_frontend():
            if caminho == ARQUIVO_ICONES or not caminho.endswith(".js"):
                continue
            declarados = set(re.findall(r"^(?:const|let|var|function|class) (\w+)", _texto(caminho), re.M))
            colisoes.extend(f"{os.path.basename(caminho)}:{nome}" for nome in sorted(nomes & declarados))
        self.assertEqual(colisoes, [], "Nomes globais de icones.js já declarados em outros scripts: " + ", ".join(colisoes))

    def test_criacao_de_icones_nao_usa_innerhtml(self):
        self.assertNotIn("innerHTML", _texto(ARQUIVO_ICONES))

    def test_simbolos_tipograficos_substituidos_por_icones_nao_aparecem(self):
        encontrados = []
        for caminho in _arquivos_do_frontend():
            for numero, linha in enumerate(_texto(caminho).splitlines(), 1):
                if any(ord(caractere) in SIMBOLOS_SUBSTITUIDOS for caractere in linha):
                    relativo = os.path.relpath(caminho, RAIZ).replace(os.sep, "/")
                    encontrados.append(ascii(f"{relativo}:{numero}"))
        self.assertEqual(encontrados, [], "Símbolos substituídos por ícones ainda presentes: " + ", ".join(encontrados))


if __name__ == "__main__":
    unittest.main()
