-- INSERT INTO, inserindo dados nas tabelas do projeto re-maid
INSERT INTO
	DEPARTAMENTO (NOME)
VALUES
	('RH'),
	('ADM'),
	('TI'),
	('Tesouraria'),
	('Vendas'),
	('Logistica');

INSERT INTO
	TECNICO (NOME)
VALUES
	('Carlos Eduardo'),
	('Maria Lucia');

INSERT INTO
	COLABORADOR (MATRICULA, NOME, ID_DEPARTAMENTO)
VALUES
	('COLAB-001', 'Jessica Lívia', 1),
	('COLAB-002', 'Lucas Neto', 1),
	('COLAB-003', 'Felipe Neto', 2),
	('COLAB-004', 'Carlos Eduardo', 3),
	('COLAB-005', 'Luan Ruan', 5),
	('COLAB-006', 'Maria Lucia', 3),
	('COLAB-007', 'João Pedro', 6),
	('COLAB-008', 'Leiticia Silva', 3),
	('COLAB-009', 'Victor Hugo', 4),
	('COLAB-010', 'Tiago Leão', 2);

INSERT INTO
	DISPOSITIVO (MARCA, DATA_COMPRA, ID_COLABORADOR)
VALUES
	(
		'Notebook Lenovo Ideapad 1I',
		'10-05-2025',
		'COLAB-001'
	),
	('PC-I5 10°', '10-01-2025', 'COLAB-002'),
	('PC-I3 13°', '10-01-2025', 'COLAB-003'),
	('PC-I7 13°', '01-01-2025', 'COLAB-004'),
	('Notebook Asus X515', '06-04-2025', 'COLAB-005'),
	('PC-I7 13°', '01-01-2025', 'COLAB-006'),
	(
		'Notebook Lenovo IdeaPad 1',
		'04-04-2025',
		'COLAB-007'
	),
	(
		'Notebook Asus Vivobook GO 15',
		'06-05-2025',
		'COLAB-008'
	),
	(
		'Notebook Apple MacBook MLY23LE/A',
		'05-03-2025',
		'COLAB-009'
	),
	('PC-I9 10°', '02-02-2025', 'COLAB-010');

INSERT INTO
	CHAMADOS (
		PROBLEMA_REPORTADO,
		ID_DISPOSITIVO,
		ID_COLABORADOR_ABRIU,
		ID_TECNICO
	)
VALUES
	(
		'Computador muito lento, demora para abrir qualquer coisa.',
		1,
		'COLAB-001',
		2
	),
	(
		'Meu computador não quer conectar a impressora.',
		4,
		'COLAB-004',
		1
	),
	('Computador não quer ligar.', 2, 'COLAB-002', 1);


-- Inserindo dados na tabela nova

INSERT INTO
	HISTORICO_DE_COLABORADOR (
		ID_COLABORADOR,
		ID_DISPOSITIVO,
		DATA_INICIO,
		DATA_FINAL
	)
VALUES
	('COLAB-001', 1, '2025-05-10', NULL),
	('COLAB-002', 2, '2025-01-10', NULL),
	('COLAB-003', 3, '2025-01-10', NULL),
	('COLAB-004', 4, '2025-01-01', NULL),
	('COLAB-005', 5, '2025-04-06', NULL),
	('COLAB-006', 6, '2025-01-01', NULL),
	('COLAB-007', 7, '2025-04-04', NULL),
	('COLAB-008', 8, '2025-05-06', NULL),
	('COLAB-009', 9, '2025-03-05', NULL),
	('COLAB-010', 10, '2025-02-02', NULL);

-- Inserindo mais dados na tabela chamados
INSERT INTO chamados (problema_reportado, status_do_chamado, data_entrada, data_finalizacao, id_dispositivo, id_tecnico, id_colaborador_abriu) VALUES
-- Chamados de Setembro (Antigos e Resolvidos)
('Mouse parou de funcionar', 'Fechado', '2025-09-01 08:15:00', '2025-09-01 09:30:00', 1, 1, 'COLAB-001'),
('Impressora atolando papel', 'Fechado', '2025-09-02 10:00:00', '2025-09-02 14:00:00', 4, 2, 'COLAB-004'),
('Não consigo acessar a pasta de rede', 'Fechado', '2025-09-03 13:20:00', '2025-09-03 13:50:00', 2, 1, 'COLAB-002'),
('Monitor piscando intermitente', 'Fechado', '2025-09-05 09:00:00', '2025-09-06 10:00:00', 3, 2, 'COLAB-003'),
('Instalação do Adobe Reader', 'Fechado', '2025-09-08 11:00:00', '2025-09-08 11:45:00', 5, 1, 'COLAB-005'),
('Erro ao abrir o Excel', 'Fechado', '2025-09-10 14:30:00', '2025-09-10 15:15:00', 6, 2, 'COLAB-006'),
('Computador travando muito', 'Fechado', '2025-09-12 08:00:00', '2025-09-12 16:00:00', 7, 1, 'COLAB-007'),
('Teclado numérico com defeito', 'Fechado', '2025-09-15 09:45:00', '2025-09-15 10:30:00', 8, 2, 'COLAB-008'),
('Sem acesso à internet', 'Fechado', '2025-09-16 10:00:00', '2025-09-16 11:00:00', 9, 1, 'COLAB-009'),
('Senha do Windows bloqueada', 'Fechado', '2025-09-18 07:50:00', '2025-09-18 08:10:00', 10, 2, 'COLAB-010'),

