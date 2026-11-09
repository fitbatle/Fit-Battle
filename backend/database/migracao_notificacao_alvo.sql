USE fitbattle;

ALTER TABLE notificacao
    ADD COLUMN tipo_alvo VARCHAR(20) NULL AFTER lida,
    ADD COLUMN id_alvo INT NULL AFTER tipo_alvo;
