import math
import os
import secrets

EXTENSOES_FOTO = {"png", "jpg", "jpeg", "gif", "webp"}
VALOR_OBJETIVO_MAXIMO = 1000000


def numero_decimal(valor, nome, maximo):
    try:
        numero = float(str(valor).replace(",", "."))
    except (TypeError, ValueError):
        raise ErroValidacao(f"O campo '{nome}' deve ser numérico.")
    if not math.isfinite(numero):
        raise ErroValidacao(f"O campo '{nome}' deve ser numérico.")
    if numero > maximo:
        raise ErroValidacao(f"O campo '{nome}' não pode passar de {maximo}.")
    return numero


class ErroValidacao(Exception):

    def __init__(self, mensagem, status=400):
        super().__init__(mensagem)
        self.mensagem = mensagem
        self.status = status


def texto_do_cliente(valor, nome):
    if valor is None:
        return ""
    if not isinstance(valor, str):
        raise ErroValidacao(f"O campo '{nome}' deve ser um texto.")
    return valor.strip()


def senha_do_cliente(valor):
    if not isinstance(valor, str):
        raise ErroValidacao("Informe a senha em formato de texto.")
    return valor


def inteiro_do_cliente(valor, nome):
    if isinstance(valor, bool):
        raise ErroValidacao(f"O campo '{nome}' deve ser um número inteiro.")
    if isinstance(valor, int):
        return valor
    if isinstance(valor, str) and valor.strip().isdigit():
        return int(valor)
    raise ErroValidacao(f"O campo '{nome}' deve ser um número inteiro.")


def _assinatura_confere(cabecalho, ext):
    if ext == "png":
        return cabecalho.startswith(b"\x89PNG\r\n\x1a\n")
    if ext == "jpg":
        return cabecalho.startswith(b"\xff\xd8\xff")
    if ext == "gif":
        return cabecalho.startswith((b"GIF87a", b"GIF89a"))
    if ext == "webp":
        return cabecalho[:4] == b"RIFF" and cabecalho[8:12] == b"WEBP"
    return False


def validar_extensao_imagem(arquivo):
    ext = arquivo.filename.rsplit(".", 1)[-1].lower() if "." in arquivo.filename else ""
    if ext not in EXTENSOES_FOTO:
        raise ErroValidacao("Formato inválido. Envie uma imagem PNG, JPG, GIF ou WEBP.")
    ext = "jpg" if ext == "jpeg" else ext
    cabecalho = arquivo.stream.read(12)
    arquivo.stream.seek(0)
    if not _assinatura_confere(cabecalho, ext):
        raise ErroValidacao("O arquivo enviado não é uma imagem PNG, JPG, GIF ou WEBP válida.")
    return ext


def salvar_imagem(arquivo, pasta_destino, prefixo, apagar_existentes=False):
    ext = validar_extensao_imagem(arquivo)
    os.makedirs(pasta_destino, exist_ok=True)

    if apagar_existentes:
        for nome_arquivo in os.listdir(pasta_destino):
            if nome_arquivo.startswith(prefixo + "_") or nome_arquivo.startswith(prefixo + "."):
                try:
                    os.remove(os.path.join(pasta_destino, nome_arquivo))
                except OSError:
                    pass

    nome = f"{prefixo}_{secrets.token_hex(8)}.{ext}"
    arquivo.save(os.path.join(pasta_destino, nome))
    return "/uploads/" + nome