-- Chamados de Outubro
('Preciso de permissão na pasta RH', 'Fechado', '2025-10-02 14:00:00', '2025-10-02 14:20:00', 1, 2, 'COLAB-001'),
('PC reiniciando sozinho', 'Fechado', '2025-10-05 09:30:00', '2025-10-06 10:00:00', 2, 1, 'COLAB-002'),
('Cabo de rede quebrado', 'Fechado', '2025-10-08 11:15:00', '2025-10-08 11:45:00', 3, 2, 'COLAB-003'),
('Outlook não sincroniza e-mails', 'Fechado', '2025-10-10 15:00:00', '2025-10-10 16:30:00', 4, 1, 'COLAB-004'),
('Solicitação de fone de ouvido novo', 'Fechado', '2025-10-12 10:00:00', '2025-10-12 10:15:00', 5, 2, 'COLAB-005'),
('Atualização do Windows falhou', 'Fechado', '2025-10-15 08:45:00', '2025-10-15 12:00:00', 6, 1, 'COLAB-006'),
('Vírus detectado pelo antivírus', 'Fechado', '2025-10-18 13:00:00', '2025-10-18 14:30:00', 7, 2, 'COLAB-007'),
('Tela azul ao ligar', 'Fechado', '2025-10-20 08:30:00', '2025-10-21 09:00:00', 8, 1, 'COLAB-008'),
('Mousepad do notebook não funciona', 'Fechado', '2025-10-25 11:00:00', '2025-10-25 11:30:00', 9, 2, 'COLAB-009'),
('Configurar assinatura de e-mail', 'Fechado', '2025-10-28 16:00:00', '2025-10-28 16:15:00', 10, 1, 'COLAB-010'),

-- Chamados de Novembro (Mistura de Fechados e Abertos para o Dashboard ficar legal)
('Lentidão ao acessar o sistema ERP', 'Em andamento', '2025-11-01 09:00:00', NULL, 1, 1, 'COLAB-001'),
('Troca de toner da impressora', 'Fechado', '2025-11-03 10:30:00', '2025-11-03 11:00:00', 4, 2, 'COLAB-004'),
('Notebook esquentando muito', 'Aberto', '2025-11-05 14:00:00', NULL, 2, 1, 'COLAB-002'),
('Instalar VPN para acesso remoto', 'Fechado', '2025-11-10 09:00:00', '2025-11-10 10:30:00', 3, 2, 'COLAB-003'),
('Monitor secundário não dá vídeo', 'Em andamento', '2025-11-15 13:00:00', NULL, 5, 1, 'COLAB-005'),
('Teclas A e S falhando', 'Aberto', '2025-11-18 08:30:00', NULL, 6, 2, 'COLAB-006'),
('Solicitação de novo mouse', 'Fechado', '2025-11-20 15:00:00', '2025-11-20 15:10:00', 7, 1, 'COLAB-007'),
('Wi-Fi caindo constantemente', 'Aberto', '2025-11-22 10:00:00', NULL, 8, 2, 'COLAB-008'),
('Erro de licença no Office', 'Fechado', '2025-11-24 11:30:00', '2025-11-24 12:00:00', 9, 1, 'COLAB-009'),
('Computador fazendo barulho alto', 'Aberto', '2025-11-24 16:00:00', NULL, 10, 2, 'COLAB-010');

-- Mais dados para a tabela chamados

INSERT INTO chamados (problema_reportado, status_do_chamado, data_entrada, data_finalização, id_dispositivo, id_tecnico, id_colaborador_abriu) VALUES

