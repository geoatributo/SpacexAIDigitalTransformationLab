# Golden Set Completo de Validação - SGQ GeoAtributo

Este documento contém o "Golden Set" consolidado de 50 perguntas e respostas para validação do sistema de IA, estruturado em 10 lotes de 5 questões cada. Todas as respostas baseiam-se estritamente nas fontes oficiais do SGQ selecionadas: "Normas_e_Procedimentos_v52.pdf", "Anexo_I_classificacao_decimal.pdf" e "anexo_IX_gestao_palavras_passe.pdf".

---

## Lote 1 (Itens 1 a 5)

[Item 1]

**Questão:** Quais são as limitações de tamanho estabelecidas para download ou upload direto de ficheiros através da VPN e que ferramentas alternativas são propostas caso esse limite seja excedido?

**Resposta:** As cópias de download ou upload direto de ficheiros através da VPN (entre o computador pessoal e o servidor) **só devem ser efetuadas para ficheiros ou conjuntos de ficheiros de dimensão inferior a 25 MB**. Para ficheiros ou conjuntos de ficheiros de **dimensão superior a 25 MB**, o manual propõe o recurso às plataformas **WeTransfer** ou **Google Drive**.

**Rastreabilidade:** Documento: "Normas_e_Procedimentos_v52.pdf" | Extrato: "As cópias (download / upload) de ficheiros através da VPN, isto é, diretamente"

---

[Item 2]

**Questão:** No acesso ao servidor de ficheiros (SAMBA), qual é o limite de tentativas de login incorretas permitido num determinado espaço de tempo e qual o correspondente período de bloqueio?

**Resposta:** No acesso ao servidor, existe o **número máximo de quatro tentativas** de login incorretas no espaço de um minuto, ficando o utilizador subsequentemente **bloqueado durante 30 minutos**.

**Rastreabilidade:** Documento: "Normas_e_Procedimentos_v52.pdf" | Extrato: "As credenciais são atribuídas a cada colaborador, existindo o número máximo de quatro"

---

[Item 3]

**Questão:** No controlo de versões, que carateres e em que número exato devem ser adicionados aos nomes dos ficheiros desatualizados guardados na pasta "old" para registar quando se tornaram obsoletos?

**Resposta:** Aos ficheiros gravados na pasta "old" deverão ser adicionados, ao final do nome do ficheiro, **exatamente 11 carateres** para registar a data em que essa versão de tornou desatualizada (por exemplo, `_2012_05_15`).

**Rastreabilidade:** Documento: "Normas_e_Procedimentos_v52.pdf" | Extrato: "Aos ficheiros gravados na pasta old deverá ser acrescentado, ao nome do ficheiro,"

---

[Item 4]

**Questão:** De acordo com as regras de padronização de registo de dados da GeoAtributo, qual é o formato numérico obrigatório para o registo de horas?

**Resposta:** No registo de horas, deve ser usado obrigatoriamente o **formato numérico decimal com duas casas** (por exemplo, registando 8,50 para 8 horas e 30 minutos, em vez de 8h30 ou 08:30).

**Rastreabilidade:** Documento: "Normas_e_Procedimentos_v52.pdf" | Extrato: "Registo de Horas: Deve ser usado o formato numérico decimal com duas casas."

---

[Item 5]

**Questão:** Quais são as regras obrigatórias de segurança e composição que os colaboradores devem respeitar ao gerar as suas palavras-passe de acesso?

**Resposta:** Os colaboradores não devem utilizar informação pessoal simples para gerar a palavra-passe. Devem utilizar uma **sequência de letras e números aleatórios com no mínimo 9 caracteres, contendo pelo menos 3 números ou letras, e sem repetir qualquer carácter**.

**Rastreabilidade:** Documento: "anexo_IX_gestao_palavras_passe.pdf" | Extrato: "Usar sequência de letras e números aleatórios (no mínimo 9 caracteres, com pelo"

---

## Lote 2 (Itens 6 a 10)

[Item 6]

**Questão:** Quais são as regras e as áreas organizativas sem qualquer direito a exceção relativamente ao uso de formatos de ficheiros no Google Drive da GeoAtributo?

**Resposta:** Todos os documentos produzidos e guardados no Google Drive devem utilizar obrigatoriamente e exclusivamente o formato nativo do Google, excluindo-se o uso de formatos associados ao Microsoft Office (salvo raras exceções de ordem estritamente técnica devidamente justificadas). Para as áreas de Gestão da Certificação, Administrativa e Comercial, não existe qualquer tipo de exceção aplicável a esta regra.

**Rastreabilidade:** Documento: "Normas_e_Procedimentos_v52.pdf" | Extrato: "Todos os documentos produzidos e guardados no Google Drive só podem utilizar o"

---

[Item 7]

**Questão:** Qual é a regra geral estrutural definida para a atribuição de nomenclatura às pastas de informação de base e o que significam os códigos "G", "D" e "R"?

