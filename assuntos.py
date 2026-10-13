"""Classificação das questões do ENEM por assunto, em Python puro (sem IA).

Cada área do ENEM tem uma lista de assuntos; cada assunto tem palavras-chave com um peso.
A questão recebe o assunto de maior pontuação, mas só se a vitória for clara. Na dúvida ela fica
sem assunto (None), porque é melhor não classificar do que classificar errado.

Como ajustar: edite os dicionários abaixo (palavras sem acento, em minúsculas) e rode
    python ferramentas/revisar_assuntos.py
para ver como cada questão foi classificada.
"""
import re
import unicodedata

PONTUACAO_MINIMA = 3     # pontos que o assunto vencedor precisa ter
VANTAGEM_MINIMA = 2      # pontos de diferença para o segundo colocado
MAX_POR_TERMO = 2        # um termo repetido muitas vezes não domina a pontuação
PESO_ALTERNATIVAS = 0.3  # as alternativas têm "distratores" de outros assuntos: pesam bem menos que o enunciado

# {área: {assunto: {palavra-chave: peso}}}. Cada palavra casa com o INÍCIO de uma palavra do texto
# ("colon" casa com "colonial" e "colonização"). Pesos: 1 = pista fraca, 2 = pista forte, 3 = quase exclusiva.
ASSUNTOS: dict[str, dict[str, dict[str, int]]] = {
    "Ciências Humanas": {
        "História": {
            "imperador": 2, "realeza": 2, "patricio": 3, "plebe": 3, "romano": 2, "polis": 2, "coulanges": 3, "hobsbawm": 3, "sergio buarque": 3, "caio prado": 3, "boris fausto": 3, "eleitor": 1, "imperio": 2, "imperial": 2, "colonia": 2, "colonial": 2, "colonizac": 2, "escravid": 3, "escravo": 2,
            "escraviz": 3, "abolic": 3, "monarquia": 2, "republica velha": 3, "ditadura": 2, "golpe": 2,
            "regime militar": 3, "estado novo": 3, "getulio": 3, "vargas": 3, "revolucao": 2, "guerra mundial": 3,
            "guerra fria": 3, "nazis": 3, "fascis": 3, "feudal": 3, "feudalismo": 3, "idade media": 3,
            "medieval": 3, "renascimento": 2, "inquisic": 3, "absolutis": 3, "napoleon": 3, "revolucao francesa": 3,
            "revolucao industrial": 3, "antiguidade": 3, "imperio romano": 3, "egito antigo": 3, "cruzada": 3,
            "independencia": 2, "bandeirante": 3, "capitania": 3, "coroa portuguesa": 3, "periodo colonial": 3,
            "seculo xix": 2, "seculo xviii": 2, "seculo xvi": 2, "seculo xvii": 2, "navegac": 2,
            "descobrimento": 2, "imigrac": 1, "historiador": 2, "passado": 1,
            "patrimonio historico": 3,
        },
        "Geografia": {
            "milton santos": 3, "ab saber": 3, "relevo": 3, "clima": 2, "climatic": 3, "bioma": 3, "vegetac": 2, "cerrado": 2, "amazonia": 1,
            "caatinga": 3, "mata atlantica": 3, "pantanal": 3, "urbaniza": 3, "metropole": 2, "metropolitana": 2,
            "migrac": 2, "territorio": 1, "territorial": 1, "populac": 1, "demograf": 3, "desmatamento": 3,
            "agropecuaria": 3, "agronegocio": 3, "hidrografic": 3, "bacia": 2, "cartograf": 3, "mapa": 2,
            "latitude": 3, "longitude": 3, "globalizac": 1, "geopolit": 3, "fronteira": 1, "energia": 1,
            "recursos naturais": 3, "solo": 1, "erosao": 3, "aquecimento global": 3, "efeito estufa": 3,
            "industrializac": 1, "espaco geografico": 3, "paisagem": 2, "regiao": 1, "cidade": 1, "urbano": 1,
            "rural": 1, "reforma agraria": 3, "commodities": 3, "imagem de satelite": 3, "satelite": 2,
            "oceano": 1, "continente": 1, "ocupacao do solo": 3, "geografia": 2, "ambiental": 1, "agricultura": 1,
            "queimada": 2, "maritimo": 1, "mobilidade urbana": 3,
        },
        "Filosofia": {
            "filosof": 3, "bobbio": 3, "marcuse": 3, "adorno": 3, "horkheimer": 3, "habermas": 3, "heraclito": 3, "bentham": 3, "stuart mill": 3, "montesquieu": 3, "voltaire": 2, "tocqueville": 3, "biopolitica": 3, "etica": 3, "etico": 3, "moral": 2, "kant": 3, "aristoteles": 3, "platao": 3,
            "socrates": 3, "descartes": 3, "hobbes": 3, "locke": 3, "rousseau": 3, "nietzsche": 3,
            "existencial": 3, "sartre": 3, "foucault": 3, "arendt": 3, "maquiavel": 3, "metafisic": 3,
            "epistemolog": 3, "conhecimento": 1, "verdade": 1, "virtude": 2, "felicidade": 1,
            "contrato social": 3, "imperativo categorico": 3, "utilitaris": 3, "relativismo": 2,
            "senso comum": 2, "dialetica": 2, "hegel": 3, "estetica": 2, "razao": 1, "iluminis": 1,
            "pensador": 1, "pensamento": 1, "liberdade": 1, "autonomia": 1, "ceticismo": 3, "retorica": 2,
            "ideologia": 1, "racionalidade": 2, "politica": 1, "justica": 1,
        },
        "Sociologia": {
            "sociolog": 3, "gramsci": 3, "bauman": 3, "bourdieu": 3, "giddens": 3, "simmel": 3, "levi strauss": 3, "geertz": 3, "gilberto freyre": 3, "darcy ribeiro": 3, "florestan": 3, "durkheim": 3, "weber": 3, "marx": 2, "desigualdade": 2, "classe social": 3,
            "classes sociais": 3, "movimento social": 3, "movimentos sociais": 3, "cidadania": 2,
            "identidade": 1, "cultura": 1, "preconceito": 2, "racismo": 3, "discriminac": 2, "genero": 1,
            "capitalis": 2, "consumo": 1, "midia": 1, "redes sociais": 1, "violencia": 1, "direitos humanos": 3,
            "democracia": 1, "estado": 0, "poder": 0, "instituic": 1, "sociedade": 1, "socializac": 2,
            "diversidade": 1, "etnia": 2, "exclusao": 2, "juventude": 1, "religiao": 1, "trabalhador": 1,
            "sindicat": 3, "mercado de trabalho": 3, "precarizac": 3, "participacao politica": 2,
            "movimento": 0, "minorias": 2, "feminis": 3, "mulheres": 1, "indigena": 1, "quilombola": 2,
            "desigualdades": 2, "mobilidade social": 3, "cultura de massa": 3, "industria cultural": 3,
        },
    },
    "Ciências da Natureza": {
        "Biologia": {
            "celula": 3, "celular": 2, "dna": 3, "genetic": 3, "gene": 2, "genes": 2, "evoluc": 2, "ecolog": 3,
            "ecossistema": 3, "fotossintese": 3, "bacteria": 3, "virus": 3, "vacina": 3, "doenca": 2,
            "especie": 2, "cadeia alimentar": 3, "hormonio": 3, "imunolog": 3, "sistema imune": 3, "enzima": 3,
            "organismo": 2, "planta": 2, "animal": 1, "biodiversidade": 3, "metabolic": 2, "metabolismo": 3,
            "mitose": 3, "meiose": 3, "cromossomo": 3, "proteina": 2, "fungo": 3, "parasita": 3, "ciclo de vida": 2,
            "seres vivos": 3, "circadiano": 3, "relogio biologico": 3, "mortalidade": 1, "gestac": 2,
            "microrganismo": 3, "reproduc": 1, "habitat": 2, "predador": 3, "populac": 0, "peixe": 1,
            "glandula": 2, "bexiga natatoria": 3, "respirac": 1, "sangue": 1, "tecido": 1, "biolog": 3,
        },
        "Química": {
            "reacao quimica": 3, "solucao": 1, "concentrac": 2, "mol ": 3, "acido": 2, "base ": 0, "ph ": 2,
            "ligac": 1, "atomo": 3, "molecul": 2, "eletron": 2, "oxidac": 3, "organic": 1, "hidrocarboneto": 3,
            "polimero": 3, "substancia": 2, "soluto": 3, "solvente": 3, "combustivel": 1, "equilibrio quimico": 3,
            "cinetica": 3, "eletroquimic": 3, "pilha": 2, "destilac": 3, "mistura": 1, "composto": 2, "elemento quimico": 3,
            "tabela periodica": 3, "carvao": 1, "adsorc": 3, "filtrac": 1, "purificac": 1, "poluente": 1,
            "catalisador": 3, "ionic": 3, "ion ": 2, "sal ": 1, "quimic": 2, "titulac": 3, "isomeria": 3,
        },
        "Física": {
            "velocidade": 2, "aceleracao": 3, "forca": 1, "energia": 1, "trabalho": 0, "potencia": 1, "calor": 2,
            "temperatura": 1, "termic": 2, "onda": 2, "som ": 1, "luz ": 1, "optica": 3, "lente": 3, "espelho": 3,
            "eletric": 2, "corrente": 1, "tensao": 2, "resistor": 3, "resistencia eletrica": 3,
            "campo magnetico": 3, "gravita": 3, "pressao": 1, "queda": 1, "movimento": 1, "newton": 3, "joule": 3,
            "watt": 3, "circuito": 3, "refrac": 3, "difrac": 3, "radiac": 2, "frequencia": 1, "inercia": 3,
            "massa": 1, "voltagem": 3, "capacitor": 3, "magnet": 2, "fisica": 2, "mecanica": 2, "termodinamic": 3,
        },
    },
    "Linguagens": {
        "Literatura": {
            "poema": 3, "poesia": 3, "poeta": 3, "romance": 2, "modernismo": 3, "romantismo": 3, "realismo": 3,
            "naturalismo": 3, "parnasian": 3, "simbolismo": 3, "barroco": 3, "arcadismo": 3, "conto": 2,
            "cronica": 2, "verso": 2, "versos": 2, "soneto": 3, "eu lirico": 3, "narrador": 2, "personagem": 2,
            "prosa": 3, "escritor": 2, "escritora": 2, "literari": 3, "literatura": 3, "machado de assis": 3,
            "drummond": 3, "clarice lispector": 3, "guimaraes rosa": 3, "cordel": 3, "estrofe": 3, "rima": 3,
            "obra literaria": 3, "autor": 1, "autora": 1, "enredo": 2, "trecho do livro": 2,
        },
        "Língua portuguesa e variação linguística": {
            "variedade linguistica": 3, "variacao linguistica": 3, "norma padrao": 3, "norma culta": 3,
            "gramati": 3, "coesao": 3, "coerencia": 2, "conectivo": 3, "pronome": 3, "verbo": 2, "oracao": 2,
            "sintax": 3, "concordancia": 3, "registro": 1, "giria": 3, "oralidade": 3, "linguagem verbal": 2,
            "funcao da linguagem": 3, "metalinguagem": 3, "pontuacao": 3, "regencia": 3, "figura de linguagem": 3,
            "metafora": 3, "ironia": 2, "denotativ": 3, "conotativ": 3, "neologismo": 3, "estrangeirismo": 3,
            "organizacao coesiva": 3, "referente": 2, "termo": 1, "expressao": 1, "palavra": 1, "lingua portuguesa": 3,
            "idioma": 2, "falantes": 2, "dialeto": 3, "sotaque": 3, "linguistic": 2, "lexical": 3, "vocabulo": 2,
        },
        "Artes e cultura corporal": {
            "pintura": 3, "escultura": 3, "obra de arte": 3, "artista": 2, "museu": 2, "cinema": 2, "teatro": 3,
            "danca": 3, "musica": 2, "fotografia": 2, "instalacao": 2, "grafite": 3, "arquitetura": 2,
            "esporte": 3, "atividade fisica": 3, "capoeira": 3, "ginastica": 3, "corpo": 1, "lazer": 2,
            "paralimp": 3, "atleta": 3, "exercicio fisico": 3, "olimp": 2, "jogos": 1, "futebol": 3,
            "arte ": 2, "artistico": 2, "tela ": 1, "oleo sobre tela": 3, "gravura": 3, "cancao": 2, "melodia": 3,
            "ritmo": 2, "coreografia": 3, "festa popular": 3, "carnaval": 3, "artesanato": 3, "design": 1,
        },
        "Mídia, tecnologia e gêneros textuais": {
            "internet": 2, "redes sociais": 2, "midia": 2, "digital": 2, "tecnologia": 1, "aplicativo": 3,
            "algoritmo": 3, "fake news": 3, "comunicacao": 1, "publicidade": 3, "propaganda": 3, "cartaz": 3,
            "campanha": 2, "charge": 3, "tirinha": 3, "reportagem": 2, "noticia": 2, "artigo de opiniao": 3,
            "anuncio": 3, "infografico": 2, "blog": 3, "post ": 2, "meme": 3, "jornal": 1, "revista": 1,
            "texto instrucional": 3, "manual": 2, "bula": 3, "receita": 2, "carta ": 1, "lei ": 1, "artigo ": 1,
            "genero textual": 3, "generos textuais": 3, "slogan": 3, "argumento": 1, "leitor": 1, "internauta": 3,
        },
    },
    "Matemática": {
        "Geometria": {
            "area ": 1, "volume": 3, "angulo": 3, "triangulo": 3, "circulo": 3, "circunferencia": 3, "prisma": 3,
            "cilindro": 3, "esfera": 3, "cone ": 3, "piramide": 3, "perimetro": 3, "plano cartesiano": 3,
            "simetria": 3, "projec": 3, "retangulo": 3, "quadrado": 2, "losango": 3, "trapezio": 3, "diagonal": 2,
            "cubo": 3, "geometric": 3, "reta ": 1, "paralel": 2, "perpendicular": 3, "raio": 2, "diametro": 3,
            "hipotenusa": 3, "seno": 2, "cosseno": 3, "tangente": 2, "coordenadas": 2, "vista superior": 3,
        },
        "Estatística e probabilidade": {
            "probabilidade": 3, "media": 1, "mediana": 3, "moda": 2, "desvio padrao": 3, "variancia": 3,
            "frequencia": 2, "amostra": 3, "estatistic": 3, "grafico": 1, "tabela": 1, "aleatoriamente": 3,
            "sorteio": 2, "sorteado": 2, "pesquisa": 1, "entrevistados": 2, "histograma": 3, "chance": 2,
            "percentil": 3, "dados": 1, "internautas": 1, "levantamento": 2,
        },
        "Álgebra e funções": {
            "funcao": 3, "equacao": 3, "inequacao": 3, "polinomio": 3, "raiz": 1, "progressao aritmetica": 3,
            "progressao geometrica": 3, "logaritmo": 3, "exponencial": 3, "parabola": 3, "vertice": 2, "incognita": 3,
            "sistema de equacoes": 3, "grafico da funcao": 3, "expressao algebrica": 3, "taxa de variacao": 2,
            "variavel": 2, "modelo matematico": 3, "sequencia": 2, "termo geral": 3, "crescente": 2, "decrescente": 2,
        },
        "Aritmética, proporção e finanças": {
            "porcentagem": 3, "por cento": 3, "razao": 2, "proporcao": 3, "proporcional": 3, "regra de tres": 3,
            "juros": 3, "desconto": 3, "escala": 2, "velocidade media": 3, "fracao": 3, "mmc": 3, "mdc": 3,
            "preco": 2, "custo": 2, "lucro": 3, "prestac": 3, "financ": 3, "reais": 2, "r$": 2, "consumo": 1,
            "litros": 1, "quilometros": 1, "kg": 1, "unidade de medida": 3, "conversao": 3, "gasto": 2,
            "orcamento": 3, "compra": 1, "mensal": 2, "salario": 3, "imposto": 3, "combustivel": 1,
        },
        "Análise combinatória": {
            "combinac": 3, "permutac": 3, "arranjo": 3, "anagrama": 3, "maneiras diferentes": 3, "senhas": 2,
            "de quantas formas": 3, "de quantas maneiras": 3, "possibilidades": 2, "principio multiplicativo": 3,
            "ordem importa": 3, "fatorial": 3, "agrupamentos": 3,
        },
    },
}