-- --- ANO DE 2024 (Histórico Antigo) ---
('Teclado numérico parou de funcionar', 'Fechado', '2024-01-10 09:00:00', '2024-01-10 10:30:00', 1, 1, 'COLAB-001'),
('Erro ao conectar na VPN', 'Fechado', '2024-02-15 14:00:00', '2024-02-15 15:00:00', 2, 2, 'COLAB-002'),
('Solicitação de instalação do WinRAR', 'Fechado', '2024-03-05 11:00:00', '2024-03-05 11:20:00', 3, 1, 'COLAB-003'),
('Monitor piscando intermitente', 'Fechado', '2024-03-20 08:30:00', '2024-03-21 09:00:00', 4, 2, 'COLAB-004'),
('Impressora não puxa papel', 'Fechado', '2024-04-12 16:00:00', '2024-04-13 10:00:00', 5, 1, 'COLAB-005'),
('PC lento após atualização', 'Fechado', '2024-05-08 09:00:00', '2024-05-08 12:00:00', 6, 2, 'COLAB-006'),
('Não consigo acessar o servidor de arquivos', 'Fechado', '2024-06-18 13:00:00', '2024-06-18 13:45:00', 7, 1, 'COLAB-007'),
('Mouse sem fio com pilha fraca', 'Fechado', '2024-07-02 10:00:00', '2024-07-02 10:15:00', 8, 2, 'COLAB-008'),
('Erro de licença expirada no Office', 'Fechado', '2024-08-14 08:00:00', '2024-08-14 09:00:00', 9, 1, 'COLAB-009'),
('Barulho estranho no cooler', 'Fechado', '2024-09-10 15:30:00', '2024-09-11 10:00:00', 10, 2, 'COLAB-010'),
('Internet caindo toda hora', 'Fechado', '2024-10-05 11:00:00', '2024-10-05 14:00:00', 1, 1, 'COLAB-001'),
('Solicitação de formatação', 'Fechado', '2024-11-20 09:00:00', '2024-11-21 17:00:00', 2, 2, 'COLAB-002'),
('Tela azul (BSOD) recorrente', 'Fechado', '2024-12-15 08:30:00', '2024-12-16 09:00:00', 3, 1, 'COLAB-003'),

-- --- ANO DE 2025 (Janeiro a Outubro) ---
('Esqueci minha senha do Windows', 'Fechado', '2025-01-08 07:50:00', '2025-01-08 08:00:00', 4, 2, 'COLAB-004'),
('Cabo de rede com mau contato', 'Fechado', '2025-02-14 10:30:00', '2025-02-14 11:00:00', 5, 1, 'COLAB-005'),
('Outlook não envia anexos grandes', 'Fechado', '2025-03-22 14:00:00', '2025-03-22 15:30:00', 6, 2, 'COLAB-006'),
('Solicitação de segundo monitor', 'Fechado', '2025-04-10 09:00:00', '2025-04-12 10:00:00', 7, 1, 'COLAB-007'),
('Vírus detectado no pendrive', 'Fechado', '2025-05-18 16:00:00', '2025-05-18 16:30:00', 8, 2, 'COLAB-008'),
('Webcam não funciona no Teams', 'Fechado', '2025-06-25 09:30:00', '2025-06-25 10:00:00', 9, 1, 'COLAB-009'),
('Notebook esquentando muito', 'Fechado', '2025-07-30 11:00:00', '2025-07-30 15:00:00', 10, 2, 'COLAB-010'),
('Erro ao imprimir PDF', 'Fechado', '2025-08-12 13:00:00', '2025-08-12 13:20:00', 1, 1, 'COLAB-001'),
('Teclas A e S falhando', 'Fechado', '2025-09-05 08:00:00', '2025-09-06 12:00:00', 2, 2, 'COLAB-002'),
('Lentidão extrema no sistema ERP', 'Fechado', '2025-10-15 14:00:00', '2025-10-15 16:00:00', 3, 1, 'COLAB-003'),

-- --- NOVEMBRO DE 2025 (Recentes e Pendentes) ---
('HD fazendo barulho', 'Fechado', '2025-11-01 09:00:00', '2025-11-02 10:00:00', 4, 2, 'COLAB-004'),
('Solicitação de mousepad novo', 'Fechado', '2025-11-05 10:00:00', '2025-11-05 10:10:00', 5, 1, 'COLAB-005'),
('Não consigo acessar o Wi-Fi', 'Em andamento', '2025-11-10 08:30:00', NULL, 6, 2, 'COLAB-006'),
('Monitor não liga', 'Aberto', '2025-11-20 09:00:00', NULL, 7, 1, 'COLAB-007'),
('Erro ao salvar arquivos no Excel', 'Em andamento', '2025-11-22 15:00:00', NULL, 8, 2, 'COLAB-008'),
('Computador reiniciando sozinho', 'Aberto', '2025-11-24 11:00:00', NULL, 9, 1, 'COLAB-009'),
('Impressora sem tinta colorida', 'Aberto', '2025-11-25 08:00:00', NULL, 10, 2, 'COLAB-010');