**Resposta:** A nomenclatura das pastas de informação de base deve seguir rigorosamente a estrutura `codigo-CDU_Codigo-tipo_tema_fonte`. O código tipo correspondente carateriza a tipologia de informação através das seguintes letras: **G** para informação georreferenciada e cartografia; **D** para dados estatísticos, outros dados, imagens e fotografias; e **R** para documentos de referência.

**Rastreabilidade:** Documento: "Normas_e_Procedimentos_v52.pdf" | Extrato: "A regra para a atribuição de nome a estas diretorias é: codigo-CDU_Codigo-tipo_tema"

---

[Item 8]

**Questão:** Qual é o prazo mínimo regulamentar determinado para a conservação digital e disponibilidade de documentos registados no âmbito do Modelo 202 ou relativos a entregas formais?

**Resposta:** O período mínimo para manutenção e disponibilidade do arquivo em formato digital é de **10 anos** a contar da data de criação do respetivo documento ou ficheiro.

**Rastreabilidade:** Documento: "Normas_e_Procedimentos_v52.pdf" | Extrato: "O período mínimo para manutenção e disponibilidade do arquivo é de 10 anos a"

---

[Item 9]

**Questão:** Qual o software gestor de passwords recomendado para uso geral na GeoAtributo e que norma de segurança deve ser observada para a guarda física de chaves digitais com suporte USB?

**Resposta:** O gestor de palavras-passe recomendado na GeoAtributo é o **KeePass**. Quanto ao suporte físico de chaves digitais USB (ou outros formatos), este deve ser mantido sob controlo rigoroso, sendo obrigatoriamente guardado em local de acesso restrito, tal como um **cofre** ou, no mínimo, um **bloco de gavetas fechado com a respetiva chave**.

**Rastreabilidade:** Documento: "anexo_IX_gestao_palavras_passe.pdf" | Extrato: "O gestor de palavras passe recomendado pela GeoAtributo é o \"keePass\" (https://keepass.info/)."

---

[Item 10]

**Questão:** Perante a ausência de metadados na informação de base fornecida por um cliente, que prazo máximo deve ser estabelecido por escrito pela GeoAtributo para que o cliente envie os respetivos dados em falta?

**Resposta:** A GeoAtributo deve realizar uma comunicação por escrito ao cliente, notificando-o da ocorrência e solicitando formalmente que envie os metadados em falta num **período máximo de 5 dias úteis** (ou, em alternativa, que o cliente indique expressamente o período de que necessita para proceder à compilação).

**Rastreabilidade:** Documento: "Normas_e_Procedimentos_v52.pdf" | Extrato: "Em caso de ausência de metadados, deverá ser realizada uma comunicação ao cliente a"

---

## Lote 3 (Itens 11 a 15)

[Item 11]

**Questão:** Qual é o prazo máximo estabelecido para responder a qualquer correio eletrónico (e-mail) recebido e qual o significado prático de "e-mail respondido" no âmbito do SGQ?

**Resposta:** Qualquer e-mail deve ser respondido no **tempo máximo de 48 horas corridas**. Entende-se como "respondido" o envio de, pelo menos, uma resposta ao remetente a **acusar a receção** e a dar conta de que o tratamento do seu conteúdo ou da solicitação será efetuada oportunamente.

**Rastreabilidade:** Documento: "Normas_e_Procedimentos_v52.pdf" | Extrato: "Qualquer email deve ser respondido no tempo máximo de 48 horas corridas, devendo"

---

[Item 12]

**Questão:** Qual é o procedimento de segurança e a localização exata para o arquivo físico e digital do repositório de palavras-passe de segurança do tipo 2 (Administração) e tipo 3 (Administrativo e Comercial)?

**Resposta:** O responsável nomeado criará um ficheiro KeePass com todas as palavras-chave do repositório e gravá-lo-á numa **pen drive que ficará guardada no cofre da garagem**. Por sua vez, a palavra-chave mestre do próprio ficheiro KeePass ficará guardada dentro de um **envelope lacrado no cofre do escritório**.

**Rastreabilidade:** Documento: "Normas_e_Procedimentos_v52.pdf" | Extrato: "Para os tipos 2 e 3, será criado um repositório de passwords, cuja atualização deverá ser"

---

[Item 13]

**Questão:** Na nomenclatura de pastas de informação de base, qual a estrutura de denominação obrigatória a adotar e em que sistema normativo se baseiam os primeiros dois dígitos da diretoria?

**Resposta:** A regra estabelecida para a atribuição de nome a estas diretorias é: **`codigo-CDU_Codigo-tipo_tema_fonte`**, sendo que os primeiros dois dígitos corresponderão à **CDU (Classificação Decimal Universal)** para aquele tipo de informação.

