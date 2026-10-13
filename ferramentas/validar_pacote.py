"""Valida um pacote de prova do ENEM antes de colocá-lo em banco_enem/.

Uso (na pasta do projeto):
    python ferramentas/validar_pacote.py banco_enem/enem_2025_dia1
    python ferramentas/validar_pacote.py banco_enem/enem_2025_dia1 --sem-pdf   # só estrutura, sem baixar PDFs

O que confere:
  1. Estrutura: ids únicos, 5 alternativas A-E, blocos válidos, imagens existentes, campos obrigatórios.
  2. Gabarito: toda questão tem resposta e nenhuma sobra.
  3. Contra os PDFs oficiais do INEP (baixados automaticamente para ferramentas/_pdfs/):
     - o gabarito do pacote é igual ao gabarito oficial;
     - o texto de cada questão existe na página do PDF (detecta erro de transcrição).
Sai com código 1 se houver erro, para uso em scripts.
Dependência opcional para a etapa 3: pip install pypdf
"""
import argparse
import json
import re
import sys
import time
import unicodedata
import urllib.request
from pathlib import Path

LETRAS = ("A", "B", "C", "D", "E")
AREAS = {"Linguagens", "Ciências Humanas", "Ciências da Natureza", "Matemática"}
EXT_IMAGEM = {".png", ".jpg", ".jpeg"}
JANELA = 12                      # nº de letras por trecho na comparação com o PDF
LIMITE_TEXTO = 0.90              # abaixo disso vira ERRO; acima, qualquer trecho sem correspondência vira AVISO
CACHE = Path(__file__).resolve().parent / "_pdfs"
# Restos de diagramação que NÃO devem estar no texto (rodapé/cabeçalho de página do INEP)
LIXO = re.compile(r"(Caderno\s*\d+\s*-\s*AZUL|P[áa]gina\s*\d+\s*(de|/)\s*\d+|\*\d{4,}[A-Z0-9]*\*|^QUEST[ÃA]O\s+\d+\s*$)", re.I | re.M)


class Relatorio:
    def __init__(self):
        self.erros, self.avisos = [], []

    def erro(self, msg):
        self.erros.append(msg)

    def aviso(self, msg):
        self.avisos.append(msg)


def _fluxo(texto: str) -> str:
    t = unicodedata.normalize("NFKD", texto.lower())
    return re.sub(r"[^a-z0-9]", "", "".join(c for c in t if not unicodedata.combining(c)))


# ─── 1. Estrutura ─────────────────────────────────────────────────────────────

def _blocos(blocos, pasta: Path, onde: str, rel: Relatorio, contadores: dict):
    if not isinstance(blocos, list) or not blocos:
        rel.erro(f"{onde}: lista de blocos vazia ou inválida")
        return
    for i, b in enumerate(blocos):
        tipo = b.get("tipo")
        if tipo == "texto":
            t = b.get("texto")
            if not isinstance(t, str) or not t.strip():
                rel.erro(f"{onde} bloco {i}: texto vazio")
                continue
            if LIXO.search(t):
                rel.erro(f"{onde} bloco {i}: sobrou cabeçalho/rodapé do PDF no texto: {LIXO.search(t).group(0)!r}")
            if t != t.strip() or "  " in t:
                rel.aviso(f"{onde} bloco {i}: espaços sobrando no texto")
        elif tipo == "latex":
            if not isinstance(b.get("expressao"), str) or not b["expressao"].strip():
                rel.erro(f"{onde} bloco {i}: expressão LaTeX vazia")
            contadores["latex"] += 1
        elif tipo == "imagem":
            arq = b.get("arquivo")
            contadores["imagens"] += 1
            if not isinstance(arq, str):
                rel.erro(f"{onde} bloco {i}: imagem sem 'arquivo'")
                continue
            caminho = (pasta / arq).resolve()
            if pasta.resolve() not in caminho.parents or not caminho.is_file():
                rel.erro(f"{onde} bloco {i}: arquivo de imagem não encontrado dentro do pacote: {arq}")
            elif caminho.suffix.lower() not in EXT_IMAGEM:
                rel.erro(f"{onde} bloco {i}: formato de imagem não aceito ({caminho.suffix}); use png ou jpg")
            elif caminho.stat().st_size > 900_000:
                rel.aviso(f"{onde} bloco {i}: imagem pesada ({caminho.stat().st_size // 1024} KB): {arq}")
            if not str(b.get("descricao") or "").strip():
                rel.aviso(f"{onde} bloco {i}: imagem sem descricao")
            if not isinstance(b.get("largura_px"), int):
                rel.aviso(f"{onde} bloco {i}: imagem sem largura_px")
        else:
            rel.erro(f"{onde} bloco {i}: tipo desconhecido {tipo!r} (use texto, latex ou imagem)")


