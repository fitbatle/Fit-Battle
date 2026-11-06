-- Rode este script uma única vez. MySQL não aceita ADD COLUMN
-- IF NOT EXISTS, então executá-lo de novo falha com erro 1060
-- (coluna já existe).

USE fitbattle;

ALTER TABLE usuario
    ADD COLUMN data_nascimento DATE NULL AFTER idade;