def normalizar(texto: str) -> str:
    """Minúsculas, sem acento, só letras/números/cifrão separados por um espaço (e espaço no fim)."""
    t = unicodedata.normalize("NFKD", texto.lower())
    t = "".join(c for c in t if not unicodedata.combining(c))
    return " " + re.sub(r"[^a-z0-9$]+", " ", t).strip() + " "


def _compilar() -> dict[str, dict[str, list[tuple[re.Pattern, int, str]]]]:
    saida: dict[str, dict[str, list[tuple[re.Pattern, int, str]]]] = {}
    for area, assuntos in ASSUNTOS.items():
        saida[area] = {}
        for assunto, termos in assuntos.items():
            lista = []
            for termo, peso in termos.items():
                if peso <= 0:
                    continue
                # o termo casa no começo de uma palavra; um espaço no fim do termo exige palavra inteira
                padrao = r"(?<![a-z0-9])" + re.escape(termo.rstrip()) + (r"(?![a-z0-9])" if termo.endswith(" ") else "")
                lista.append((re.compile(padrao), peso, termo.strip()))
            saida[area][assunto] = lista
    return saida


_PADROES = _compilar()


def pontuar(area: str, texto: str) -> dict[str, tuple[int, list[str]]]:
    """Pontuação de cada assunto da área para o texto: {assunto: (pontos, termos que casaram)}."""
    t = normalizar(texto)
    resultado = {}
    for assunto, padroes in _PADROES.get(area, {}).items():
        pontos, achados = 0, []
        for padrao, peso, termo in padroes:
            n = len(padrao.findall(t))
            if n:
                pontos += peso * min(n, MAX_POR_TERMO)
                achados.append(termo)
        resultado[assunto] = (pontos, achados)
    return resultado


def ranking(area: str, enunciado: str, alternativas: str = "") -> list[tuple[str, float, list[str]]]:
    """Assuntos da área do mais para o menos provável: [(assunto, pontos, termos)]."""
    do_enunciado = pontuar(area, enunciado)
    das_alternativas = pontuar(area, alternativas) if alternativas else {}
    saida = []
    for assunto, (p, termos) in do_enunciado.items():
        pa, ta = das_alternativas.get(assunto, (0, []))
        saida.append((assunto, p + PESO_ALTERNATIVAS * pa, termos + [f"({t})" for t in ta if t not in termos]))
    return sorted(saida, key=lambda x: x[1], reverse=True)


def classificar(area: str, enunciado: str, alternativas: str = "") -> str | None:
    """Assunto da questão, ou None se não houver um vencedor claro."""
    r = ranking(area, enunciado, alternativas)
    if not r:
        return None
    melhor, p1, _ = r[0]
    p2 = r[1][1] if len(r) > 1 else 0
    if p1 >= PONTUACAO_MINIMA and p1 - p2 >= VANTAGEM_MINIMA:
        return melhor
    return None
