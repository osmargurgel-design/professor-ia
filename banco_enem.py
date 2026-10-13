"""Banco de questões oficiais do ENEM (INEP).

Lê a pasta banco_enem/ uma única vez e mantém em memória. Não usa IA nem internet.
Dois formatos de prova são aceitos:

  1. Pacote em subpasta (formato preferido): banco_enem/<nome>/ com questoes.json, gabarito.json
     e imagens/. O enunciado e as alternativas são blocos de texto, LaTeX e imagem, então o app
     os desenha de forma nativa (só as figuras reais ficam como imagem).
  2. Arquivo .json solto em banco_enem/ (formato antigo): cada questão é uma imagem recortada
     do PDF do INEP, com enunciado e alternativas dentro da figura.

Para adicionar uma prova: copie a pasta (ou o arquivo) para banco_enem/ e reinicie o app.
"""
import base64
import json
import random
from pathlib import Path

import streamlit as st

import assuntos

PASTA = Path(__file__).parent / "banco_enem"
LETRAS = ("A", "B", "C", "D", "E")

_AREAS_CURTAS = (
    ("Linguagens", "Linguagens"),
    ("Ciências Humanas", "Ciências Humanas"),
    ("Ciências da Natureza", "Ciências da Natureza"),
    ("Matemática", "Matemática"),
)


def _area_curta(area: str) -> str:
    for prefixo, curta in _AREAS_CURTAS:
        if area.startswith(prefixo):
            return curta
    return area


def _ler_questao(q: dict, fonte: dict, rotulo_arquivo: str):
    """Valida uma questão. Retorna (meta, imagens) ou None se estiver inválida."""
    try:
        gabarito = str(q["gabarito"]).strip().upper()
        if q.get("anulada") or gabarito not in LETRAS:
            return None
        partes = q["partes_visuais"]
        imagens = []
        for p in partes:
            uri = p["imagem_data_uri"]
            if not uri.startswith("data:image/"):
                return None
            imagens.append(base64.b64decode(uri.split(",", 1)[1]))
        if not imagens:
            return None
        ano = int(q["ano"])
        numero = int(q["numero_original"])
        meta = {
            "id": str(q["id"]),
            "formato": "imagem",
            "assunto": None,
            "ano": ano,
            "numero": numero,
            "area": _area_curta(str(q["area"])),
            "gabarito": gabarito,
            "caderno": f"{q.get('cor', '')}".strip(),
            "rotulo": f"ENEM {ano} · Questão {numero}",
            "prova_url": fonte.get("prova_url", ""),
            "gabarito_url": fonte.get("gabarito_url", ""),
        }
        return meta, imagens
    except (KeyError, TypeError, ValueError, AttributeError):
        return None


def _ler_blocos(blocos, pasta: Path):
    """Valida e normaliza blocos de conteúdo (texto / latex / imagem). Retorna None se inválido."""
    if not isinstance(blocos, list) or not blocos:
        return None
    saida = []
    for b in blocos:
        tipo = b.get("tipo")
        if tipo == "texto" and isinstance(b.get("texto"), str) and b["texto"].strip():
            saida.append({"tipo": "texto", "texto": b["texto"]})
        elif tipo == "latex" and isinstance(b.get("expressao"), str) and b["expressao"].strip():
            saida.append({"tipo": "latex", "expressao": b["expressao"]})
        elif tipo == "imagem" and isinstance(b.get("arquivo"), str):
            caminho = (pasta / b["arquivo"]).resolve()
            # só aceita arquivos que existam e estejam DENTRO da pasta do pacote
            if not caminho.is_file() or pasta.resolve() not in caminho.parents:
                return None
            saida.append({
                "tipo": "imagem",
                "caminho": str(caminho),
                "largura": int(b.get("largura_px") or 0),
                "descricao": str(b.get("descricao") or ""),
            })
        else:
            return None
    return saida


