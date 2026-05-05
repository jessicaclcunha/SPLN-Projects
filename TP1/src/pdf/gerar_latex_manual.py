import json
import re
import unicodedata
from collections import Counter
from math import log
import spacy

def nfc(texto):
    return unicodedata.normalize('NFC', texto)

with open("manual_teoria_musical.json", encoding="utf-8") as f:
    artigo = json.load(f)

artigo = {nfc(k): [nfc(p) for p in v] for k, v in artigo.items()}

frases = []
for seccao in artigo:
    for paragrafo in artigo[seccao]:
        for frase in re.split(r'(?<=[.!?])\s+', paragrafo):
            if frase.strip():
                frases.append(frase.strip())

def tokenizar(texto):
    texto = texto.lower()
    texto = re.sub(r"[^\wÀ-ú\s]", " ", texto)
    return [t for t in texto.split() if len(t) >= 2]

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
V, N = len(uni), len(corpus)

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
texto_completo = "\n".join(p for seccao in artigo for p in artigo[seccao])
doc = nlp(texto_completo)

def is_valida(ent):
    texto = ent.text.strip()
    if len(texto) <= 2:
        return False
    if texto.isupper():        
        return False
    if len(texto.split()) > 5:
        return False
    ruido = {'veja', 'ver', 'exemplo', 'nota', 'tipo', 'forma'}
    return texto.lower().split()[0] not in ruido

def latex_escape(texto):
    subs = {'\u2013': '--', '\u2014': '---', '\u2018': "'", '\u2019': "'",
            '\u201c': '"', '\u201d': '"'}
    for s, r in subs.items():
        texto = texto.replace(s, r)
    texto = ''.join(c if ord(c) <= 0x00FF else '?' for c in texto)
    for char, rep in [('\\', r'\textbackslash{}'), ('&', r'\&'), ('%', r'\%'),
                      ('$', r'\$'), ('#', r'\#'), ('_', r'\_'),
                      ('{', r'\{'), ('}', r'\}'),
                      ('~', r'\textasciitilde{}'), 
                      ('^', r'\^{}')]:             
        texto = texto.replace(char, rep)
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

\title{Manual de Teoria Musical --- Análise com N-Gramas e NER}
\author{Jéssica Cunha \\ SPLN 2025/26}
\date{}

\begin{document}
\maketitle

\begin{abstract}
As três frases mais representativas do \textit{Manual de Teoria Musical} (LXPRO),
selecionadas com base num modelo de linguagem de bigramas com Laplace smoothing:

\begin{itemize}
"""

for frase in top3:
    latex += f"  \\item {latex_escape(frase)}\n"

latex += r"""\end{itemize}
\end{abstract}

\section{Fonte}
Texto extraído de:
\begin{itemize}
  \item LXPRO. \textit{Manual de Teoria Musical}. Documento PDF.
\end{itemize}

\section{Corpo do Manual}
Texto extraído do PDF com \texttt{pdftotext}. As entidades nomeadas estão anotadas
inline com \textbf{negrito} e etiqueta \textsc{[tipo]}, identificadas com spaCy
(\texttt{pt\_core\_news\_sm}).

"""

for seccao in artigo:
    latex += f"\\subsection*{{{latex_escape(seccao)}}}\n"
    for paragrafo in artigo[seccao]:
        p = anotar_entidades(latex_escape(paragrafo), doc.ents)
        latex += p + "\n\n"

latex += r"""
\begin{thebibliography}{1}
\bibitem{manual_lxpro}
LXPRO.
\textit{Manual de Teoria Musical}.
Documento PDF. Acedido em: março de 2026.
\end{thebibliography}

\end{document}
"""

with open("artigo_manual.tex", "w", encoding="utf-8") as f:
    f.write(latex)

print("Ficheiro gerado: artigo_manual.tex")
print("\nTop 3 frases:")
for i, frase in enumerate(top3, 1):
    print(f"  {i}. {frase[:80]}...")