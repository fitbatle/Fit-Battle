from database import db
from models.base import ModeloBase
from utils import agora, iso_utc


class Comentario(ModeloBase):
    __tablename__ = "comentario"

    id_comentario = db.Column(db.Integer, primary_key=True, autoincrement=True)
    id_usuario = db.Column(
        db.Integer,
        db.ForeignKey("usuario.id_usuario", ondelete="CASCADE"),
        nullable=False,
    )
    tipo_alvo = db.Column(db.String(20), nullable=False)
    id_alvo = db.Column(db.Integer, nullable=False)
    texto = db.Column(db.String(500), nullable=False)
    data_registro = db.Column(db.DateTime, nullable=False, default=agora)

    @staticmethod
    def formatar(c):
        return {
            "id": c["id_comentario"],
            "id_usuario": c["id_usuario"],
            "texto": c["texto"],
            "data_registro": iso_utc(c["data_registro"]),
        }

    def to_dict(self):
        return self.formatar(self.campos())
