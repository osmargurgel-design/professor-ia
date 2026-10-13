"""Mostra como cada questão do banco foi classificada por assunto (para ajustar assuntos.py).

Uso (na pasta do projeto):
    python ferramentas/revisar_assuntos.py                # todas as questões em blocos
    python ferramentas/revisar_assuntos.py --area Linguagens
    python ferramentas/revisar_assuntos.py --sem-assunto  # só as que ficaram sem classificação
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.stdout.reconfigure(encoding="utf-8")

import assuntos  # noqa: E402
import banco_enem  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--area")
    ap.add_argument("--sem-assunto", action="store_true")
    ap.add_argument("--exportar", metavar="ARQUIVO.json",
                    help="grava um modelo {id: assunto automático} para você corrigir e salvar como banco_enem/assuntos_manuais.json")
    args = ap.parse_args()
    banco = banco_enem.carregar_banco.__wrapped__()
    if args.exportar:
        import json
        modelo = {m["id"]: m["assunto"] for m in sorted(banco["questoes"].values(), key=lambda m: (m["ano"], m["numero"]))
                  if m["formato"] == "blocos"}
        Path(args.exportar).write_text(json.dumps(modelo, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"modelo com {len(modelo)} questões gravado em {args.exportar}")
        print("Assuntos válidos por área:", {a: list(v) for a, v in assuntos.ASSUNTOS.items()})
        return
    resumo: dict[str, dict[str, int]] = {}
    for m in sorted(banco["questoes"].values(), key=lambda m: (m["area"], m["ano"], m["numero"])):
        if m["formato"] != "blocos" or (args.area and m["area"] != args.area):
            continue
        resumo.setdefault(m["area"], {})
        resumo[m["area"]][m["assunto"] or "(sem assunto)"] = resumo[m["area"]].get(m["assunto"] or "(sem assunto)", 0) + 1
        if args.sem_assunto and m["assunto"]:
            continue
        enun, alts = banco_enem.textos_da_questao(m["conteudo"], m["alternativas"])
        texto = enun
        top = assuntos.ranking(m["area"], enun, alts)[:2]
        placar = " x ".join(f"{a.split()[0]} {p:.1f}" for a, p, _ in top)
        print(f"{m['ano']} Q{m['numero']:<3} {m['area'][:9]:9} | {(m['assunto'] or '— sem assunto —'):38} | {placar:28} | {texto[:95]!r}")
    print()
    for area, c in resumo.items():
        print(area, "->", dict(sorted(c.items())))


if __name__ == "__main__":
    main()
