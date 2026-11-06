from models.consentimento import Consentimento

CONSENTIMENTOS_OBRIGATORIOS = {
    "conta_autenticacao": "Criar, autenticar e manter a minha conta",
    "registro_atividades": "Registrar e armazenar meus treinos",
    "historico_estatisticas": "Manter meu histórico e minhas estatísticas individuais",
    "dados_saude": "Tratar dados de treino que possam revelar condição de saúde (art. 11 da LGPD)",
    "seguranca_auditoria": "Guardar registros técnicos de segurança e auditoria",
}
CONSENTIMENTOS_OPCIONAIS = {
    "ranking_publico": "Exibir meu perfil e desempenho nos rankings regional e global",
    "localizacao": "Usar minha cidade/região para o ranking regional",
    "chat_publico": "Participar dos chats públicos da plataforma",
    "chat_privado_externo": "Receber mensagens privadas de usuários fora dos meus grupos",
    "busca_perfil": "Permitir que outros usuários me encontrem pela busca",
    "notificacoes": "Receber notificações por push ou e-mail",
    "compartilhamento": "Compartilhar conquistas e recordes em redes sociais externas",
}


def registrar_consentimentos_iniciais(id_usuario, escolhas):
    escolhas = escolhas or {}
    registros = []

    for chave, descricao in CONSENTIMENTOS_OBRIGATORIOS.items():
        registros.append({
            "chave": chave, "descricao": descricao,
            "obrigatorio": True, "aceito": True,
        })

    for chave, descricao in CONSENTIMENTOS_OPCIONAIS.items():
        registros.append({
            "chave": chave, "descricao": descricao,
            "obrigatorio": False,
            "aceito": bool(escolhas.get(chave, False)),
        })

    with Consentimento.transacao():
        return [Consentimento(id_usuario=id_usuario, **registro).salvar() for registro in registros]