**Rastreabilidade:** Documento: "Normas_e_Procedimentos_v52.pdf" | Extrato: "A regra para a atribuição de nome a estas diretorias é: codigo-CDU_Codigo-tipo_tema"

---

[Item 14]

**Questão:** No sistema de Classificação Decimal Universal (CDU) adotado no SGQ, a que classe de assunto ou área temática específica corresponde o código numérico inicial "71"?

**Resposta:** O código numérico "71" corresponde a **Planeamento Regional e Urbano. Paisagens, Jardins, etc.**

**Rastreabilidade:** Documento: "Anexo_I_classificacao_decimal.pdf" | Extrato: "71 Planeamento Regional e Urbano. Paisagens, Jardins, etc."

---

[Item 15]

**Questão:** Aquando do processo de saída de um colaborador (offboarding), quais são os prazos exatos definidos para desativar o e-mail institucional e para alterar ou revogar as passwords comuns da empresa a que ele teve acesso?

**Resposta:** O e-mail institucional (e contas associadas como Wrike e VPN) deve ser desativado no **primeiro dia útil após a saída do colaborador**. Todas as palavras-passe comuns da empresa a que o colaborador teve acesso (como WeTransfer, servidor ou e-mail comum) devem ser alteradas e/ou revogadas num **prazo máximo de 5 dias úteis após a saída**.

**Rastreabilidade:** Documento: "Normas_e_Procedimentos_v52.pdf" | Extrato: "No primeiro dia útil após a saída do colaborador, deverá ser desativado o seu"

---

## Lote 4 (Itens 16 a 20)

[Item 16]

**Questão:** Quais são os três requisitos cumulativos obrigatórios para propor um desvio planeado a um procedimento padrão estabelecido no manual da GeoAtributo?

**Resposta:** Os três requisitos cumulativos obrigatórios são: **Fundamentação Crítica** (a proposta de desvio deve ser claramente fundamentada, demonstrando inequivocamente como a abordagem alternativa gera uma vantagem para a organização, para o projeto ou para o cliente); **Documentação e Registo** (a proposta, a sua fundamentação e a decisão final devem ser registadas formalmente através do modelo 337 "Registo de Desvio de Procedimento"); e **Aprovação Formal** (o desvio só pode ser implementado após aprovação explícita do Gestor e/ou Coordenador de Projeto).

**Rastreabilidade:** Documento: "Normas_e_Procedimentos_v52.pdf" | Extrato: "Um colaborador pode propor não seguir uma norma num caso concreto, desde que"

---

[Item 17]

**Questão:** Qual é o prazo de antecedência mínima obrigatório para uma gestora de projeto comunicar ao coordenador, por escrito, a sua ausência planeada por motivo de férias?

**Resposta:** A gestora de projeto deve comunicar a sua ausência por escrito à coordenação de projeto com a antecedência mínima de **5 dias úteis**.

**Rastreabilidade:** Documento: "Normas_e_Procedimentos_v52.pdf" | Extrato: "Coordenação de projeto: A gestora deverá comunicar ao coordenador de projeto, por escrito,"

---

[Item 18]

**Questão:** Em que situações ou condições é obrigatório utilizar o modelo de registo de notas associado ao agendamento de uma reunião interna de equipa no calendário da Google?

**Resposta:** O preenchimento do registo de notas é obrigatório sempre que a reunião ou sessão em causa tenha associado um **dispêndio de pelo menos 15 minutos** e/ou sempre que o assunto ou assuntos a abordar possam **influenciar estruturalmente o andamento dos trabalhos do projeto**.

**Rastreabilidade:** Documento: "Normas_e_Procedimentos_v52.pdf" | Extrato: "Deverá ser preenchida sempre que a reunião / sessão em causa tenha associado um dispêndio"

---

[Item 19]

**Questão:** Com que antecedência mínima deve ser iniciada a submissão de uma proposta comercial na plataforma eletrónica de contratação pública?

**Resposta:** A submissão da proposta na plataforma eletrónica de contratação pública deve ser iniciada obrigatoriamente **24 horas antes do final do prazo** fixado para a respetiva submissão.

**Rastreabilidade:** Documento: "Normas_e_Procedimentos_v52.pdf" | Extrato: "A submissão da proposta na plataforma eletrónica deve ser iniciada 24h antes do"

---

[Item 20]

**Questão:** Ao fim do prazo de validade de uma proposta comercial, qual o procedimento obrigatório que a GeoAtributo deve adotar para aferir o interesse do cliente?

**Resposta:** O cliente deve ser obrigatoriamente **contactado e questionado sobre se pretende a emissão (atualizada) da proposta ou se deixou de ter interesse**, de modo a garantir que todos os processos ativos de propostas tenham uma avaliação de interesse por um período não superior a **6 meses**.

**Rastreabilidade:** Documento: "Normas_e_Procedimentos_v52.pdf" | Extrato: "Todas as propostas e inclusive a simples apresentação de preço obriga a clarificação"

