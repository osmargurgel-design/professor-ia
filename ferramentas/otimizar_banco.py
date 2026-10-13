"""Ajusta as imagens dos arquivos de prova em banco_enem/ (rodar uma vez por arquivo novo).

O que faz em cada imagem de questão:
  1. Remove o cabeçalho do INEP ("QUESTÃO 78" + linhas azuis): o app já numera as questões.
  2. Remove o traço azul duplo do rodapé e todo o espaço branco que sobra no fim.
  3. Acrescenta uma margem branca uniforme (a imagem fica como um "cartão").
  4. Recomprime o JPEG (arquivo bem menor, texto continua nítido).

Segurança: o arquivo original é copiado para banco_enem_originais/ antes de qualquer mudança,
e arquivos já ajustados (marca "ajuste_imagens") são ignorados, então é seguro rodar de novo.

Uso (na pasta do projeto):
    python ferramentas/otimizar_banco.py                 # ajusta tudo em banco_enem/
    python ferramentas/otimizar_banco.py --saida pasta   # só gera o resultado em outra pasta (para revisar)
"""
import argparse
import base64
import io
import json
import shutil
import sys
from pathlib import Path

import numpy as np
from PIL import Image

RAIZ = Path(__file__).resolve().parent.parent
PASTA = RAIZ / "banco_enem"
BACKUP = RAIZ / "banco_enem_originais"

LIMIAR_BRANCO = 235     # abaixo disso o pixel conta como "tinta"
MARGEM = 14             # margem branca ao redor do conteúdo (px)
QUALIDADE_JPEG = 82
VERSAO_AJUSTE = 1


def _linhas_com_tinta(a: np.ndarray) -> np.ndarray:
    return (a.min(axis=2) < LIMIAR_BRANCO).any(axis=1)


def _eh_ciano(a: np.ndarray) -> np.ndarray:
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    return (b > 170) & (r < 140) & (g > 110) & (b - r > 60)


