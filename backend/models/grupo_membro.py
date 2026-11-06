from database import db
from models.base import ModeloBase
from utils import agora


class GrupoMembro(ModeloBase):
    __tablename__ = "grupo_membro"

    id_grupo = db.Column(
        db.Integer,
        db.ForeignKey("grupo.id_grupo", ondelete="CASCADE"),
        primary_key=True,
    )
    id_usuario = db.Column(
        db.Integer,
        db.ForeignKey("usuario.id_usuario", ondelete="CASCADE"),
        primary_key=True,
    )
    papel = db.Column(db.String(10), nullable=False, default="membro")
    entrou_em = db.Column(db.DateTime, nullable=False, default=agora)