def textos_da_questao(conteudo: list, alternativas: dict) -> tuple[str, str]:
    """(texto do enunciado, texto das alternativas), incluindo fórmulas e descrição das imagens."""
    def juntar(blocos_lista):
        return " ".join(b.get("texto") or b.get("expressao") or b.get("descricao") or "" for blocos in blocos_lista for b in blocos)
    return juntar([conteudo]), juntar(alternativas.values())


def _ler_questao_blocos(q: dict, gabaritos: dict, pasta: Path):
    """Valida uma questão do formato novo. Retorna meta ou None."""
    try:
        resp = gabaritos[str(q["id"])]
        gabarito = str(resp["alternativa_correta"]).strip().upper()
        if resp.get("situacao") != "valida" or gabarito not in LETRAS:
            return None
        enunciado = _ler_blocos(q["conteudo"], pasta)
        alternativas = {}
        for alt in q["alternativas"]:
            letra = str(alt["letra"]).strip().upper()
            alternativas[letra] = _ler_blocos(alt["conteudo"], pasta)
        if enunciado is None or sorted(alternativas) != list(LETRAS) or None in alternativas.values():
            return None
        ano = int(q["ano"])
        numero = int(q["numero_original"])
        fonte = q.get("fonte") or {}
        return {
            "id": str(q["id"]),
            "formato": "blocos",
            "ano": ano,
            "numero": numero,
            "area": _area_curta(str(q["area"])),
            "gabarito": gabarito,
            "rotulo": f"ENEM {ano} · Questão {numero}",
            "prova_url": str(fonte.get("url_prova", "")),
            "conteudo": enunciado,
            "alternativas": alternativas,
            "assunto": assuntos.classificar(_area_curta(str(q["area"])), *textos_da_questao(enunciado, alternativas)),
        }
    except (KeyError, TypeError, ValueError, AttributeError):
        return None


def _carregar_pacote(pasta: Path, questoes: dict, avisos: list):
    try:
        dq = json.loads((pasta / "questoes.json").read_text(encoding="utf-8"))
        dg = json.loads((pasta / "gabarito.json").read_text(encoding="utf-8"))
        gabaritos = {str(r["questao_id"]): r for r in dg["respostas"]}
        lista = dq["questoes"]
    except (OSError, ValueError, KeyError, TypeError):
        avisos.append(f"{pasta.name}/: questoes.json ou gabarito.json ilegível ou fora do formato esperado")
        return
    puladas = substituidas = 0
    for q in lista:
        meta = _ler_questao_blocos(q, gabaritos, pasta) if isinstance(q, dict) else None
        if meta is None:
            puladas += 1
            continue
        if meta["id"] in questoes:  # mesma questão em outra pasta: vale a da pasta que vem por último (ordem alfabética)
            substituidas += 1
        questoes[meta["id"]] = meta
    if puladas:
        avisos.append(f"{pasta.name}/: {puladas} questão(ões) ignorada(s) por estarem inválidas ou sem gabarito válido")
    if substituidas:
        avisos.append(f"{pasta.name}/: {substituidas} questão(ões) já existiam em outra pasta e foram substituídas por esta versão")


def _aplicar_assuntos_manuais(questoes: dict, avisos: list):
    """banco_enem/assuntos_manuais.json corrige o assunto automático: {"id da questão": "Assunto"}.
    Use null (ou apague a linha) para voltar à classificação automática."""
    arquivo = PASTA / "assuntos_manuais.json"
    if not arquivo.exists():
        return
    try:
        manuais = json.loads(arquivo.read_text(encoding="utf-8"))
        if not isinstance(manuais, dict):
            raise ValueError
    except (OSError, ValueError):
        avisos.append("assuntos_manuais.json: arquivo ilegível (deve ser um objeto JSON {id: assunto})")
        return
    invalidos = 0
    for qid, assunto in manuais.items():
        meta = questoes.get(qid)
        if meta is None or assunto is None:
            continue
        if assunto not in assuntos.ASSUNTOS.get(meta["area"], {}):
            invalidos += 1
            continue
        meta["assunto"] = assunto
    if invalidos:
        avisos.append(f"assuntos_manuais.json: {invalidos} correção(ões) ignorada(s) por assunto inexistente na área da questão")


