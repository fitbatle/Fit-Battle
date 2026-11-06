from database import db
from models.base import ModeloBase
from utils import agora, iso_utc


class Atividade(ModeloBase):
    __tablename__ = "atividade"

    id_atividade = db.Column(db.Integer, primary_key=True, autoincrement=True)
    id_usuario = db.Column(
        db.Integer,
        db.ForeignKey("usuario.id_usuario", ondelete="CASCADE"),
        nullable=False,
    )
    tipo = db.Column(db.String(60), nullable=False)
    titulo = db.Column(db.String(120))
    descricao = db.Column(db.String(500))
    tempo_min = db.Column(db.Integer)
    distancia_km = db.Column(db.Numeric(6, 2))
    carga_kg = db.Column(db.Numeric(6, 2))
    repeticoes = db.Column(db.Integer)
    pontuacao = db.Column(db.Integer, nullable=False, default=0)
    data_registro = db.Column(db.DateTime, nullable=False, default=agora)

    @staticmethod
    def formatar(c):
        return {
            "id": c["id_atividade"],
            "id_usuario": c["id_usuario"],
            "tipo": c["tipo"],
            "titulo": c["titulo"],
            "descricao": c["descricao"],
            "tempo_min": c["tempo_min"],
            "distancia_km": float(c["distancia_km"]) if c["distancia_km"] is not None else None,
            "carga_kg": float(c["carga_kg"]) if c["carga_kg"] is not None else None,
            "repeticoes": c["repeticoes"],
            "pontuacao": c["pontuacao"],
            "data_registro": iso_utc(c["data_registro"]),
        }

    def to_dict(self):
        return self.formatar(self.campos())
