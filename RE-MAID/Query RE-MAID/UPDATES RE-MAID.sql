--UPDATES gerais 
UPDATE COLABORADOR
SET
	STATUS = 'Ativo'
WHERE
	STATUS = 'Disponivel';

UPDATE DISPOSITIVO
SET
	STATUS = 'Em uso';

WHERE
	STATUS = 'Disponivel';

UPDATE COLABORADOR
SET
	NOME = 'Leticia Silva'
WHERE
	MATRICULA = 'COLAB-008';

UPDATE COLABORADOR
SET
	STATUS = 'ATIVO'
WHERE
	STATUS = 'Ativo'
UPDATE HISTORICO_DE_COLABORADOR
SET
	DATA_FINAL = NULL
WHERE
	ID_COLABORADOR = 'COLAB-001';

UPDATE COLABORADOR
SET
	STATUS = 'INATIVO'
WHERE
	NOME = 'Lucas Neto';

UPDATE HISTORICO_DE_COLABORADOR
SET
	STATUS = 'Disponivel';

UPDATE HISTORICO_DE_COLABORADOR
SET
	STATUS = 'INATIVO'
WHERE
	ID_COLABORADOR = 'COLAB-002';

UPDATE historico_de_colaborador
  SET 
     data_final = '25/11/2025'
  WHERE id_colaborador = 'COLAB-002';


 -- Atualizando as datas de compra para 2023 para garantir consistência com o histórico de chamados


UPDATE dispositivo 
SET data_compra = '2023-03-15' 
WHERE id IN (1, 2, 3);

UPDATE dispositivo 
SET data_compra = '2023-06-20' 
WHERE id IN (4, 5, 6);

UPDATE dispositivo 
SET data_compra = '2023-11-10' 
WHERE id IN (7, 8, 9, 10);
