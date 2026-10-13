# Especificação para gerar pacotes de prova do ENEM (app Professor IA)

Este documento é a instrução completa para quem for gerar os pacotes. Siga-o à risca: o app lê os arquivos
automaticamente e um campo fora do padrão faz a questão ser rejeitada. Quem receber o pacote vai rodar um
validador que compara tudo com os PDFs oficiais do INEP, então **fidelidade ao PDF vale mais que beleza**.

## 1. O que produzir

Provas **oficiais do INEP, aplicação regular, caderno AZUL**, dos três anos mais recentes: **2023, 2024 e 2025**.
Entregue **um pacote por dia de prova** (6 pacotes no total), para facilitar a conferência:

| Pacote (nome da pasta) | Conteúdo | Questões |
|---|---|---|
| `enem_2023_dia1`, `enem_2024_dia1`, `enem_2025_dia1` | Linguagens + Ciências Humanas | 6 a 90 → **85** (1 a 5 são língua estrangeira: **não incluir**) |
| `enem_2023_dia2`, `enem_2024_dia2`, `enem_2025_dia2` | Ciências da Natureza + Matemática | 91 a 180 → **90** |

- **Não incluir:** redação, questões de inglês/espanhol (1 a 5), cadernos de outras cores, aplicações PPL/reaplicação.
- **Questão anulada:** mantenha no pacote e marque `"situacao": "anulada"` no gabarito (o app a ignora).
- **Fonte:** somente os PDFs oficiais em
  https://www.gov.br/inep/pt-br/areas-de-atuacao/avaliacao-e-exames-educacionais/enem/provas-e-gabaritos
  (arquivos `AAAA_PV_impresso_D1_CD1.pdf` / `AAAA_GB_impresso_D1_CD1.pdf` etc.; confirme o código do caderno azul
  de cada dia no nome do arquivo). **Não use sites de terceiros.**

## 2. Estrutura de cada pacote

```
enem_2025_dia1/
├── questoes.json
├── gabarito.json
├── validacao.json
└── imagens/
    ├── q047_mapa.png
    └── ...
```

Entregue em `.zip` com exatamente essa árvore. Caminhos sempre com `/`, relativos à pasta do pacote.

## 3. `questoes.json`

```json
{
  "versao_esquema": "1.0",
  "titulo": "ENEM 2025 - Dia 1 - Caderno azul",
  "quantidade": 85,
  "questoes": [ ...85 objetos... ]
}
```

Cada questão (exemplo real do pacote-modelo):

```json
{
  "id": "enem_2025_regular_d1_cd1_q011",
  "ano": 2025,
  "aplicacao": "regular",
  "dia": 1,
  "caderno": 1,
  "cor": "azul",
  "numero_original": 11,
  "area": "Linguagens",
  "idioma": null,
  "conteudo": [
    {"tipo": "texto", "texto": "— Vejo, disse ele com algum acanhamento, que o doutor não é nenhum pé-rapado..."},
    {"tipo": "texto", "texto": "TAUNAY, A. d’E. Inocência. Disponível em: www.dominiopublico.gov.br. Acesso em: 29 fev. 2024."},
    {"tipo": "texto", "texto": "Nesse trecho, ao se referir à sua filha, o pai de Inocência reproduz os ideais românticos, presentes na"}
  ],
  "alternativas": [
    {"letra": "A", "conteudo": [{"tipo": "texto", "texto": "valorização do ambiente rural na formação moral da mulher."}]},
    {"letra": "B", "conteudo": [{"tipo": "texto", "texto": "figura decorativa da mulher ante o protagonismo masculino."}]},
    {"letra": "C", "conteudo": [{"tipo": "texto", "texto": "equivalência de origem social para a harmonia do casal."}]},
    {"letra": "D", "conteudo": [{"tipo": "texto", "texto": "importância do dote como condição para o casamento."}]},
    {"letra": "E", "conteudo": [{"tipo": "texto", "texto": "aura de mistério sobre a identidade da jovem."}]}
  ],
  "fonte": {
    "instituicao": "Inep",
    "pagina_pdf": 8,
    "url_prova": "https://download.inep.gov.br/enem/provas_e_gabaritos/2025_PV_impresso_D1_CD1.pdf"
  }
}
```

Campos e regras:

- **`id`**: `enem_{ano}_regular_d{dia}_cd{caderno}_q{numero com 3 dígitos}`. Único em todo o pacote.
- **`numero_original`**: número impresso na prova (6 a 90 no Dia 1; 91 a 180 no Dia 2). **Nunca renumere.**
- **`area`**: exatamente um destes quatro valores: `"Linguagens"`, `"Ciências Humanas"`, `"Ciências da Natureza"`, `"Matemática"`.
- **`idioma`**: sempre `null`. **`aplicacao`**: `"regular"`. **`cor`**: `"azul"`.
- **`fonte.pagina_pdf`**: página do PDF da prova (contando a partir de 1) onde a questão **começa**.
  **`fonte.url_prova`**: URL oficial do PDF da prova (`..._PV_...`). O validador deduz o PDF do gabarito trocando `PV` por `GB`.
- **`alternativas`**: sempre as cinco, letras `A`, `B`, `C`, `D`, `E`, nessa ordem. Cada uma tem `conteudo` (lista de blocos).
- **Nunca** coloque resposta, dica, explicação ou resolução em `questoes.json`.

### Tipos de bloco (a ordem da lista é a ordem de exibição)

| Bloco | Campos | Quando usar |
|---|---|---|
| `{"tipo":"texto","texto":"..."}` | `texto` | Texto corrido, citações, comando da questão, alternativas em texto |
| `{"tipo":"latex","expressao":"\\frac{3}{5}"}` | `expressao` | Equação ou fração **em linha própria** (exibida em destaque, centralizada) |
| `{"tipo":"imagem","arquivo":"imagens/q047_mapa.png","descricao":"...","largura_px":553,"altura_px":447}` | todos obrigatórios (`recorte_pdf_pt` é opcional) | Figuras que não podem virar texto |

