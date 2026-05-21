# 📚 Professor IA — Ensino Médio

App de apoio ao estudo para o ensino médio brasileiro, usando Gemini (gratuito).

---

## 🚀 Como rodar localmente

### 1. Clone ou baixe os arquivos
```
professor_ia/
├── app.py
├── config.py
├── utils.py
├── requirements.txt
└── README.md
```

### 2. Instale as dependências
```bash
pip install -r requirements.txt
```

### 3. Rode o app
```bash
streamlit run app.py
```

### 4. Configure sua chave da API
- Acesse [aistudio.google.com](https://aistudio.google.com/apikey)
- Crie uma chave gratuita (sem cartão)
- Cole na barra lateral do app

---

## ☁️ Deploy no Streamlit Cloud (grátis)

### Passo 1 — Suba o projeto no GitHub
Crie um repositório e suba apenas estes arquivos:
```
professor_ia/
├── app.py
├── config.py
├── utils.py
├── requirements.txt
├── .env.example
└── .gitignore
```
⚠️ **NUNCA** suba `.env` nem `.streamlit/secrets.toml` — o `.gitignore` já os protege.

---

### Passo 2 — Crie o app no Streamlit Cloud
1. Acesse [share.streamlit.io](https://share.streamlit.io) e faça login com GitHub
2. Clique em **"New app"**
3. Selecione seu repositório e o arquivo `app.py`
4. Clique em **"Deploy!"**

---

### Passo 3 — Configure a chave da API com segurança
Ainda na tela de deploy (ou depois em **Settings > Secrets**):

Clique em **"Advanced settings"** → aba **"Secrets"** e cole:
```toml
GEMINI_API_KEY = "cole_sua_chave_aqui"
```

O app lê automaticamente essa chave — ninguém vê, nem fica exposta no código. ✅

---

### Resultado
Seu app terá um link público tipo:
```
https://seu-usuario-professor-ia.streamlit.app
```
Funciona no celular, tablet e computador. Pode compartilhar com quem quiser!

---

## 📋 Funcionalidades

- ✅ 8 matérias do ensino médio
- ✅ Respostas humanizadas e pedagógicas
- ✅ Dicas para o aluno não copiar a resposta
- ✅ Aviso claro quando o limite da API é atingido
- ✅ Contador de espera antes de tentar novamente
- ✅ Histórico da conversa por sessão
- ✅ Sugestões rápidas por matéria
- ✅ Gratuito com Gemini 2.5 Flash (~250 perguntas/dia)

---

## ⚠️ Limites do plano gratuito do Gemini (2026)

| Modelo | Req/min | Req/dia |
|---|---|---|
| Gemini 2.5 Flash | 10 | 250 |
| Gemini 2.5 Pro | 5 | 100 |

Para uso escolar casual, o limite gratuito é mais que suficiente.
