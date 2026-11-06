-- Rode este script uma única vez. Ele acrescenta o tipo 'medalha' e a coluna
-- chave_medalha à tabela compartilhamento. Executá-lo de novo falha na linha do
-- ADD COLUMN (coluna já existe) com erro 1060.

USE fitbattle;

ALTER TABLE compartilhamento
    MODIFY tipo_conteudo ENUM('atividade','meta','desafio','recorde','medalha') NOT NULL,
    ADD COLUMN chave_medalha VARCHAR(40) NULL AFTER id_meta;
