import threading
import time

from services.comum import ErroValidacao


class _LimitadorLogin:

    MAX_TENTATIVAS = 5
    JANELA_SEGUNDOS = 15 * 60
    BLOQUEIO_SEGUNDOS = 15 * 60

    _tentativas = {}
    _lock = threading.Lock()

    @classmethod
    def verificar(cls, chave):
        with cls._lock:
            registro = cls._tentativas.get(chave)
            if not registro:
                return
            bloqueado_ate = registro.get("bloqueado_ate")
            if bloqueado_ate and bloqueado_ate > time.time():
                restante = int(bloqueado_ate - time.time())
                raise ErroValidacao(
                    f"Muitas tentativas de login. Tente novamente em {restante} segundos.",
                    status=429,
                )

    @classmethod
    def registrar_falha(cls, chave):
        with cls._lock:
            agora = time.time()
            registro = cls._tentativas.setdefault(chave, {"falhas": [], "bloqueado_ate": None})
            registro["falhas"] = [t for t in registro["falhas"] if agora - t < cls.JANELA_SEGUNDOS]
            registro["falhas"].append(agora)
            if len(registro["falhas"]) >= cls.MAX_TENTATIVAS:
                registro["bloqueado_ate"] = agora + cls.BLOQUEIO_SEGUNDOS
                registro["falhas"] = []

    @classmethod
    def registrar_sucesso(cls, chave):
        with cls._lock:
            cls._tentativas.pop(chave, None)

    @classmethod
    def resetar(cls):
        with cls._lock:
            cls._tentativas.clear()


def resetar_limitador_login():
    _LimitadorLogin.resetar()
