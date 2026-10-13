# Prompt para gerar um pacote de prova do ENEM

Como usar: troque os campos entre {chaves} (ANO, DIA, FAIXA, ÁREAS), cole o prompt na outra IA e **anexe**:
1. `ESPECIFICACAO_PACOTE_ENEM.md` (esta pasta);
2. o pacote modelo `2025_piloto` em .zip (`banco_enem/2025_piloto`);
3. os PDFs oficiais da prova e do gabarito, se a IA não conseguir baixá-los sozinha.

Valores por pacote:

| Pacote | ANO | DIA | FAIXA | ÁREAS | Total |
|---|---|---|---|---|---|
| enem_2025_dia1 (comece por este) | 2025 | 1 | questões 6 a 90 | Linguagens e Ciências Humanas | 85 |
| enem_2025_dia2 | 2025 | 2 | questões 91 a 180 | Ciências da Natureza e Matemática | 90 |
| os mesmos para 2024 e 2023 | | | | | |

---

## PROMPT (copie daqui)

```
Você vai montar um pacote de dados com as questões oficiais do ENEM {ANO}, Dia {DIA}, caderno AZUL
(aplicação regular), questões {FAIXA} ({ÁREAS}). O pacote alimenta um app escolar para alunos de 14 a 18
anos, que corrige automaticamente pelo gabarito. Um erro de transcrição ou de gabarito ensina errado ao
aluno, então fidelidade ao PDF oficial é mais importante do que rapidez ou aparência.

ANEXOS
- ESPECIFICACAO_PACOTE_ENEM.md: regras completas do formato. Siga-a integralmente; ela vale sobre qualquer
  hábito seu de formatação.
- Pacote modelo (2025_piloto): exemplo real, já aprovado, de como os arquivos devem ficar. Imite a estrutura
  e o estilo dos blocos.
- PDFs oficiais do INEP (prova e gabarito), se anexados. Se não estiverem anexados, baixe-os de
  https://www.gov.br/inep/pt-br/areas-de-atuacao/avaliacao-e-exames-educacionais/enem/provas-e-gabaritos
  (arquivos {ANO}_PV_impresso_D{DIA}_CD?.pdf e {ANO}_GB_impresso_D{DIA}_CD?.pdf, caderno azul).
  Use somente fontes oficiais do INEP, nunca sites de terceiros.

COMO TRABALHAR
1. Confirme qual é o PDF do caderno azul do Dia {DIA} e me diga o nome dos arquivos que vai usar.
   Se não conseguir acessar os PDFs, PARE e me peça para anexá-los. Não prossiga de memória.
2. Extraia o texto da camada de texto do PDF (use código, por exemplo PyMuPDF ou pdfplumber). Não reescreva
   nem "lembre" o enunciado: copie o que está no PDF, aplicando as regras de limpeza da especificação.
3. Monte o gabarito.json copiando as respostas do PDF oficial do gabarito, questão por questão.
4. Para cada figura necessária, recorte a imagem diretamente do PDF (renderizando a página em alta
   resolução e cortando a região da figura). Nunca redesenhe, nunca recrie uma figura.
5. Trabalhe em lotes de cerca de 15 questões. Ao fim de cada lote, diga quais questões foram concluídas.
   Se o limite da conversa impedir terminar tudo, entregue o que está pronto, diga exatamente em que
   questão parou e aguarde eu escrever "continue". Nunca entregue um pacote incompleto como se estivesse
   completo.
6. Quando terminar todos os lotes, gere o .zip final com exatamente esta árvore:
   enem_{ANO}_dia{DIA}/questoes.json, gabarito.json, validacao.json, pendencias.md e imagens/.

REGRAS QUE NÃO PODEM SER QUEBRADAS
- Não invente nada. Se um trecho estiver ilegível ou duvidoso, não complete por conta própria: anote em
  pendencias.md (id da questão e a dúvida) e, se for possível, use uma imagem daquele trecho.
- Não resolva as questões. As respostas vêm somente do PDF do gabarito.
- Não coloque explicação, dica, resolução ou resposta dentro de questoes.json.
- Mantenha numero_original exatamente como impresso na prova; nunca renumere.
- Exclua da prova: questões de língua estrangeira (1 a 5), redação, cabeçalhos e rodapés de página.
- Tabelas, gráficos, mapas, charges e figuras viram imagem; texto corrido nunca vira imagem.
- Frações e equações em linha própria vão em bloco latex; matemática dentro de frase fica em Unicode.

ANTES DE ENTREGAR, VERIFIQUE POR CÓDIGO E ME MOSTRE O RESULTADO
- Quantidade de questões esperada: {TOTAL}, números {FAIXA} sem faltar nem repetir.
- Toda questão tem as cinco alternativas A a E, na ordem, e a área escrita exatamente como na especificação.
- Todo "arquivo" citado em questoes.json existe em imagens/, e as dimensões largura_px/altura_px conferem
  com o arquivo real.
- gabarito.json tem uma resposta para cada questão e nenhuma a mais.
- Nenhum cabeçalho ou rodapé do PDF sobrou nos textos (por exemplo "Caderno 1 - AZUL", "Página 8").
- Comparação automática: para cada questão, o texto do JSON precisa existir na página do PDF
  (ignorando acentos e quebras de linha). Liste as questões em que isso falhar.

ENTREGA FINAL
Responda com: (a) o .zip; (b) um relatório curto com a quantidade de questões, de imagens e de blocos latex;
(c) o conteúdo de pendencias.md; (d) o que você verificou por código e o que NÃO conseguiu verificar.
Seja honesto: se algo não foi conferido, diga. Não afirme "tudo conferido" sem ter rodado as verificações.
```

---

## Depois que a IA entregar

1. Descompacte dentro de `banco_enem/` (ficando `banco_enem/enem_{ANO}_dia{DIA}/questoes.json`).
2. Rode: `python ferramentas/validar_pacote.py banco_enem/enem_{ANO}_dia{DIA}`
3. Só use o pacote se o resultado for **APROVADO**. Se houver ERRO ou AVISO, devolva a saída do validador à IA:
   "Corrija exatamente estes pontos e reenvie o pacote completo."
