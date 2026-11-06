import os
import unittest

RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

PASTAS_VARRIDAS = ["frontend", "backend"]
PASTAS_IGNORADAS = {os.path.join("frontend", "mockups"), os.path.join("backend", "uploads"), "__pycache__"}
EXTENSOES_TEXTO = {".html", ".js", ".css", ".py", ".md", ".sql", ".json", ".txt", ".svg"}

FAIXAS_EMOJI = [
    (0x1F000, 0x1FAFF),
    (0x2600, 0x27BF),
    (0x2B00, 0x2BFF),
    (0xFE0F, 0xFE0F),
    (0x200D, 0x200D),
]


def _arquivos_de_texto():
    for pasta in PASTAS_VARRIDAS:
        for raiz, pastas, nomes in os.walk(os.path.join(RAIZ, pasta)):
            relativa = os.path.relpath(raiz, RAIZ)
            pastas[:] = [
                nome for nome in pastas
                if os.path.join(relativa, nome) not in PASTAS_IGNORADAS and nome not in PASTAS_IGNORADAS
            ]
            for nome in nomes:
                if os.path.splitext(nome)[1].lower() in EXTENSOES_TEXTO:
                    yield os.path.join(raiz, nome)
    yield os.path.join(RAIZ, "README.md")


def _e_emoji(codigo):
    return any(inicio <= codigo <= fim for inicio, fim in FAIXAS_EMOJI)


def _achados():
    for caminho in _arquivos_de_texto():
        with open(caminho, "r", encoding="utf-8") as arquivo:
            try:
                linhas = arquivo.read().splitlines()
            except UnicodeDecodeError:
                continue
        for numero, linha in enumerate(linhas, 1):
            for caractere in linha:
                if _e_emoji(ord(caractere)):
                    relativo = os.path.relpath(caminho, RAIZ).replace(os.sep, "/")
                    yield ascii(f"{relativo}:{numero} U+{ord(caractere):04X} {linha.strip()[:120]}")


class TestSemEmoji(unittest.TestCase):

    def test_nao_ha_emoji_no_frontend_backend_nem_readme(self):
        achados = list(_achados())
        if achados:
            self.fail("Emoji encontrado (arquivo:linha, codigo, trecho):\n" + "\n".join(achados))


if __name__ == "__main__":
    unittest.main()