def _fim_do_cabecalho(a: np.ndarray) -> int | None:
    """Linha onde o cabeçalho do INEP termina, ou None se a imagem não tem cabeçalho."""
    tinta = _linhas_com_tinta(a)
    topo = a[:46]
    if not tinta[:20].any():
        return None
    # Cabeçalho = texto escuro à esquerda + linhas azuis à direita, nas primeiras linhas.
    esquerda_escura = (topo[:, : a.shape[1] // 3].min(axis=2) < 110).sum()
    direita_ciano = _eh_ciano(topo[:, a.shape[1] // 2:]).sum()
    if esquerda_escura < 20 or direita_ciano < 40:
        return None
    # Fim = primeira faixa de >= 5 linhas brancas a partir da linha 28.
    y = 28
    while y + 5 <= min(len(tinta), 60):
        if not tinta[y: y + 5].any():
            return y + 5
        y += 1
    return None


def _inicio_rodape(a: np.ndarray, fim_conteudo: int) -> int:
    """Se o final tiver o traço azul duplo do INEP, devolve a linha onde ele começa; senão, o fim do conteúdo."""
    tinta = _linhas_com_tinta(a)
    # Agrupa as linhas de tinta e olha os últimos grupos.
    grupos, ini = [], None
    for y in range(fim_conteudo):
        if tinta[y] and ini is None:
            ini = y
        elif not tinta[y] and ini is not None:
            grupos.append((ini, y)); ini = None
    if ini is not None:
        grupos.append((ini, fim_conteudo))
    corte = fim_conteudo
    while grupos:
        y0, y1 = grupos[-1]
        bloco = a[y0:y1]
        tinta_px = (bloco.min(axis=2) < LIMIAR_BRANCO).sum()
        if tinta_px < 30:  # pixel solto / ruído de JPEG: descarta e continua olhando para cima
            grupos.pop()
            continue
        # Traço do rodapé = linha fina azul, sem nenhum pixel escuro (texto é preto/cinza: todos os canais baixos).
        sem_texto = not (bloco.max(axis=2) < 140).any()
        so_azul = tinta_px > 0 and sem_texto and _eh_ciano(bloco).sum() > 0.3 * tinta_px
        if (y1 - y0) <= 14 and so_azul:
            corte = y0
            grupos.pop()
        else:
            break
    # corte = começo do rodapé azul; o conteúdo útil termina no fim do último grupo restante
    return grupos[-1][1] if grupos else corte


def ajustar_imagem(dados: bytes) -> tuple[bytes, dict]:
    img = Image.open(io.BytesIO(dados)).convert("RGB")
    a = np.asarray(img).astype(int)
    h0, w0 = a.shape[:2]

    topo = _fim_do_cabecalho(a) or 0
    tinta = _linhas_com_tinta(a)
    ultima = int(np.nonzero(tinta)[0].max()) + 1
    fim = _inicio_rodape(a, ultima)

    corpo = a[topo:fim]
    t = _linhas_com_tinta(corpo)
    colunas = (corpo.min(axis=2) < LIMIAR_BRANCO).any(axis=0)
    if not t.any() or not colunas.any():
        raise ValueError("imagem sem conteúdo após o ajuste")
    y0, y1 = int(np.argmax(t)), len(t) - int(np.argmax(t[::-1]))
    x0, x1 = int(np.argmax(colunas)), len(colunas) - int(np.argmax(colunas[::-1]))
    recorte = img.crop((x0, topo + y0, x1, topo + y1))

    # Margem uniforme. Se o conteúdo já ocupava (quase) toda a largura, não encolhe nada.
    tela = Image.new("RGB", (recorte.width + 2 * MARGEM, recorte.height + 2 * MARGEM), (255, 255, 255))
    tela.paste(recorte, (MARGEM, MARGEM))

    saida = io.BytesIO()
    tela.save(saida, "JPEG", quality=QUALIDADE_JPEG, optimize=True, progressive=True)
    info = {"altura_antes": h0, "altura_depois": tela.height, "cabecalho_removido": bool(topo),
            "bytes_antes": len(dados), "bytes_depois": saida.tell()}
    return saida.getvalue(), info


def processar_arquivo(origem: Path, destino: Path) -> dict | None:
    dados = json.loads(origem.read_text(encoding="utf-8"))
    if dados.get("ajuste_imagens"):
        print(f"- {origem.name}: já ajustado, ignorado")
        return None
    antes = depois = n = sem_cab = 0
    maior_corte = 0
    for q in dados["questoes"]:
        for parte in q["partes_visuais"]:
            bruto = base64.b64decode(parte["imagem_data_uri"].split(",", 1)[1])
            novo, info = ajustar_imagem(bruto)
            parte["imagem_data_uri"] = "data:image/jpeg;base64," + base64.b64encode(novo).decode()
            parte["largura"], parte["altura"] = Image.open(io.BytesIO(novo)).size
            antes += info["bytes_antes"]; depois += info["bytes_depois"]; n += 1
            sem_cab += 0 if info["cabecalho_removido"] else 1
            maior_corte = max(maior_corte, info["altura_antes"] - info["altura_depois"])
    dados["ajuste_imagens"] = {"versao": VERSAO_AJUSTE, "descricao": "cabeçalho/rodapé do INEP e espaço em branco removidos; margem uniforme; JPEG recomprimido"}
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_text(json.dumps(dados, ensure_ascii=False), encoding="utf-8")
    return {"imagens": n, "sem_cabecalho_detectado": sem_cab, "mb_antes": antes / 1e6, "mb_depois": depois / 1e6,
            "maior_corte_px": maior_corte}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--saida", help="grava os resultados nesta pasta em vez de substituir os arquivos de banco_enem/")
    args = ap.parse_args()

    arquivos = sorted(PASTA.glob("*.json"))
    if not arquivos:
        sys.exit(f"Nenhum .json em {PASTA}")
    for arq in arquivos:
        if args.saida:
            r = processar_arquivo(arq, Path(args.saida) / arq.name)
        else:
            BACKUP.mkdir(exist_ok=True)
            copia = BACKUP / arq.name
            if not copia.exists():
                shutil.copy2(arq, copia)
            r = processar_arquivo(arq, arq)
        if r:
            print(f"- {arq.name}: {r['imagens']} imagens | {r['mb_antes']:.1f} MB -> {r['mb_depois']:.1f} MB "
                  f"| sem cabeçalho detectado: {r['sem_cabecalho_detectado']} | maior corte: {r['maior_corte_px']} px")


if __name__ == "__main__":
    main()