## 4. `gabarito.json`

```json
{
  "versao_esquema": "1.0",
  "respostas": [
    {"questao_id": "enem_2025_regular_d1_cd1_q011", "alternativa_correta": "B", "situacao": "valida",
     "fonte": "https://download.inep.gov.br/enem/provas_e_gabaritos/2025_GB_impresso_D1_CD1.pdf"}
  ]
}
```

Uma resposta para **cada** questão do pacote, copiada do PDF oficial do gabarito (nunca deduzida ou "resolvida").
Para questão anulada: `"situacao": "anulada"` e `"alternativa_correta": null`.

## 5. `validacao.json` (rastreabilidade)

```json
{
  "questoes": 85,
  "fontes_sha256": {"2025_PV_impresso_D1_CD1.pdf": "<sha256>", "2025_GB_impresso_D1_CD1.pdf": "<sha256>"},
  "observacoes": ""
}
```

## 6. Regras de transcrição do texto

1. **Fidelidade total.** Copie exatamente o que está na prova, usando a **camada de texto do PDF** (não adivinhe por OCR
   quando houver texto selecionável). Não corrija, não atualize a ortografia, não resuma, não "melhore".
2. **Remova** o que não é conteúdo da questão: o cabeçalho "QUESTÃO 11", cabeçalhos e rodapés de página
   (ex.: "LC - 1º dia | Caderno 1 - AZUL - Página 8"), códigos de barras/asteriscos, quadros "RASCUNHO".
3. **Mantenha** as linhas de fonte do texto (`Disponível em: ... Acesso em: ...`, `AUTOR. Obra, ano.`) como bloco `texto`
   logo após o texto a que pertencem.
4. **Hifenização de diagramação:** una a palavra quebrada no fim da linha ("transfe-\nrência" → "transferência").
   Hífens que fazem parte da palavra ("pé-rapado", "norma-padrão") permanecem.
5. **Parágrafos:** um bloco `texto` para cada parágrafo, citação ou fonte. **Versos de poema ou letra de música:** um único
   bloco, com `\n` entre os versos.
6. **Cada questão é independente.** Se um texto-base é compartilhado por duas questões, repita-o nas duas.
7. **Símbolos e unidades:** use caracteres Unicode (m³, m², CO₂, H₂O, °C, ≤, ≥, ×, √, π, ½). **Não use LaTeX dentro de bloco
   `texto`**: o `$` é mostrado literalmente (R$ 10,00 é permitido e sai correto).
8. **Fórmulas e frações em linha própria** (inclusive alternativas que são só uma expressão) vão em bloco `latex`.
   Matemática simples dentro de uma frase (x², 3/4, 2 × 10⁵) fica no `texto`, em Unicode.
9. **Cuidado com formatação indevida no `texto`** (o app interpreta Markdown): não deixe uma linha começar com `#`, `>` ou
   `- `/`* `, e escreva `\*` e `\_` se o texto original tiver asterisco ou sublinhado literal.
10. **Se não tiver certeza** de um trecho (ilegível, símbolo estranho), **não invente**: registre a questão em `pendencias.md`
    (id + o que ficou em dúvida) e, se possível, use imagem daquele trecho.

## 7. Regras para imagens

- **Use imagem apenas quando for necessário:** gráficos, mapas, tabelas, infográficos, charges, pinturas, fotos, esquemas,
  estruturas químicas, figuras geométricas. **Tabelas vão como imagem.** Texto corrido nunca vira imagem.
- **Tudo o que é preciso para resolver a questão deve estar visível** (legendas, escalas, eixos, fontes da figura).
  Não omita nem resuma informação que só existe na figura.
- **Recorte justo:** sem número da questão, sem margens grandes da página e sem partes de outras questões.
- **Formato PNG** (JPEG só para fotos e pinturas), em boa resolução (cerca de 200 a 300 dpi: o texto dentro da imagem
  precisa ficar nítido em tela de celular), **no máximo ~600 KB** por arquivo.
- **Nomes:** `imagens/q{numero}_{assunto}.png` (ex.: `q047_mapa.png`; alternativas em imagem: `q138_alternativa_A.png`).
- **`descricao`:** em português, objetiva, descrevendo **o que se vê** para quem não enxerga a imagem. **Nunca** inclua a
  resposta ou pistas de resolução. `largura_px` e `altura_px` devem ser as dimensões reais do arquivo.
- **Alternativas em imagem:** uma imagem por alternativa, sem a letra desenhada quando possível (o app mostra a letra).

## 8. Checklist antes de entregar

- [ ] Quantidade certa: **85** (Dia 1) ou **90** (Dia 2); numeração `numero_original` completa e sem repetição.
- [ ] Todas as questões com 5 alternativas A–E; todas as áreas com os nomes exatos.
- [ ] `gabarito.json` com uma resposta para cada questão, copiada do PDF oficial.
- [ ] Todo arquivo citado em `"arquivo"` existe em `imagens/`; nenhuma imagem sobrando sem uso.
- [ ] Nenhum cabeçalho/rodapé do PDF, nenhuma resposta ou explicação dentro de `questoes.json`.
- [ ] `fonte.pagina_pdf` e `fonte.url_prova` preenchidos em todas as questões.
- [ ] `pendencias.md` entregue (vazio se não houver dúvidas).

Se você consegue executar Python, rode o validador (`ferramentas/validar_pacote.py`, fornecido junto) antes de entregar.
Ele dá **APROVADO** apenas quando estrutura, gabarito e texto conferem com os PDFs oficiais.
