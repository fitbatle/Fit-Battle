USE fitbattle;

ALTER TABLE meta
    ADD COLUMN tipo_metrica ENUM('carga_maxima','frequencia') NULL AFTER tipo,
    ADD COLUMN exercicio VARCHAR(120) NULL AFTER tipo_metrica,
    ADD COLUMN valor_objetivo DECIMAL(8,2) NULL AFTER exercicio,
    ADD COLUMN valor_partida DECIMAL(8,2) NULL AFTER valor_objetivo,
    ADD COLUMN concluida_em DATETIME NULL AFTER status,
    DROP COLUMN progresso;
