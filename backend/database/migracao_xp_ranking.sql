USE fitbattle;

CREATE OR REPLACE VIEW vw_ranking_global AS
WITH idade_usuario AS (
    SELECT u.*,
        CASE
            WHEN u.data_nascimento IS NOT NULL THEN
                (SUBSTR(CURRENT_DATE,1,4)+0 - SUBSTR(u.data_nascimento,1,4)+0)
                - CASE WHEN (SUBSTR(CURRENT_DATE,6,2)+0)*100 + (SUBSTR(CURRENT_DATE,9,2)+0)
                            < (SUBSTR(u.data_nascimento,6,2)+0)*100 + (SUBSTR(u.data_nascimento,9,2)+0)
                       THEN 1 ELSE 0 END
            ELSE u.idade
        END AS idade_calculada
    FROM usuario u
)
SELECT
    u.id_usuario,
    u.nome,
    u.cidade,
    u.estado,
    COALESCE(u.xp, 0) AS pontuacao_total,
    RANK() OVER (ORDER BY COALESCE(u.xp, 0) DESC) AS posicao
FROM idade_usuario u
WHERE u.perfil_publico = 1
    AND (u.idade_calculada IS NULL OR u.idade_calculada >= 18);

CREATE OR REPLACE VIEW vw_ranking_regional AS
WITH idade_usuario AS (
    SELECT u.*,
        CASE
            WHEN u.data_nascimento IS NOT NULL THEN
                (SUBSTR(CURRENT_DATE,1,4)+0 - SUBSTR(u.data_nascimento,1,4)+0)
                - CASE WHEN (SUBSTR(CURRENT_DATE,6,2)+0)*100 + (SUBSTR(CURRENT_DATE,9,2)+0)
                            < (SUBSTR(u.data_nascimento,6,2)+0)*100 + (SUBSTR(u.data_nascimento,9,2)+0)
                       THEN 1 ELSE 0 END
            ELSE u.idade
        END AS idade_calculada
    FROM usuario u
)
SELECT
    u.id_usuario,
    u.nome,
    u.cidade,
    u.estado,
    COALESCE(u.xp, 0) AS pontuacao_total,
    RANK() OVER (
        PARTITION BY u.cidade
        ORDER BY COALESCE(u.xp, 0) DESC
    ) AS posicao
FROM idade_usuario u
WHERE u.perfil_publico = 1
    AND (u.idade_calculada IS NULL OR u.idade_calculada >= 18);

CREATE OR REPLACE VIEW vw_ranking_grupo AS
SELECT
    gm.id_grupo,
    u.id_usuario,
    u.nome,
    COALESCE(u.xp, 0) AS pontuacao_total,
    RANK() OVER (
        PARTITION BY gm.id_grupo
        ORDER BY COALESCE(u.xp, 0) DESC
    ) AS posicao
FROM grupo_membro gm
JOIN usuario u ON u.id_usuario = gm.id_usuario;
