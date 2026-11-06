from database import db
from models.base import ModeloBase
from utils import agora, iso_utc


class Notificacao(ModeloBase):
    __tablename__ = "notificacao"

    id_notif = db.Column(db.Integer, primary_key=True, autoincrement=True)
    id_usuario = db.Column(
        db.Integer,
        db.ForeignKey("usuario.id_usuario", ondelete="CASCADE"),
        nullable=False,
    )
    tipo = db.Column(db.String(60), nullable=False)
    mensagem = db.Column(db.String(300), nullable=False)
    lida = db.Column(db.Boolean, nullable=False, default=False)
    tipo_alvo = db.Column(db.String(20))
    id_alvo = db.Column(db.Integer)
    data_envio = db.Column(db.DateTime, nullable=False, default=agora)

    @staticmethod
    def formatar(c):
        return {
            "id": c["id_notif"],
            "tipo": c["tipo"],
            "mensagem": c["mensagem"],
            "lida": c["lida"],
            "tipo_alvo": c["tipo_alvo"],
            "id_alvo": c["id_alvo"],
            "data_envio": iso_utc(c["data_envio"]),
        }

    def to_dict(self):
        return self.formatar(self.campos())