---

## Lote 5 (Itens 21 a 25)

[Item 21]

**Questão:** No caso de ausência planeada por motivo de férias de uma gestora de projeto, que procedimentos de notificação devem ser aplicados por escrito aos clientes com projetos em curso?

**Resposta:** Os clientes com projetos em curso devem ser notificados da ausência da gestora por escrito, devendo ser indicado um contacto alternativo ou a confirmação de receção das comunicações no contacto habitual (tendo em conta o procedimento de encaminhamento de e-mail para a área administrativa). Adicionalmente, deve ser programada uma resposta de e-mail automática para o período de ausência.

**Rastreabilidade:** Documento: "Normas_e_Procedimentos_v52.pdf" | Extrato: "Clientes: Também os clientes com projetos em curso deverão ser notificados da ausência da"

---

[Item 22]

**Questão:** Qual o procedimento sequencial de três passos estabelecido para o colaborador que não tenha tarefas programadas e apresente disponibilidade no seu cronograma?

**Resposta:** O colaborador deve adotar as seguintes ações: 1. Informar, via e-mail, que se encontra sem tarefas atribuídas/programadas, sendo a comunicação enviada para o coordenador com o conhecimento de todas as gestoras; 2. Dirigir-se ao coordenador (sempre que este esteja disponível) e questionar a possibilidade de abraçar tarefas que possam estar fora do âmbito direto dos projetos; 3. Proceder à atualização de competências/conhecimentos, nomeadamente através de autoformação, enquanto aguarda a atribuição de novas tarefas.

**Rastreabilidade:** Documento: "Normas_e_Procedimentos_v52.pdf" | Extrato: "Sempre que o colaborador não tenha tarefas programadas e tenha disponibilidade no seu cronograma"

---

[Item 23]

**Questão:** Quais são as regras gerais do SGQ relativamente ao formato de compactação obrigatório e aos canais de envio a utilizar para disponibilizar ficheiros via web aos clientes, em função do tamanho dos dados?

**Resposta:** Qualquer conjunto de dados que seja enviado para o cliente e necessite de ser compactado deve sê-lo **apenas no formato .ZIP**, não sendo admissível o envio noutro formato. Relativamente ao meio de envio, se o tamanho do ficheiro ou conjunto de ficheiros for **igual ou superior a 5 MB**, o envio deve ser efetuado obrigatoriamente através de uma plataforma de disponibilização de ficheiros na web (como o WeTransfer). Se o tamanho total for **inferior a 5 MB**, o técnico pode optar por efetuar o envio em anexo no e-mail ou via plataforma web.

**Rastreabilidade:** Documento: "Normas_e_Procedimentos_v52.pdf" | Extrato: "Independentemente do programa usado no processo de compactação de ficheiros, qualquer conjunto de"

---

[Item 24]

**Questão:** Qual é a regra obrigatória para a inclusão do coordenador de projeto nas comunicações eletrónicas relevantes e qual o impacto administrativo dessa inclusão na ação do coordenador?

**Resposta:** Todos os e-mails com conteúdo relevante, não só da área de projeto, mas também das áreas administrativa e comercial, devem incluir obrigatoriamente o contacto do coordenador em **Cc ou Bcc**. Contudo, a inclusão deste não determina a necessidade de resposta ou ação imediata por parte do coordenador, a menos que especificado de outra forma.

**Rastreabilidade:** Documento: "Normas_e_Procedimentos_v52.pdf" | Extrato: "Todos os e-mails com conteúdo relevante, não só da área de projeto, mas"

---

[Item 25]

**Questão:** No âmbito da segurança informática dos postos de trabalho da GeoAtributo, qual é o tempo de inatividade configurado para o bloqueio automático do ecrã e qual a obrigação direta do colaborador ao ausentar-se do seu computador?

**Resposta:** Todos os computadores estão configurados para bloquear automaticamente após **15 minutos de inatividade**. Adicionalmente, todos os colaboradores têm a obrigação de efetuar o bloqueio manual do ecrã sempre que se ausentem do seu posto de trabalho de tal forma que não consigam controlar o seu acesso, mesmo que por um período de tempo inferior a 15 minutos.

**Rastreabilidade:** Documento: "Normas_e_Procedimentos_v52.pdf" | Extrato: "De forma a evitar acessos indevidos, todos os computadores estão configurados para bloquearem"

---

## Lote 6 (Itens 26 a 30)

[Item 26]

**Questão:** Quais são as regras gerais e as respetivas estruturas a adotar para a nomenclatura de ficheiros/relatórios gerais e para os que têm por base um modelo do SGQ, e que formatos de ficheiro estão excluídos dessa obrigatoriedade?

