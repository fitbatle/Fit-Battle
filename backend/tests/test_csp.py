import os
import re
import unittest

from politica_csp import PASTA_FRONTEND, meta_csp, paginas_html

REGEX_SCRIPT_SEM_SRC = re.compile(r"<script(?![^>]*\ssrc=)[^>]*>", re.I)
REGEX_ATRIBUTO_ON = re.compile(r"\son[a-z]+\s*=", re.I)
REGEX_META = re.compile(r'<meta http-equiv="Content-Security-Policy"[^>]*>')


def _texto(caminho):
    with open(caminho, "r", encoding="utf-8") as arquivo:
        return arquivo.read()


class TestContentSecurityPolicy(unittest.TestCase):

    def test_toda_pagina_tem_a_meta_gerada_a_partir_do_ponto_unico(self):
        esperada = meta_csp()
        sem_meta = []
        for caminho in paginas_html():
            conteudo = _texto(caminho)
            if conteudo.count(esperada) != 1:
                sem_meta.append(os.path.relpath(caminho, PASTA_FRONTEND).replace(os.sep, "/"))
        self.assertEqual(
            sem_meta, [],
            "Páginas sem a meta CSP atual (rode backend/gerar_csp.py): " + ", ".join(sem_meta),
        )

    def test_nenhuma_pagina_tem_script_inline(self):
        infratores = [
            os.path.relpath(caminho, PASTA_FRONTEND).replace(os.sep, "/")
            for caminho in paginas_html()
            if REGEX_SCRIPT_SEM_SRC.search(_texto(caminho))
        ]
        self.assertEqual(infratores, [], "Scripts inline encontrados: " + ", ".join(infratores))

    def test_nenhuma_pagina_tem_atributo_de_evento_inline(self):
        infratores = [
            os.path.relpath(caminho, PASTA_FRONTEND).replace(os.sep, "/")
            for caminho in paginas_html()
            if REGEX_ATRIBUTO_ON.search(_texto(caminho))
        ]
        self.assertEqual(infratores, [], "Atributos on* encontrados: " + ", ".join(infratores))

    def test_politica_nao_libera_script_inline(self):
        politica = REGEX_META.search(meta_csp()).group(0)
        self.assertIn("script-src 'self'", politica)
        self.assertNotIn("script-src 'self' 'unsafe-inline'", politica)


if __name__ == "__main__":
    unittest.main()
