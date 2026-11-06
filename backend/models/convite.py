from database import db
from models.base import ModeloBase
from utils import agora


class Convite(ModeloBase):
    __tablename__ = "convite"
    __table_args__ = (
        db.UniqueConstraint("id_grupo", "id_destinatario", "status", name="uq_convite"),
    )

    id_convite = db.Column(db.Integer, primary_key=True, autoincrement=True)
    id_grupo = db.Column(
        db.Integer,
        db.ForeignKey("grupo.id_grupo", ondelete="CASCADE"),
        nullable=False,
    )
    id_remetente = db.Column(
        db.Integer,
        db.ForeignKey("usuario.id_usuario", ondelete="CASCADE"),
        nullable=False,
    )
    id_destinatario = db.Column(
        db.Integer,
        db.ForeignKey("usuario.id_usuario", ondelete="CASCADE"),
        nullable=False,
    )
    status = db.Column(db.String(10), nullable=False, default="pendente")
    data_envio = db.Column(db.DateTime, nullable=False, default=agora)
    data_resposta = db.Column(db.DateTime)
