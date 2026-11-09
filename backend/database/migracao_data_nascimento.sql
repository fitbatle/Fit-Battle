USE fitbattle;

ALTER TABLE usuario
    ADD COLUMN data_nascimento DATE NULL AFTER idade;
