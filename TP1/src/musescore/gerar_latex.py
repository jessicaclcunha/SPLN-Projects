import json
import re
import unicodedata
from collections import Counter
from math import log
import spacy

def nfc(texto):
    """Normalizar para NFC — garante chars compostos (ç em vez de c+cedilha)."""
    return unicodedata.normalize('NFC', texto)

with open("musescore_glossario.json", encoding="utf-8") as f:
    glossario_raw = json.load(f)

glossario = {}
for letra in glossario_raw:
    glossario[nfc(letra)] = {}
    for termo in glossario_raw[letra]:
        entrada = glossario_raw[letra][termo]
        glossario[nfc(letra)][nfc(termo)] = {
            "definicao": nfc(entrada["definicao"]),
            "variante": entrada["variante"],
            "musescore_especifico": entrada["musescore_especifico"]
        }

def limpar(texto):
    texto = texto.lower()
    texto = re.sub(r"[^\wÀ-ú\s]", " ", texto)
    texto = re.sub(r"\s+", " ", texto)
    return texto.strip()

def tokenizar(texto):
    return [t for t in limpar(texto).split() if len(t) >= 2]

frases = []
for letra in glossario:
    for termo in glossario[letra]:
        definicao = glossario[letra][termo]["definicao"]
        if definicao:
            frases.append(definicao)

corpus = []
frases_tokenizadas = []
for frase in frases:
    tokens = tokenizar(frase)
    if tokens:
        frases_tokenizadas.append((frase, tokens))
        corpus.extend(tokens)

def build_ngrams(tokens, n):
    return Counter(tuple(tokens[i:i+n]) for i in range(len(tokens) - n + 1))

uni = build_ngrams(corpus, 1)
bi  = build_ngrams(corpus, 2)
V   = len(uni)
N   = len(corpus)

def p2(w1, w2):
    return (bi.get((w1, w2), 0) + 1) / (uni.get((w1,), 0) + V)

def score_frase(tokens):
    if len(tokens) < 8:
        return float('-inf')
    score = sum(log(p2(tokens[i], tokens[i+1])) for i in range(len(tokens) - 1))
    return score / (len(tokens) - 1)

frases_scored = sorted(
    [(score_frase(tokens), frase) for frase, tokens in frases_tokenizadas],
    reverse=True
)
top3 = [frase for _, frase in frases_scored[:3]]

nlp = spacy.load("pt_core_news_sm")

texto_completo = "\n".join(frases)
doc = nlp(texto_completo)

def is_valida(ent):
    texto = ent.text.strip()
    if len(texto) <= 2:
        return False
    if texto.isupper():
        return False
    if len(texto.split()) > 5:
        return False
    ruido = {'veja', 'consulte', 'inserindo', 'indica', 'altera',
             'usado', 'trabalhando', 'ligado', 'criar', 'preencher',
             'excluir', 'implodir', 'contrast', 'see', 'meaning'}
    return texto.lower().split()[0] not in ruido

def latex_escape(texto):
    substituicoes = {
        '\u2011': '-',
        '\u2013': '--',
        '\u2014': '---',
        '\u2192': '->',
        '\u266f\u266f': '(duplo sustenido)',
        '\u1d12a': '(duplo sustenido)',
        '\u266d\u266d': '(duplo bemol)',
        '\u1d12b': '(duplo bemol)',
        '\u266f': '(sustenido)',
        '\u266d': '(bemol)',
        '\u266e': '(bequadro)',
        '\u1d110': '(respiracao)',
        '\u1d111': '(caesura)',
    }
    for s, rep in substituicoes.items():
        texto = texto.replace(s, rep)
    texto = ''.join(c if ord(c) <= 0x00FF else '?' for c in texto)
    texto = texto.replace('\\', r'\textbackslash{}')
    texto = texto.replace('&', r'\&')
    texto = texto.replace('%', r'\%')
    texto = texto.replace('$', r'\$')
    texto = texto.replace('#', r'\#')
    texto = texto.replace('_', r'\_')
    texto = texto.replace('{', r'\{')
    texto = texto.replace('}', r'\}')
    texto = texto.replace('~', r'\textasciitilde{}')
    texto = texto.replace('^', r'\^{}')
    return texto

def anotar_entidades(texto, ents):
    vistas = {}
    for e in ents:
        if is_valida(e) and e.text not in vistas:
            vistas[e.text] = e.label_

    entidades = sorted(vistas.items(), key=lambda x: len(x[0]), reverse=True)

    placeholders = {}
    for i, (nome, label) in enumerate(entidades):
        nome_esc = latex_escape(nome)
        if nome_esc not in texto:
            continue
        ph = f"PLCHLDR{i:04d}PLCHLDR"
        texto = texto.replace(nome_esc, ph)
        placeholders[ph] = f"\\textbf{{{nome_esc}}}\\textsc{{[{label}]}}"

    for ph, markup in placeholders.items():
        texto = texto.replace(ph, markup)

    return texto

latex = r"""\documentclass[a4paper,12pt]{article}
\usepackage[T1]{fontenc}
\usepackage[utf8]{inputenc}
\usepackage[portuguese]{babel}
\usepackage{hyperref}

\title{Glossário do MuseScore Studio}
\author{Jéssica Cunha \\ SPLN 2025/26}
\date{}

\begin{document}
\maketitle

\begin{abstract}
As três frases mais representativas do glossário, selecionadas com base
num modelo de linguagem de bigramas com Laplace smoothing:

\begin{itemize}
"""

for frase in top3:
    latex += f"  \\item {latex_escape(frase)}\n"

latex += r"""\end{itemize}
\end{abstract}

\section{Fonte}
Glossário recolhido de:
\begin{itemize}
  \item \url{https://handbook.musescore.org/pt_br/appendix/glossary}
\end{itemize}

\section{Corpo do Glossário}
Definições extraídas do glossário do MuseScore Studio Handbook.
As entidades nomeadas estão anotadas inline com \textbf{negrito}
e etiqueta \textsc{[tipo]}, identificadas com spaCy (\texttt{pt\_core\_news\_sm}).

"""

for letra in glossario:
    latex += f"\\subsection*{{{latex_escape(letra)}}}\n"
    for termo in glossario[letra]:
        definicao  = glossario[letra][termo]["definicao"]
        variante   = glossario[letra][termo]["variante"]
        especifico = glossario[letra][termo]["musescore_especifico"]

        label = latex_escape(termo)
        if variante:
            label += f" ({variante})"
        if especifico:
            label += r" $\star$"

        latex += f"\\textbf{{{label}}}"
        if definicao:
            definicao_escaped = latex_escape(definicao)
            definicao_anotada = anotar_entidades(definicao_escaped, doc.ents)
            latex += f" --- {definicao_anotada}"
        latex += "\n\n"

latex += r"""
\begin{thebibliography}{1}
\bibitem{musescore}
MuseScore Studio Handbook.
\textit{Glossário}.
Disponível em: \url{https://handbook.musescore.org/pt_br/appendix/glossary}.
Acedido em: março de 2026.
\end{thebibliography}

\end{document}
"""

with open("artigo_musescore.tex", "w", encoding="utf-8") as f:
    f.write(latex)

print("Ficheiro gerado: artigo_musescore.tex")
print(f"\nTop 3 frases escolhidas:")
for i, frase in enumerate(top3, 1):
    print(f"  {i}. {frase[:80]}...")