def validar_estrutura(pasta: Path, rel: Relatorio):
    try:
        dq = json.loads((pasta / "questoes.json").read_text(encoding="utf-8"))
        dg = json.loads((pasta / "gabarito.json").read_text(encoding="utf-8"))
    except (OSError, ValueError) as e:
        rel.erro(f"não consegui ler questoes.json/gabarito.json: {e}")
        return None, None
    questoes = dq.get("questoes")
    respostas = dg.get("respostas")
    if not isinstance(questoes, list) or not isinstance(respostas, list):
        rel.erro("questoes.json precisa ter a lista 'questoes' e gabarito.json a lista 'respostas'")
        return None, None

    contadores = {"imagens": 0, "latex": 0}
    ids, numeros = set(), set()
    for q in questoes:
        qid = q.get("id", "?")
        onde = f"[{qid}]"
        if qid in ids:
            rel.erro(f"{onde}: id repetido")
        ids.add(qid)
        for campo in ("ano", "dia", "caderno", "numero_original"):
            if not isinstance(q.get(campo), int):
                rel.erro(f"{onde}: campo '{campo}' ausente ou não numérico")
        if q.get("area") not in AREAS:
            rel.erro(f"{onde}: area {q.get('area')!r} inválida (use exatamente {sorted(AREAS)})")
        if q.get("idioma") is not None:
            rel.aviso(f"{onde}: questão de língua estrangeira (idioma={q['idioma']!r}); o app ainda não separa por idioma")
        if q.get("numero_original") in numeros and isinstance(q.get("numero_original"), int):
            rel.erro(f"{onde}: numero_original {q['numero_original']} repetido")
        numeros.add(q.get("numero_original"))
        fonte = q.get("fonte") or {}
        if not str(fonte.get("url_prova", "")).startswith("https://") or not isinstance(fonte.get("pagina_pdf"), int):
            rel.erro(f"{onde}: 'fonte' precisa de url_prova (https) e pagina_pdf (número)")
        _blocos(q.get("conteudo"), pasta, f"{onde} enunciado", rel, contadores)
        alts = q.get("alternativas")
        letras = [a.get("letra") for a in alts] if isinstance(alts, list) else []
        if letras != list(LETRAS):
            rel.erro(f"{onde}: alternativas devem ser exatamente A, B, C, D, E nessa ordem (veio {letras})")
        else:
            for a in alts:
                _blocos(a.get("conteudo"), pasta, f"{onde} alternativa {a['letra']}", rel, contadores)

    gab = {}
    for r in respostas:
        qid = r.get("questao_id")
        if qid in gab:
            rel.erro(f"gabarito: questao_id repetido {qid}")
        gab[qid] = r
        if r.get("situacao") not in ("valida", "anulada"):
            rel.erro(f"gabarito [{qid}]: 'situacao' deve ser valida ou anulada")
        if r.get("situacao") == "valida" and r.get("alternativa_correta") not in LETRAS:
            rel.erro(f"gabarito [{qid}]: alternativa_correta inválida {r.get('alternativa_correta')!r}")
    for qid in ids - set(gab):
        rel.erro(f"gabarito: falta resposta para {qid}")
    for qid in set(gab) - ids:
        rel.erro(f"gabarito: resposta para questão que não existe: {qid}")
    return questoes, (gab, contadores)


# ─── 2. Contra os PDFs oficiais ───────────────────────────────────────────────

