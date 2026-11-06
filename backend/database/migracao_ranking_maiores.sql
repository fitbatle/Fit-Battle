-- Rode este script quantas vezes precisar. CREATE OR REPLACE VIEW
-- nao falha se a view ja existir, ao contrario das migracoes de
-- ADD COLUMN.

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
    COALESCE(SUM(a.pontuacao), 0) AS pontuacao_total,
    RANK() OVER (ORDER BY COALESCE(SUM(a.pontuacao), 0) DESC) AS posicao
FROM idade_usuario u
LEFT JOIN atividade a ON a.id_usuario = u.id_usuario
WHERE u.perfil_publico = 1
    AND (u.idade_calculada IS NULL OR u.idade_calculada >= 18)
GROUP BY u.id_usuario, u.nome, u.cidade, u.estado;

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
    COALESCE(SUM(a.pontuacao), 0) AS pontuacao_total,
    RANK() OVER (
        PARTITION BY u.cidade
        ORDER BY COALESCE(SUM(a.pontuacao), 0) DESC
    ) AS posicao
FROM idade_usuario u
LEFT JOIN atividade a ON a.id_usuario = u.id_usuario
WHERE u.perfil_publico = 1
    AND (u.idade_calculada IS NULL OR u.idade_calculada >= 18)
GROUP BY u.id_usuario, u.nome, u.cidade, u.estado;

CREATE OR REPLACE VIEW vw_ranking_exercicio AS
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
    MIN(a.titulo) AS titulo,
    LOWER(a.titulo) AS titulo_normalizado,
    MAX(a.carga_kg) AS carga_maxima,
    RANK() OVER (
        PARTITION BY LOWER(a.titulo)
        ORDER BY MAX(a.carga_kg) DESC
    ) AS posicao
FROM idade_usuario u
JOIN atividade a ON a.id_usuario = u.id_usuario
WHERE u.perfil_publico = 1
    AND (u.idade_calculada IS NULL OR u.idade_calculada >= 18)
    AND a.tipo = 'musculacao'
    AND a.carga_kg IS NOT NULL
GROUP BY u.id_usuario, u.nome, u.cidade, u.estado, LOWER(a.titulo);