**Resposta:** A regra geral para ficheiros e relatórios (tipicamente .doc e .pdf) é **`descritor_n-de-documento-ou-ordem_versão`** (o nome deve possuir uma descrição e o respetivo número de versão). Se o ficheiro tiver por base um modelo do SGQ, aplica-se a estrutura **`codigo-do-modelo_descritor_n-de-documento-ou-ordem`**. Estão excluídos desta obrigatoriedade de denominação outros formatos de ficheiro (como **.shp, .xls, .dwg**, etc.) ou documentos a entregar ao cliente com designação previamente definida ou exigida pelo próprio.

**Rastreabilidade:** Documento: "Normas_e_Procedimentos_v52.pdf" | Extrato: "Regra geral a aplicar: descritor_n-de-documento-ou-ordem_versão - Os ficheiros deverão"

---

[Item 27]

**Questão:** Como funciona o sistema de codificação de versões de quatro algarismos para os documentos de projeto da GeoAtributo, indicando como se processam as alterações internas e as submissões ao cliente?

**Resposta:** A terminação das versões possui quatro algarismos separados por `_` (ex.: `V00_01`). As sucessivas alterações internas passam a atualizar a versão nos **dois últimos algarismos** (ex.: `V00_01` passa a `V00_02`). Quando o documento/peça é submetido a avaliação (entregue ao cliente), a versão é alterada nos **dois primeiros algarismos** (ex.: se na última edição interna constar `V00_03`, a versão entregue ao cliente passa a ser `V01`). As alterações internas subsequentes sobre este documento já entregue atualizam novamente os dois últimos algarismos (ex.: de `V01` para `V01_01`), e a nova entrega ao cliente atualiza os dois primeiros (ex.: `V02`).

**Rastreabilidade:** Documento: "Normas_e_Procedimentos_v52.pdf" | Extrato: "• A terminação das versões tem quatro algarismos separadaos por"

---

[Item 28]

**Questão:** Quais as regras definidas na política de "Mesa Limpa" da GeoAtributo e qual o destino obrigatório de qualquer documentação confidencial impressa em papel após o seu uso?

**Resposta:** A política de "Mesa Limpa" estipula que, sempre que os colaboradores se ausentem do seu posto de trabalho, **nenhuma informação confidencial deve ser deixada à vista em cima da mesa** (cadernos abertos, notas, documentos impressos, etc.). No fim do dia, os postos devem estar arrumados e os documentos sensíveis guardados em armários/prateleiras. Toda a documentação impressa em papel deve ser **digitalizada após o uso** (caso o conteúdo seja relevante) para arquivo digital, e o documento físico original deve ser **destruído obrigatoriamente na trituradora**.

**Rastreabilidade:** Documento: "Normas_e_Procedimentos_v52.pdf" | Extrato: "No sentido de salvaguardar a informação sensível que possa existir fisicamente"

---

[Item 29]

**Questão:** Como é classificada a informação gerada e tratada no âmbito da GeoAtributo e que medidas físicas e lógicas de segurança são aplicadas especificamente à informação classificada como confidencial?

**Resposta:** A informação é classificada de três modos: **Confidencial** (informação administrativa e comercial); **Uso interno** (informação de base de projetos); e **Pública** (informação de divulgação de serviços). A informação confidencial em papel fica arquivada em **armário na sala da gerência**, devidamente etiquetada, dispondo a sala de **alarme com acesso restrito** à gerência e a dois colaboradores da área administrativa/comercial. Digitalmente, apenas os responsáveis administrativos, comerciais e a administração dispõem de **credenciais de acesso** a essa informação.

**Rastreabilidade:** Documento: "Normas_e_Procedimentos_v52.pdf" | Extrato: "A informação é classificada de três modos: * Confidencial: informação administrativa"

---

[Item 30]

**Questão:** Em caso de falha de energia elétrica, quais as obrigações e prazos limites que a equipa de colaboradores e a área administrativa devem respeitar para salvaguardar os equipamentos informáticos e os dados?

**Resposta:** Os colaboradores devem gravar os seus trabalhos e desligar os computadores pessoais no **limite máximo de 5 minutos** após a falha de energia. Se a falha se prolongar por **mais de 10 minutos**, um elemento da área administrativa deve **desligar as máquinas de rede e armazenamento (NAS)** locais.

**Rastreabilidade:** Documento: "Normas_e_Procedimentos_v52.pdf" | Extrato: "Equipa: (antecipadamente, cada um dos colaboradores está responsável por verificar se os seus"

---

## Lote 7 (Itens 31 a 35)

[Item 31]

**Questão:** No planeamento de faturação (Modelo 208), que regras de cores (Verde, Amarelo e Vermelho) são utilizadas para distinguir e caracterizar as datas previstas de faturação das fases em curso do projeto?

**Resposta:** As datas previstas de faturação no Modelo 208 são distinguidas de acordo com as seguintes cores: **Verde** (data mais realista para faturação); **Amarelo** (data prevista de acordo com o prazo estabelecido no cronograma e pendente da data da fase anterior); e **Vermelho** (data prevista mas pendente da aprovação por parte do cliente e/ou de outras entidades).