def _baixar(url: str, rel: Relatorio) -> Path | None:
    CACHE.mkdir(exist_ok=True)
    destino = CACHE / url.rsplit("/", 1)[-1]
    if destino.exists() and destino.stat().st_size > 10_000:
        return destino
    for tentativa in range(4):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=60) as r:
                destino.write_bytes(r.read())
            return destino
        except Exception as e:  # noqa: BLE001
            ultimo = e
            time.sleep(2 * (tentativa + 1))
    rel.erro(f"não consegui baixar {url}: {ultimo}")
    return None


def _paginas(pdf: Path, layout: bool = False):
    """Leitor de páginas. layout=True mantém a tabela do gabarito alinhada; layout=False (leitura
    normal) é o certo para textos de questão em duas colunas, pois o modo layout intercala as colunas."""
    from pypdf import PdfReader
    leitor = PdfReader(str(pdf))
    cache = {}

    def pagina(n: int) -> str:
        if n not in cache:
            if 1 <= n <= len(leitor.pages):
                pg = leitor.pages[n - 1]
                cache[n] = pg.extract_text(extraction_mode="layout") if layout else pg.extract_text()
            else:
                cache[n] = ""
        return cache[n]
    return pagina, len(leitor.pages)


def _gabarito_oficial(texto: str) -> dict[int, str]:
    out = {}
    for linha in texto.splitlines():
        for n, g in re.findall(r"(?<!\d)(\d{1,3})\s+([A-E])(?=\s|$)", linha):
            out.setdefault(int(n), g)
    return out


def _sem_numeros_de_linha(texto: str) -> str:
    """Textos com numeração de linha (1, 2, 3... no início de cada linha, usada em perguntas como 'l. 3')
    têm os números separados do texto na leitura do PDF. Se houver pelo menos 3 linhas seguidas com
    números consecutivos, esses números iniciais são ignorados na comparação. Qualquer outro número do
    texto continua sendo comparado normalmente."""
    quebra = chr(10)
    linhas = texto.split(quebra)
    nums = []
    for ln in linhas:
        m = re.match(r"^\s*(\d{1,3})\s+\S", ln)
        nums.append(int(m.group(1)) if m else None)
    consecutivos = sum(1 for a, b in zip(nums, nums[1:]) if a is not None and b == a + 1)
    if consecutivos < 2:
        return texto
    return quebra.join(re.sub(r"^\s*\d{1,3}\s+", "", ln) if n is not None else ln for ln, n in zip(linhas, nums))


def _conferencias_manuais(pasta: Path, rel: Relatorio) -> dict[str, str]:
    """conferencias_manuais.json no pacote: {id da questão: quem/como conferiu}. Serve para texto que o PDF
    não permite comparar por código (ex.: poema que é imagem dentro do PDF) e que alguém conferiu à mão."""
    arquivo = pasta / "conferencias_manuais.json"
    if not arquivo.exists():
        return {}
    try:
        dados = json.loads(arquivo.read_text(encoding="utf-8"))
        if not isinstance(dados, dict) or not all(isinstance(v, str) and v.strip() for v in dados.values()):
            raise ValueError
        return dados
    except (OSError, ValueError):
        rel.erro("conferencias_manuais.json inválido: deve ser {id da questão: descrição de como foi conferida}")
        return {}


