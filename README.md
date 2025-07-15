# MonitordeAtividade

Monitora o tempo de atividade do usuário. Caso a inatividade exceda o tempo limite definido, um alerta é enviado por e-mail para um ou mais usuários

## Prinicipais funcionalidades

• Monitoramento de Inatividade: Detecta a ausência de movimentos do mouse, cliques ou uso do teclado.

• Alertas por E-mail: Envia um e-mail detalhado com o nome do usuário, nome da máquina e o horário do alerta para múltiplos destinatários.

• Execução em Segundo Plano: Roda de forma totalmente oculta, sendo acessível apenas por um ícone na bandeja do sistema (próximo ao relógio do Windows).

• Pausa para Almoço Configurável: Permite que o usuário defina um intervalo de pausa (ex: horário de almoço), durante o qual o monitoramento é pausado. 
  Inclui uma trava que impede a configuração de pausas superiores a 2 horas.

• Configuração Centralizada: Todas as configurações sensíveis (tempo de inatividade, credenciais de e-mail, destinatários) são gerenciadas através de um arquivo config.json, que não é acessível pela interface do usuário. (Recomenda-se ocultá-lo numa pasta)

• Inicialização Automática: Pode ser facilmente configurado para iniciar junto com o Windows, garantindo que o monitoramento esteja sempre ativo.

• Ícone Personalizável: Permite a personalização tanto do ícone da bandeja do sistema quanto do ícone do arquivo executável (.exe).

## Onde e por quê utilizar

O monitor de atividades é ideal para ambientes onde se é necessário garantir que as estações de trabalho estejam sendo efetivamente utilizadas.

• Permite que gestores identifiquem terminais que estão ligados, mas sem uso, otimizando o consumo de energia e os custos operacionais.

• Oferece uma maneira automatizada de verificar a atividade dos colaboradores, especialmente em regimes de trabalho remoto ou em tarefas que exigem presença constante.

• Ao identificar longos períodos de inatividade, pode servir como um gatilho para políticas de segurança, como o bloqueio automático de sessão (Indisponível nesta versão).

• Elimina a necessidade de supervisão manual, enviando alertas confiáveis e baseados em dados para os responsáveis.

# Requires

pynput: Listeners globais que detectam interações com o mouse e o teclado.

pystray: Cria e gerencia o ícone e o menu na bandeja do sistema.

tkinter: Exibe a janela de configuração da pausa.

smtplib: Conecta-se a um servidor SMTP e envia os e-mails de alerta.

threading: Executa o cronômetro de inatividade em uma thread separada para otimizar a aplicação.
