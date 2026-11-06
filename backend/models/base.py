from contextlib import contextmanager

from sqlalchemy.exc import IntegrityError

from database import db
from utils import ConflitoDeDados


def sincronizar():
    db.session.flush()


def efetivar():
    if db.session.info.get("transacao"):
        db.session.flush()
        db.session.expire_all()
    else:
        db.session.commit()


class ModeloBase(db.Model):
    __abstract__ = True

    def salvar(self):
        return self._confirmar(lambda: db.session.add(self))

    def atualizar(self, campos):
        chaves = {coluna.key for coluna in self.__mapper__.primary_key}
        atributos = {coluna.key for coluna in self.__mapper__.column_attrs} - chaves
        for nome, valor in campos.items():
            if nome in atributos:
                setattr(self, nome, valor)
        return self.salvar()

    def deletar(self):
        return self._confirmar(lambda: db.session.delete(self))

    def campos(self):
        return {atributo.key: getattr(self, atributo.key) for atributo in self.__mapper__.column_attrs}

    @classmethod
    def listar_todos(cls):
        return db.session.execute(db.select(cls)).scalars().all()

    @classmethod
    def buscar_por_id(cls, chave):
        return db.session.get(cls, chave)

    @staticmethod
    @contextmanager
    def transacao():
        if db.session.info.get("transacao"):
            yield
            return
        db.session.info["transacao"] = True
        try:
            yield
            db.session.commit()
        except Exception:
            db.session.rollback()
            raise
        finally:
            db.session.info["transacao"] = False

    def _confirmar(self, operacao):
        try:
            operacao()
            efetivar()
        except IntegrityError as erro:
            db.session.rollback()
            raise ConflitoDeDados() from erro
        except Exception:
            db.session.rollback()
            raise
        return self
