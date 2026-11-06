from database import db
from models.base import ModeloBase
from utils import agora


class Curtida(ModeloBase):
    __tablename__ = "curtida"
    __table_args__ = (
        db.UniqueConstraint("id_usuario", "tipo_alvo", "id_alvo", name="uq_curtida_usuario_alvo"),
    )

    id_curtida = db.Column(db.Integer, primary_key=True, autoincrement=True)
    id_usuario = db.Column(
        db.Integer,
        db.ForeignKey("usuario.id_usuario", ondelete="CASCADE"),
        nullable=False,
    )
    tipo_alvo = db.Column(db.String(20), nullable=False)
    id_alvo = db.Column(db.Integer, nullable=False)
    data_registro = db.Column(db.DateTime, nullable=False, default=agora)
