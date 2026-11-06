from database import db
from models.base import ModeloBase
from utils import agora, iso_utc


class Grupo(ModeloBase):
    __tablename__ = "grupo"

    id_grupo = db.Column(db.Integer, primary_key=True, autoincrement=True)
    nome = db.Column(db.String(120), nullable=False)
    descricao = db.Column(db.String(300))
    privacidade = db.Column(db.String(10), nullable=False, default="privado")
    codigo_convite = db.Column(db.String(10), unique=True)
    id_criador = db.Column(
        db.Integer,
        db.ForeignKey("usuario.id_usuario", ondelete="CASCADE"),
        nullable=False,
    )
    data_criacao = db.Column(db.DateTime, nullable=False, default=agora)

    @staticmethod
    def formatar(c):
        return {
            "id": c["id_grupo"],
            "nome": c["nome"],
            "descricao": c["descricao"],
            "id_criador": c["id_criador"],
            "data_criacao": iso_utc(c["data_criacao"]),
        }

    def to_dict(self):
        return self.formatar(self.campos())