**Rastreabilidade:** Documento: "Normas_e_Procedimentos_v52.pdf" | Extrato: "Verde - data mais realista para faturação; Amarelo - data prevista de acordo com"

---

[Item 32]

**Questão:** Sempre que for realizada uma reunião com o sócio-gerente utilizando o formulário Google do Modelo 101 (Relatório Ata de reunião com o cliente), qual é o procedimento obrigatório no calendário e quem deve acompanhar o preenchimento?

**Resposta:** Sempre que seja realizada uma reunião com o sócio-gerente, o **link associado ao formulário Google deverá ser inserido no calendário** para que no dia seja preenchido pelo mesmo. Cabe à **área administrativa** acompanhar o seu devido preenchimento.

**Rastreabilidade:** Documento: "Normas_e_Procedimentos_v52.pdf" | Extrato: "Sempre que seja realizada uma reunião com o sócio-gerente, o link associado deverá"

---

[Item 33]

**Questão:** No âmbito do Orçamento (Modelo 103), qual o preenchimento mínimo obrigatório estabelecido para propostas informais e qual a exigência contratual para a participação em propostas formais?

**Resposta:** O preenchimento das folhas designadas **"Identificação do Projecto" e "Orçamento"** é o mínimo mandatório quando se trate de propostas informais. Contudo, aquando da participação em propostas formais, é obrigatório o preenchimento de todas as folhas (nomeadamente as folhas **"Faseamento", "Entregáveis", "Reuniões", "Recursos Humanos" e "Gantt Chart"**).

**Rastreabilidade:** Documento: "Normas_e_Procedimentos_v52.pdf" | Extrato: "O preenchimento das folhas designadas \"Identificação do Projecto\" e \"Orçamento\" é o mínimo"

---

[Item 34]

**Questão:** Ao acolher um visitor nas instalações da GeoAtributo, que dados específicos devem ser registados obrigatoriamente pelo colaborador no Modelo 215 (Registo de visitas) e qual o campo de preenchimento opcional?

**Resposta:** O colaborador deve efetuar obrigatoriamente o registo com o **primeiro e último nome, data, hora de entrada e responsável pelo acompanhamento da visita**. O preenchimento do campo **"Entidade"** é de caráter facultativo.

**Rastreabilidade:** Documento: "Normas_e_Procedimentos_v52.pdf" | Extrato: "Qualquer colaborador que rececione a entrada de algum visitante (por motivos de reunião,"

---

[Item 35]

**Questão:** Em que momentos específicos deve ser atualizado o Modelo 108 (Ponto de Situação de Propostas Enviadas) para cada proposta e qual link obrigatório deve ser adicionado no campo de observações?

**Resposta:** Este modelo deverá ser preenchido para cada proposta apresentada em dois momentos: **aquando da apresentação da proposta** e **aquando da decisão do cliente sobre a mesma**. No campo de observações, deve constar obrigatoriamente o **link de acesso à Ficha de Acompanhamento do Cliente (Modelo 107) que consta na ferramenta Wrike**.

**Rastreabilidade:** Documento: "Normas_e_Procedimentos_v52.pdf" | Extrato: "Este modelo deverá ser preenchido para cada proposta apresentada, nos seguintes momentos: aquando"

---

## Lote 8 (Itens 36 a 40)

[Item 36]

**Questão:** No âmbito do SGQ da GeoAtributo, no caso de uma ação de formação interna, a quem cabe a responsabilidade de remeter os elementos de formação e o respetivo Modelo 320 preenchido à área administrativa para arquivo?

**Resposta:** Em caso de **formação interna**, cabe ao **formador** a responsabilidade de proceder ao envio dos elementos de formação e do Modelo 320 preenchido à área administrativa (ao passo que nas formações externas essa responsabilidade recai sobre o próprio formando).

**Rastreabilidade:** Documento: "Normas_e_Procedimentos_v52.pdf" | Extrato: "Sempre que a formação for externa, deverá ser o formando a remeter à"

---

[Item 37]

**Questão:** Com que frequência regular, por quem e em qual modelo específico do SGQ deve ser registada a verificação da funcionalidade de todos os contactos móveis e fixos da GeoAtributo e das restantes empresas parceiras?

**Resposta:** A verificação de contactos deve ser efetuada **semanalmente, no início de cada semana**, pela **pessoa da área administrativa que estiver fisicamente nas instalações**, sendo o registo desta ação obrigatoriamente efetuado no **Modelo 221**.

**Rastreabilidade:** Documento: "Normas_e_Procedimentos_v52.pdf" | Extrato: "Semanalmente, é verificada a funcionalidade de todos os contactos móveis e fixos (da"

---

[Item 38]

