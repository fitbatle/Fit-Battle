# Fit-Battle

#Bernardo Nardelli, Cauã Gomes, João Paulo Costa, João Pedro Braga, Miguel Assunção, Henrique Vale.

nome-do-projeto/
├── frontend/
│   └── index.html
└── backend/
    ├── app.py
    ├── controllers/
    │   └── user_controller.py
    ├── models/
    │   └── user_model.py
    ├── repositories/
    │   └── user_repository.py
    ├── services/
    │   └── user_service.py
    └── database/
        └── create_database.sql
        
Funcionalidades:
1:Cadastro(nome, data de nascimento, e-mail, senha)
2:Login e autenticação, com token assinado
3:Perfil (visualizar/editar, foto, nível, bio)
4:Registrar atividade (tipo, tempo, distância, carga/repetições)
5:Histórico completo de atividades
6:Criar grupos privados de competição
7:Convidar via link/código ou busca direta
8:Aceitar/recusar convites
9:Ranking interno do grupo
10:Ranking regional, por "Da sua cidade" ou "Do seu estado"
11:Ranking global
12:Cálculo automático de pontuação por atividade
13:Atribuição automática de nível/categoria por XP (cinco categorias: iniciante → intermediário → avançado → profissional → elite)
14:Dashboard com XP por semana, treinos por semana, distribuição por tipo, evolução de carga máxima, sequência atual/melhor e totais
15:Criar/gerenciar metas pessoais (curto/longo prazo)
16:Desafios sazonais propostos pela administração (e-mails em ADMIN_EMAILS)
17:Bloco "Em Andamento" com metas ativas e desafios em que o usuário está inscrito
18:Notificações in-app (sino no header, contador de não lidas, e-mail opcional via SMTP)
19:Busca de perfis (nome ou cidade) e busca de grupos
20:Compartilhar treino, recorde, meta ou medalha em redes sociais externas (condicionado ao consentimento "compartilhamento")
