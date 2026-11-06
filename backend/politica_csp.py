import os
import re
from urllib.parse import urlparse

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PASTA_FRONTEND = os.path.join(RAIZ, "frontend")
PASTA_MOCKUPS = os.path.join(PASTA_FRONTEND, "mockups")
ARQUIVO_CONFIG = os.path.join(PASTA_FRONTEND, "config.js")
PORTA_API_DESENVOLVIMENTO = 5000

REGEX_CONFIG = re.compile(r"window\.FITBATTLE_API_URL\s*=\s*['\"]([^'\"]*)['\"]")
REGEX_META = re.compile(r'<meta http-equiv="Content-Security-Policy"[^>]*>')
REGEX_INICIO_DO_HEAD = re.compile(r"<head>\s*")


def origem_da_api():
    with open(ARQUIVO_CONFIG, "r", encoding="utf-8") as arquivo:
        encontrado = REGEX_CONFIG.search(arquivo.read())
    if not encontrado or not encontrado.group(1):
        return None
    partes = urlparse(encontrado.group(1))
    return f"{partes.scheme}://{partes.netloc}"


def politica():
    origem = origem_da_api()
    desenvolvimento = f"http://*:{PORTA_API_DESENVOLVIMENTO}"
    conexao = ["'self'", desenvolvimento]
    imagem = ["'self'", "data:", desenvolvimento]
    if origem:
        conexao.append(origem)
        imagem.append(origem)
    diretivas = [
        "default-src 'self'",
        "script-src 'self'",
        "style-src 'self' 'unsafe-inline'",
        f"img-src {' '.join(imagem)}",
        f"connect-src {' '.join(conexao)}",
        "font-src 'self'",
        "frame-src 'self'",
        "object-src 'none'",
        "base-uri 'self'",
        "form-action 'self'",
    ]
    return "; ".join(diretivas)


def meta_csp():
    return f'<meta http-equiv="Content-Security-Policy" content="{politica()}">'


def paginas_html():
    for raiz, pastas, nomes in os.walk(PASTA_FRONTEND):
        if raiz.startswith(PASTA_MOCKUPS):
            pastas[:] = []
            continue
        for nome in nomes:
            if nome.endswith(".html"):
                yield os.path.join(raiz, nome)


def aplicar_nas_paginas():
    meta = meta_csp()
    alteradas = []
    for caminho in paginas_html():
        with open(caminho, "r", encoding="utf-8", newline="") as arquivo:
            conteudo = arquivo.read()
        fim_de_linha = "\r\n" if "\r\n" in conteudo else "\n"
        if REGEX_META.search(conteudo):
            novo = REGEX_META.sub(lambda _: meta, conteudo)
        else:
            novo = REGEX_INICIO_DO_HEAD.sub(lambda casa: casa.group(0) + meta + fim_de_linha, conteudo, count=1)
        if novo != conteudo:
            with open(caminho, "w", encoding="utf-8", newline="") as arquivo:
                arquivo.write(novo)
            alteradas.append(caminho)
    return alteradas