**Questão:** Na execução de tarefas no âmbito de projetos, quais são as margens de tolerância de prolongamento do tempo de execução estabelecidas pelo SGQ para tarefas com mais de 100 horas e para tarefas com menos de 100 horas?

**Resposta:** É definida uma margem de tolerância de **5%** para tarefas ou subtarefas com **mais de 100 horas**, e de **10%** para tarefas ou subtarefas com **menos de 100 horas**.

**Rastreabilidade:** Documento: "Normas_e_Procedimentos_v52.pdf" | Extrato: "Por outro lado, sempre que sejam necessárias mais horas para a execução de"

---

[Item 39]

**Questão:** No processo de admissão de novos colaboradores, que tipo de credenciais e permissões iniciais de acesso ao servidor de dados são atribuídas ao novo elemento por razões de segurança de informação?

**Resposta:** Are atribuídas ao novo colaborador **credenciais pessoais de acesso ao servidor de dados**, mas configuradas estritamente com as permissões de **"convidado"** (as quais apenas lhe permitem ler a informação nas pastas de trabalhos em curso).

**Rastreabilidade:** Documento: "Normas_e_Procedimentos_v52.pdf" | Extrato: "No processo de admissão de colaboradores, ao novo elemento da equipa será atribuído"

---

[Item 40]

**Questão:** Sob que condições específicas de custos da GeoAtributo se torna obrigatório o preenchimento do Modelo 222 (Ficha de despesa) e qual a distribuição de responsabilidades pelo preenchimento das suas secções?

**Resposta:** O preenchimento do **Modelo 222** é obrigatório para **todas as despesas pontuais** e para **despesas mensais fixas sempre que se verifique qualquer desvio** em relação ao custo previsto. As **Secções 1 (Detalhes da Despesa) e 2 (Solicitação de Pagamento) são preenchidas pela área administrativa**, e a **Secção 3 (Autorização da Gerência) é preenchida pela gerência** após notificação por e-mail.

**Rastreabilidade:** Documento: "Normas_e_Procedimentos_v52.pdf" | Extrato: "O modelo 222 será preenchido através do google forms, em que as secções"

---

## Lote 9 (Itens 41 a 45)

[Item 41]

**Questão:** Sob que condições específicas de reporte de anomalia e tempo de indisponibilidade é admitida a reiniciação do Router Draytek de suporte à VPN, e que comunicação interna prévia deve ser efetuada?

**Resposta:** A reiniciação do router só deve ser realizada quando uma **amostra significativa de utilizadores** (definida como 4 pessoas em localizações diferentes, ou menos caso o número total de utilizadores seja igual ou inferior a 4) reportar a impossibilidade de ligação e esta se mantiver por um **período mínimo de 10 minutos**. Adicionalmente, antes de proceder à reiniciação, deve ser enviado obrigatoriamente um **e-mail para o geogrupo** comunicando a anomalia.

**Rastreabilidade:** Documento: "Normas_e_Procedimentos_v52.pdf" | Extrato: "A reiniciação do router deverá ser realizada apenas quando uma amostra significativa"

---

[Item 42]

**Questão:** Como é realizada a verificação e o registo de sucesso do backup automático diário dos servidores para a NAS, e em que situações específicas a administração de sistemas recebe notificações por e-mail?

**Resposta:** A verificação dos backups efetuados é realizada de forma automática através do **recebimento de um e-mail enviado pelo programa que executa os backups**, dando conta do sucesso da operação. Por sua vez, a administração de sistemas recebe notificações específicas no e-mail **sincro@geo** em caso de ocorrência de erro e quando a capacidade de armazenamento da NAS atinge os **80%**.

**Rastreabilidade:** Documento: "Normas_e_Procedimentos_v52.pdf" | Extrato: "Verificação dos backup's efetuados (registo): a ser realizado através do envio de"

---

[Item 43]

**Questão:** Com que frequência regular deve ser atualizado o currículo da própria empresa (currículo Geo) e por qual perfil profissional?

**Resposta:** O currículo da empresa deve ser atualizado de **3 em 3 meses** (trimestralmente) pela **técnica administrativa**, a qual deve utilizar o currículo com a data mais recente de atualização, alterar ou acrescentar o que for necessário e guardá-lo colocando sempre a data de atualização no nome do ficheiro.

**Rastreabilidade:** Documento: "Normas_e_Procedimentos_v52.pdf" | Extrato: "Contém o currículo da empresa, o qual deve ser atualizado de 3"

---

[Item 44]

**Questão:** No âmbito do controlo de qualidade de entregas ao cliente via Modelo 309, até que campo deve o gestor preencher a ficha digitalmente e quem deve assinar os campos 5 e 6 antes do seu arquivo?

**Resposta:** O gestor do projeto deve preencher a ficha digitalmente **até ao campo 5, inclusive**. Após ser impressa, a ficha deve ser obrigatoriamente assinada pelo **gestor do projeto no campo 5** ("Declaração do Gestor") e pelo **coordenador do projeto no ponto 6** ("Declaração do Coordenador") para que este proceda à deliberação e autorização de entrega.

