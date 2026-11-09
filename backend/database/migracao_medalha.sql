USE fitbattle;

ALTER TABLE compartilhamento
    MODIFY tipo_conteudo ENUM('atividade','meta','desafio','recorde','medalha') NOT NULL,
    ADD COLUMN chave_medalha VARCHAR(40) NULL AFTER id_meta;
