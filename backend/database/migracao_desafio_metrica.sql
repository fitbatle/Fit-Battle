USE fitbattle;

ALTER TABLE desafio
    ADD COLUMN tipo_metrica VARCHAR(12) NOT NULL DEFAULT 'treinos' AFTER recompensa_xp,
    ADD COLUMN valor_objetivo DECIMAL(8,2) NOT NULL DEFAULT 1 AFTER tipo_metrica;
