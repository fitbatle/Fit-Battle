from database import db
from models.base import ModeloBase
from utils import agora, calcular_idade, iso_utc


class Usuario(ModeloBase):
    __tablename__ = "usuario"

    id_usuario = db.Column(db.Integer, primary_key=True, autoincrement=True)
    nome = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    senha = db.Column(db.String(255), nullable=False)
    idade = db.Column(db.SmallInteger)
    data_nascimento = db.Column(db.Date)
    peso = db.Column(db.Numeric(5, 2))
    altura = db.Column(db.Numeric(3, 2))
    cidade = db.Column(db.String(100))
    estado = db.Column(db.String(2))
    foto = db.Column(db.String(255))
    descricao = db.Column(db.String(300))
    responsavel_nome = db.Column(db.String(120))
    responsavel_email = db.Column(db.String(150))
    responsavel_autorizado_em = db.Column(db.DateTime)
    nivel = db.Column(db.String(20), nullable=False, default="iniciante")
    xp = db.Column(db.Integer, nullable=False, default=0)
    perfil_publico = db.Column(db.Boolean, nullable=False, default=True)
    criado_em = db.Column(db.DateTime, nullable=False, default=agora)

    atividades = db.relationship(
        "Atividade",
        backref="usuario",
        cascade="all, delete-orphan",
        lazy="dynamic",
    )

    consentimentos = db.relationship(
        "Consentimento",
        backref="usuario",
        cascade="all, delete-orphan",
        lazy="dynamic",
    )

    @staticmethod
    def formatar(c):
        return {
            "id": c["id_usuario"],
            "nome": c["nome"],
            "email": c["email"],
            "idade": calcular_idade(c["data_nascimento"], c["idade"]),
            "data_nascimento": c["data_nascimento"].isoformat() if c["data_nascimento"] else None,
            "peso": float(c["peso"]) if c["peso"] is not None else None,
            "altura": float(c["altura"]) if c["altura"] is not None else None,
            "cidade": c["cidade"],
            "estado": c["estado"],
            "foto": c["foto"],
            "descricao": c["descricao"],
            "nivel": c["nivel"],
            "xp": c["xp"],
            "perfil_publico": c["perfil_publico"],
            "criado_em": iso_utc(c["criado_em"]),
        }

    def to_dict(self):
        return self.formatar(self.campos())

    @staticmethod
    def formatar_publico(c):
        return {
            "id": c["id_usuario"],
            "nome": c["nome"],
            "cidade": c["cidade"],
            "estado": c["estado"],
            "foto": c["foto"],
            "descricao": c["descricao"],
            "nivel": c["nivel"],
            "xp": c["xp"],
            "criado_em": iso_utc(c["criado_em"]),
        }

    def to_publico(self):
        return self.formatar_publico(self.campos())
