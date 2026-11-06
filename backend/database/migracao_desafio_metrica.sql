-- Rode este script uma única vez. MySQL não aceita ADD COLUMN
-- IF NOT EXISTS, então executá-lo de novo falha com erro 1060
-- (coluna já existe).

USE fitbattle;

ALTER TABLE desafio
    ADD COLUMN tipo_metrica VARCHAR(12) NOT NULL DEFAULT 'treinos' AFTER recompensa_xp,
    ADD COLUMN valor_objetivo DECIMAL(8,2) NOT NULL DEFAULT 1 AFTER tipo_metrica;