@st.cache_resource(show_spinner=False)
def carregar_banco() -> dict:
    """Retorna {'questoes': {id: meta}, 'imagens': {id: [bytes]}, 'avisos': [str]}."""
    questoes: dict[str, dict] = {}
    imagens: dict[str, list[bytes]] = {}
    avisos: list[str] = []

    for pasta in sorted(p for p in PASTA.iterdir() if p.is_dir() and (p / "questoes.json").exists()):
        _carregar_pacote(pasta, questoes, avisos)

    for arquivo in sorted(PASTA.glob("*.json")):
        if arquivo.name == "assuntos_manuais.json":  # não é uma prova: ver _aplicar_assuntos_manuais
            continue
        try:
            dados = json.loads(arquivo.read_text(encoding="utf-8"))
            lista = dados["questoes"]
        except (OSError, ValueError, KeyError, TypeError):
            avisos.append(f"{arquivo.name}: arquivo ilegível ou fora do formato esperado")
            continue
        fonte = dados.get("fonte", {}) if isinstance(dados.get("fonte"), dict) else {}
        puladas = 0
        for q in lista:
            lido = _ler_questao(q, fonte, arquivo.name) if isinstance(q, dict) else None
            if lido is None:
                puladas += 1
                continue
            meta, imgs = lido
            if meta["id"] in questoes:  # id repetido entre arquivos: mantém o primeiro
                puladas += 1
                continue
            questoes[meta["id"]] = meta
            imagens[meta["id"]] = imgs
        if puladas:
            avisos.append(f"{arquivo.name}: {puladas} questão(ões) ignorada(s) por estarem inválidas ou anuladas")

    _aplicar_assuntos_manuais(questoes, avisos)

    for aviso in avisos:  # aparece no terminal, para quem mantém o app
        print(f"[banco_enem] {aviso}")
    return {"questoes": questoes, "imagens": imagens, "avisos": avisos}


def anos_disponiveis() -> list[int]:
    return sorted({m["ano"] for m in carregar_banco()["questoes"].values()})


def contagem_por_area(ano: int | None = None) -> dict[str, int]:
    """Quantas questões há em cada área (opcionalmente só de um ano)."""
    cont: dict[str, int] = {}
    for m in carregar_banco()["questoes"].values():
        if ano is None or m["ano"] == ano:
            cont[m["area"]] = cont.get(m["area"], 0) + 1
    return dict(sorted(cont.items()))


def contagem_por_assunto(area: str, ano: int | None = None) -> dict[str, int]:
    """Quantas questões já classificadas há em cada assunto da área (as sem assunto não entram)."""
    cont: dict[str, int] = {}
    for m in carregar_banco()["questoes"].values():
        if m["area"] == area and (ano is None or m["ano"] == ano) and m.get("assunto"):
            cont[m["assunto"]] = cont.get(m["assunto"], 0) + 1
    return dict(sorted(cont.items()))


def sortear(n: int, area: str | None = None, ano: int | None = None, assunto: str | None = None,
            evitar: set[str] | None = None) -> list[dict]:
    """Sorteia até n questões (sem repetir) filtrando por área, ano e/ou assunto.
    Questões de `evitar` (as que o aluno já viu) só entram se não houver outras suficientes."""
    candidatas = [
        m for m in carregar_banco()["questoes"].values()
        if (area is None or m["area"] == area) and (ano is None or m["ano"] == ano)
        and (assunto is None or m.get("assunto") == assunto)
    ]
    random.shuffle(candidatas)
    if evitar:
        candidatas.sort(key=lambda m: m["id"] in evitar)   # ordenação estável: as já vistas vão para o fim
    return candidatas[:n]


def obter(questao_id: str) -> dict | None:
    """Metadados completos de uma questão (None se não existir mais no banco)."""
    return carregar_banco()["questoes"].get(questao_id)


def imagens_da_questao(questao_id: str) -> list[bytes]:
    return carregar_banco()["imagens"].get(questao_id, [])
