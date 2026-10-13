# Pendências e limitações de validação

- **enem_2025_regular_d1_cd1_q006, enem_2025_regular_d1_cd1_q007, enem_2025_regular_d1_cd1_q008, enem_2025_regular_d1_cd1_q009 e enem_2025_regular_d1_cd1_q010:** o texto-base está na página 6, mas as questões começam na página 7. O texto-base foi repetido em cada questão e `fonte.pagina_pdf` permanece 7, conforme a especificação. O validador fornecido consulta apenas a página inicial e a seguinte; por isso reprova esses cinco casos. A comparação complementar inclui a página 6 e confirmou todos os blocos textuais, desconsiderando os índices de linha na busca.

- **enem_2025_regular_d1_cd1_q031:** o título “dezenove” e o poema estão rasterizados no PDF, sem camada textual selecionável. Foram transcritos com apoio de OCR e conferência visual; a ilustração foi recortada separadamente. Esses dois blocos não puderam ser comparados automaticamente com a camada textual do PDF e precisam de uma segunda revisão visual antes da liberação aos alunos. Fonte, comando e alternativas passaram na comparação automática. O validador fornecido reprova este caso.

- **enem_2025_regular_d1_cd1_q038:** os índices de linha foram preservados para permitir consultar as referências “l. 1”, “l. 3” etc. A leitura linear do PDF separa os índices do texto, e o validador fornecido reprova esse caso. A comparação complementar, desconsiderando os índices de linha na busca, confirmou todos os blocos textuais.

O validador fornecido foi executado sem alterações: **REPROVADO, 7 erros e 0 avisos**. Os resultados estão em `validacao.json`. A comparação complementar confirmou os 790 blocos textuais verificáveis; os dois blocos rasterizados da questão 31 ficaram explicitamente excluídos dessa comparação.

Não houve validação de importação ou de exibição no app escolar do usuário. O texto interno das figuras foi revisado visualmente, sem comparação automática integral por OCR.