**Rastreabilidade:** Documento: "Normas_e_Procedimentos_v52.pdf" | Extrato: "1. O gestor do projeto deverá preencher a ficha, em versão digital, até"

---

[Item 45]

**Questão:** Aquando do início de um projeto, caso se verifiquem desvios negativos na análise crítica do orçamento inicial (Modelo 103) face às necessidades reais dos trabalhos, qual o procedimento de reporte a adotar?

**Resposta:** Caso se verifiquem desvios negativos (necessidade de recursos adicionais, tempo ou outros aspetos que influenciem negativamente a previsão orçamental inicial), tal deverá ser **reportado, via email, à gerência**, identificando detalhadamente qual é a **fonte do desvio e a sua respetiva dimensão**.

**Rastreabilidade:** Documento: "Normas_e_Procedimentos_v52.pdf" | Extrato: "Caso se verifiquem desvios negativos (necessidade de recursos adicionais, tempo ou outros"

---

## Lote 10 (Itens 46 a 50)

[Item 46]

**Questão:** Em contexto de teletrabalho na GeoAtributo, sob que restrição os telemóveis pessoais das gestoras podem ser utilizados para a realização de chamadas telefónicas de serviço e que alternativa preferencial é proposta?

**Resposta:** As gestoras podem utilizar os seus telemóveis pessoais, mas exclusivamente como dispositivo para a instalação de uma aplicação que permite fazer chamadas VoIP (chamadas através da internet). Em alternativa ao telemóvel pessoal, a aplicação poderá, preferencialmente, ser instalada num tablet disponibilizado pela GeoAtributo.

**Rastreabilidade:** Documento: "Normas_e_Procedimentos_v52.pdf" | Extrato: "Quanto ao estabelecimento de chamadas telefónicas, as gestoras podem utilizar os seus"

---

[Item 47]

**Questão:** No âmbito da elaboração de atas de reuniões no processo de projetos da GeoAtributo, a quem cabe a responsabilidade direta pela sua redação inicial e por quem deve a mesma ser validada?

**Resposta:** A elaboração da ata é da responsabilidade do membro mais recente da equipa, devendo ser posteriormente validada pelo gestor de projeto.

**Rastreabilidade:** Documento: "Normas_e_Procedimentos_v52.pdf" | Extrato: "A elaboração da ata deverá ser da responsabilidade do membro mais recente"

---

[Item 48]

**Questão:** Sempre que ocorre uma atualização legislativa relevante no Modelo 322, que modificação obrigatória deve ser efetuada na Ficha Geral de Projeto (Modelo 301) dos projetos afetados e que informação deve ser prestada ao cliente?

**Resposta:** Deve ser alterada a Ficha Geral de Projeto (Modelo 301) de cada um dos projetos afetados, colocando-se no campo "requisitos legais e regulamentares" uma nota que evidencie a ocorrência da alteração legislativa e se a mesma vai ser incorporada nos trabalhos em curso. Adicionalmente, o cliente deve ser sempre informado da alteração legislativa e de qual a posição da GeoAtributo e dos trabalhos desenvolvidos relativamente à referida alteração.

**Rastreabilidade:** Documento: "Normas_e_Procedimentos_v52.pdf" | Extrato: "Quando da atualização da legislação deve ser considerada a necessidade de alterar"

---

[Item 49]

**Questão:** Sob que condição específica se torna obrigatório o preenchimento da ficha de Análise do Cliente (Modelo 102) no processo prospetivo da GeoAtributo?

**Resposta:** O preenchimento da ficha de Análise do Cliente (Modelo 102) é de preenchimento obrigatório quando se tratar de um cliente com o qual a GeoAtributo nunca tenha trabalhado anteriormente.

**Rastreabilidade:** Documento: "Normas_e_Procedimentos_v52.pdf" | Extrato: "Esta ficha é de preenchimento obrigatório quando se tratar de um cliente com o"

---

[Item 50]

**Questão:** No âmbito do processo de gestão de ideias do Núcleo de IDI, como são classificadas as ideias em função da pontuação obtida na avaliação trimestral conjunta da Gerência e do Coordenador de IDI?

**Resposta:** As ideias avaliadas são classificadas das seguintes formas: **Ideia aprovada para implementação de projeto IDI** (caso atinga uma avaliação superior a 17 pontos); **Ideia hibernada, para reavaliação mais tarde** (entre 16 a 17 pontos); **Ideia rejeitada** (pontuação inferior a 16 pontos); ou **Ideia para SGQ**.

**Rastreabilidade:** Documento: "Normas_e_Procedimentos_v52.pdf" | Extrato: "A avaliação da ideia é realizada pelo Coordenador de IDI em conjunto"
