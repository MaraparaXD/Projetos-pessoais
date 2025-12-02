/*1. Inventário Ativo: Colaboradores e seus Dispositivos Atuais Exibe apenas colaboradores 
que possuem um dispositivo vinculado e dispositivos que têm um dono.*/
SELECT 
    c.NOME AS Colaborador,
    c.MATRICULA,
    d.MARCA AS Dispositivo,
    d.DATA_COMPRA
FROM 
    COLABORADOR c
INNER JOIN 
    DISPOSITIVO d ON c.MATRICULA = d.ID_COLABORADOR;

/*2. Relatório Completo de Chamados Atendidos Lista os chamados, quem abriu e qual técnico atendeu. 
Se um chamado não tiver técnico atribuído ainda, ele não aparecerá nesta lista.*/
SELECT 
    ch.ID AS ID_Chamado,
    c.NOME AS Solicitante,
    ch.PROBLEMA_REPORTADO,
    t.NOME AS Tecnico_Responsavel,
    ch.STATUS_DO_CHAMADO
FROM 
    CHAMADOS ch
INNER JOIN 
    COLABORADOR c ON ch.ID_COLABORADOR_ABRIU = c.MATRICULA
INNER JOIN 
    TECNICO t ON ch.ID_TECNICO = t.ID
ORDER BY 
    ch.DATA_ENTRADA DESC;
/*3. Volume de Chamados por Departamento Mostra quais departamentos estão gerando demandas de TI.*/
SELECT 
    dept.NOME AS Departamento,
    COUNT(ch.ID) AS Total_Chamados
FROM 
    CHAMADOS ch
INNER JOIN 
    COLABORADOR c ON ch.ID_COLABORADOR_ABRIU = c.MATRICULA
INNER JOIN 
    DEPARTAMENTO dept ON c.ID_DEPARTAMENTO = dept.ID
GROUP BY 
    dept.NOME
ORDER BY 
    Total_Chamados DESC;
/*4. Histórico de Uso de Equipamentos Rastreabilidade de quem usou o quê, cruzando as três tabelas principais.*/
SELECT 
    h.ID AS ID_Historico,
    c.NOME AS Colaborador,
    d.MARCA AS Dispositivo,
    h.DATA_INICIO,
    h.DATA_FINAL
FROM 
    HISTORICO_DE_COLABORADOR h
INNER JOIN 
    COLABORADOR c ON h.ID_COLABORADOR = c.MATRICULA
INNER JOIN 
    DISPOSITIVO d ON h.ID_DISPOSITIVO = d.ID;
/*5. Ranking de Atendimentos por Técnico (Apenas quem trabalhou) Conta quantos chamados cada técnico atendeu. 
Técnicos sem chamados são excluídos.*/
SELECT 
    t.NOME AS Tecnico,
    COUNT(ch.ID) AS Chamados_Resolvidos
FROM 
    TECNICO t
INNER JOIN 
    CHAMADOS ch ON t.ID = ch.ID_TECNICO
GROUP BY 
    t.NOME
ORDER BY 
    Chamados_Resolvidos DESC;
/*6.Identificação de Dispositivos Problemáticos Lista apenas os dispositivos que já tiveram pelo menos um chamado aberto registrado.*/
SELECT 
    d.MARCA AS Dispositivo,
    d.ID AS ID_Patrimonio,
    COUNT(ch.ID) AS Qtd_Problemas
FROM 
    DISPOSITIVO d
INNER JOIN 
    CHAMADOS ch ON d.ID = ch.ID_DISPOSITIVO
GROUP BY 
    d.MARCA, d.ID
ORDER BY 
    Qtd_Problemas DESC;
/*7. Monitoramento de Chamados em Aberto Filtra tudo que ainda precisa de atenção imediata.*/
SELECT 
    ID, 
    PROBLEMA_REPORTADO, 
    DATA_ENTRADA 
FROM 
    CHAMADOS 
WHERE 
    STATUS_DO_CHAMADO = 'Aberto';
/*8. Auditoria de Compras (2023) Verifica os dispositivos adquiridos no ano corrente.*/
SELECT 
    ID, 
    MARCA, 
    DATA_COMPRA 
FROM 
    DISPOSITIVO 
WHERE 
    DATA_COMPRA >= '2023-01-01'
ORDER BY 
    DATA_COMPRA DESC;
/*9.Média de Tempo de Resolução (Dias) Cálculo simples de performance baseado nas datas de entrada e saída.*/
SELECT 
    ID,
    PROBLEMA_REPORTADO,
    (data_finalização - DATA_ENTRADA) AS Tempo_Gasto
FROM 
    CHAMADOS
WHERE 
    data_finalização IS NOT NULL;
/*10. Listagem de Colaboradores do RH */
SELECT 
    MATRICULA, 
    NOME, 
    STATUS 
FROM 
    COLABORADOR 
WHERE 
    ID_DEPARTAMENTO = 1;
