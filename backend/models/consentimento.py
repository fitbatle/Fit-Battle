from database import db
from models.base import ModeloBase
from utils import agora, iso_utc


class Consentimento(ModeloBase):
    __tablename__ = "consentimento"
    __table_args__ = (
        db.UniqueConstraint("id_usuario", "chave", name="uq_consent_usuario_chave"),
    )

    id_consentimento = db.Column(db.Integer, primary_key=True, autoincrement=True)
    id_usuario = db.Column(
        db.Integer,
        db.ForeignKey("usuario.id_usuario", ondelete="CASCADE"),
        nullable=False,
    )
    chave = db.Column(db.String(40), nullable=False)
    descricao = db.Column(db.String(200), nullable=False)
    obrigatorio = db.Column(db.Boolean, nullable=False, default=False)
    aceito = db.Column(db.Boolean, nullable=False, default=True)
    data_registro = db.Column(db.DateTime, nullable=False, default=agora)
    data_atualizacao = db.Column(db.DateTime)

    @staticmethod
    def formatar(c):
        return {
            "chave": c["chave"],
            "descricao": c["descricao"],
            "obrigatorio": c["obrigatorio"],
            "aceito": c["aceito"],
            "data_registro": iso_utc(c["data_registro"]),
            "data_atualizacao": iso_utc(c["data_atualizacao"]),
        }

    def to_dict(self):
        return self.formatar(self.campos())