def validar_contra_pdf(questoes, gab, rel: Relatorio, manuais: dict | None = None) -> dict:
    try:
        import pypdf  # noqa: F401
    except ImportError:
        rel.aviso("etapa dos PDFs ignorada: instale a biblioteca com  pip install pypdf  e rode de novo")
        return {}
    por_pdf: dict[str, list] = {}
    for q in questoes:
        por_pdf.setdefault(q["fonte"]["url_prova"], []).append(q)
    estat = {"questoes": 0, "trechos": 0, "achados": 0, "gabaritos_ok": 0, "gabaritos_total": 0}
    for url_pv, qs in por_pdf.items():
        pv = _baixar(url_pv, rel)
        gb = _baixar(url_pv.replace("_PV_", "_GB_"), rel)
        if pv is None or gb is None:
            continue
        pagina_pv, _ = _paginas(pv)
        pagina_gb, n_gb = _paginas(gb, layout=True)
        oficial = _gabarito_oficial("\n".join(pagina_gb(i) for i in range(1, n_gb + 1)))
        for q in qs:
            n = q["numero_original"]
            r = gab[q["id"]]
            if r["situacao"] == "valida":
                estat["gabaritos_total"] += 1
                if oficial.get(n) == r["alternativa_correta"]:
                    estat["gabaritos_ok"] += 1
                else:
                    rel.erro(f"[{q['id']}] gabarito do pacote ({r['alternativa_correta']}) difere do oficial ({oficial.get(n)})")
            pg = q["fonte"]["pagina_pdf"]
            # texto-base pode estar na página anterior à da questão; a questão pode continuar na seguinte
            alvo = _fluxo(pagina_pv(pg - 1) + pagina_pv(pg) + pagina_pv(pg + 1))
            tot = ach = 0
            perdidos = []
            for textos in ([b["texto"] for b in q["conteudo"] if b["tipo"] == "texto"],
                           [b["texto"] for a in q["alternativas"] for b in a["conteudo"] if b["tipo"] == "texto"]):
                for t in textos:
                    f = _fluxo(_sem_numeros_de_linha(t))
                    for i in range(0, max(1, len(f) - JANELA + 1), 6):
                        tot += 1
                        if f[i:i + JANELA] in alvo:
                            ach += 1
                        else:  # guarda um pedaço do texto original, para o revisor localizar o problema
                            pos = int(i * len(t) / max(len(f), 1))
                            perdidos.append(t[max(0, pos - 12): pos + 36].replace(chr(10), " "))
            estat["questoes"] += 1
            estat["trechos"] += tot
            estat["achados"] += ach
            if perdidos:
                exemplos = " | ".join(f"«…{x}…»" for x in perdidos[:3])
                msg = (f"[{q['id']}] {len(perdidos)} trecho(s) do texto não existem na página {pg} do PDF "
                       f"({100 * ach / tot:.0f}% achado). Revise perto de: {exemplos}")
                if q["id"] in (manuais or {}):
                    rel.aviso(f"{msg} | CONFERIDA MANUALMENTE: {manuais[q['id']]}")
                elif tot and ach / tot < LIMITE_TEXTO:
                    rel.erro(msg)
                else:
                    rel.aviso(msg)
    return estat


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("pasta")
    ap.add_argument("--sem-pdf", action="store_true", help="só valida a estrutura (não baixa os PDFs do INEP)")
    args = ap.parse_args()
    pasta = Path(args.pasta).resolve()
    if not (pasta / "questoes.json").exists():
        sys.exit(f"Não achei questoes.json em {pasta}")

    rel = Relatorio()
    questoes, extra = validar_estrutura(pasta, rel)
    estat = {}
    if questoes is not None:
        gab, cont = extra
        por_area: dict[str, int] = {}
        for q in questoes:
            por_area[q.get("area", "?")] = por_area.get(q.get("area", "?"), 0) + 1
        print(f"Pacote: {pasta.name} | {len(questoes)} questões | por área: {dict(sorted(por_area.items()))}")
        print(f"        {cont['imagens']} imagens | {cont['latex']} blocos LaTeX | "
              f"{sum(1 for r in gab.values() if r.get('situacao') == 'anulada')} anulada(s)")
        if not args.sem_pdf and not rel.erros:
            estat = validar_contra_pdf(questoes, gab, rel, _conferencias_manuais(pasta, rel))
        elif not args.sem_pdf:
            print("(etapa dos PDFs adiada: corrija primeiro os erros de estrutura abaixo)")
    if estat:
        print(f"Gabarito x INEP: {estat['gabaritos_ok']}/{estat['gabaritos_total']} conferem")
        if estat["trechos"]:
            print(f"Texto x PDF: {estat['achados']}/{estat['trechos']} trechos achados ({100 * estat['achados'] / estat['trechos']:.1f}%)")
    for a in rel.avisos:
        print("AVISO:", a)
    for e in rel.erros:
        print("ERRO: ", e)
    print(f"\nResultado: {'REPROVADO' if rel.erros else 'APROVADO'} — {len(rel.erros)} erro(s), {len(rel.avisos)} aviso(s)")
    sys.exit(1 if rel.erros else 0)


if __name__ == "__main__":
    main()
