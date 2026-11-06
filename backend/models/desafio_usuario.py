from database import db
from models.base import ModeloBase


class DesafioUsuario(ModeloBase):
    __tablename__ = "desafio_usuario"

    id_desafio = db.Column(
        db.Integer,
        db.ForeignKey("desafio.id_desafio", ondelete="CASCADE"),
        primary_key=True,
    )
    id_usuario = db.Column(
        db.Integer,
        db.ForeignKey("usuario.id_usuario", ondelete="CASCADE"),
        primary_key=True,
    )
    status = db.Column(db.String(10), nullable=False, default="inscrito")
    concluido_em = db.Column(db.DateTime)
