# Documento de Requisitos Funcionais do Projeto Delta

Este documento tem como objetivo registrar e organizar os requisitos funcionais do Projeto Delta, descrevendo as principais funcionalidades e comportamentos que o sistema deve oferecer aos usuários e aos demais componentes envolvidos. Os requisitos apresentados servem como base para o desenvolvimento, validação e acompanhamento das funcionalidades do sistema, garantindo alinhamento entre as necessidades do projeto e sua implementação.

RF = Requisito Funcional

## RF - Autenticação e Gerenciamento de Usuários
- RF01 -> O sistema deve permitir que novos usuários realizem seu cadastro, fornecendo as informações pessoais necessárias.
- RF02 -> O sistema deve permitir que usuários cadastrados realizem login utilizando suas credenciais.
- RF03 -> O sistema deve validar as informações fornecidas durante o cadastro e informar ao usuário quando houver dados inválidos.
- RF04 -> O sistema deve permitir que usuários autenticados encerrem sua sessão.
- RF05 -> O sistema deve permitir que o usuário consulte suas informações de perfil.
- RF06 -> O sistema deve permitir que o usuário altere suas informações de perfil.

## RF - Monitoramento do Consumo de Água
- RF07 -> O sistema deve receber automaticamente os dados de consumo de água enviados pelos dispositivos de monitoramento.
- RF08 -> O sistema deve registrar as medições recebidas, associando-as ao dispositivo responsável e ao momento da coleta.
- RF09 -> O sistema deve calcular o volume de água consumido a partir das medições recebidas.
- RF10 -> O sistema deve permitir que o usuário visualize seu consumo de água acumulado.
- RF11 -> O sistema deve permitir que o usuário consulte seu histórico de consumo de água.
- RF12 -> O sistema deve permitir que o usuário visualize informações sobre a vazão de água registrada pelos dispositivos.
- RF13 -> O sistema deve apresentar indicadores e gráficos relacionados ao consumo de água do usuário.
- RF14 -> O sistema deve permitir a consulta dos dados de consumo por períodos determinados.

## RF - Detecção de vazamentos e alertas
- RF15 -> O sistema deve analisar os dados de consumo para identificar padrões que indiquem possíveis vazamentos.
- RF16 -> O sistema deve identificar períodos de consumo contínuo ou anormal que possam representar desperdício de água.
- RF17 -> O sistema deve gerar alertas quando identificar indícios de vazamento.
- RF18 -> O sistema deve permitir que o usuário consulte os alertas de possíveis vazamentos identificados.
- RF19 -> O sistema deve enviar notificações ao usuário sobre situações relevantes relacionadas ao consumo ou a possíveis vazamentos.

## RF - Inteligência Artificial e Sistema Multiagente
- RF20 -> O sistema deve permitir que o usuário interaja com um chatbot para realizar consultas relacionadas ao consumo de água.
- RF21 -> O sistema deve interpretar as perguntas do usuário e encaminhá-las ao módulo especializado correspondente.
- RF22 -> O sistema deve permitir que o usuário solicite análises sobre seu histórico de consumo de água por meio do chatbot.
- RF23 -> O sistema deve permitir que o usuário consulte possíveis vazamentos identificados por meio do chatbot.
- RF24 -> O sistema deve gerar previsões de consumo de água com base nos dados históricos disponíveis.
- RF25 -> O sistema deve permitir que o usuário consulte previsões de consumo por meio do chatbot.
- RF26 -> O sistema deve consultar informações de uma base de conhecimento para responder a perguntas relacionadas ao uso consciente da água.
- RF27 -> O sistema deve verificar as respostas produzidas pelos agentes antes de apresentá-las ao usuário, conforme critérios de validação definidos.
- RF28 -> O sistema deve manter o contexto da conversa durante uma sessão de interação com o chatbot.

## RF - Funcionalidades Adicionais
- RF29 -> O sistema deve permitir que o usuário associe dispositivos de monitoramento a um imóvel.
- RF30 -> O sistema deve permitir que o usuário defina metas de consumo de água.
- RF31 -> O sistema deve acompanhar o consumo em relação às metas estabelecidas.
- RF32 -> O sistema deve estimar o valor financeiro do consumo de água com base em tarifas configuradas.
- RF33 -> O sistema deve permitir que o usuário consulte recomendações para reduzir o desperdício de água.