-- Rode este script uma única vez. MySQL não aceita ADD COLUMN
-- IF NOT EXISTS, então executá-lo de novo falha com erro 1060
-- (coluna já existe).

USE fitbattle;

ALTER TABLE notificacao
    ADD COLUMN tipo_alvo VARCHAR(20) NULL AFTER lida,
    ADD COLUMN id_alvo INT NULL AFTER tipo_alvo;
