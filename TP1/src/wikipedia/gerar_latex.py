import json
import re
import unicodedata
from collections import Counter
from math import log
import spacy

def nfc(texto):
    """Normalizar para NFC — garante chars compostos (ç em vez de c+cedilha)."""
    return unicodedata.normalize('NFC', texto)

with open("wikipedia_musica.json", encoding="utf-8") as f:
    artigo_raw = json.load(f)

artigo = {}
for seccao in artigo_raw:
    artigo[nfc(seccao)] = [nfc(p) for p in artigo_raw[seccao]]

def limpar(texto):
    texto = texto.lower()
    texto = re.sub(r"[^\wÀ-ú\s]", " ", texto)
    texto = re.sub(r"\s+", " ", texto)
    return texto.strip()

def tokenizar(texto):
    return [t for t in limpar(texto).split() if len(t) >= 2]

frases = []
for seccao in artigo:
    for paragrafo in artigo[seccao]:
        for frase in re.split(r'(?<=[.!?])\s+', paragrafo):
            frase = frase.strip()
            if frase:
                frases.append(frase)

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
doc = nlp(texto_completo[:100_000])  # spaCy tem limite de tamanho

def is_valida(ent):
    texto = ent.text.strip()
    if len(texto) <= 2:
        return False
    if len(texto.split()) > 5:
        return False
    ruido = {'veja', 'ver', 'exemplo', 'nota', 'tipo', 'forma',
             'consulte', 'indica', 'usado', 'criar'}
    return texto.lower().split()[0] not in ruido

def latex_escape(texto):
    subs = {
        '\u2013': '--',    # en-dash
        '\u2014': '---',   # em-dash
        '\u201c': '``',    # aspas abertas
        '\u201d': "''",    # aspas fechadas
        '\u2018': '`',     # aspa simples
        '\u2019': "'",     # aspa simples
        '\u2026': '...',   # reticências
    }
    for s, r in subs.items():
        texto = texto.replace(s, r)
    texto = ''.join(c if ord(c) <= 255 else '?' for c in texto)

    for char, rep in [('\\', r'\textbackslash{}'), ('&', r'\&'), ('%', r'\%'),
                      ('$', r'\$'), ('#', r'\#'), ('_', r'\_'),
                      ('{', r'\{'), ('}', r'\}'), ('~', r'\textasciitilde{}'),
                      ('^', r'\^{}')]:
        texto = texto.replace(char, rep)
    return texto

def anotar_entidades(texto, ents):
    """Anota entidades inline: \textbf{entidade}\textsc{[TIPO]}
    Deduplica entidades e substitui todas as ocorrências no texto."""
    vistas = {}
    for e in ents:
        if is_valida(e) and e.text not in vistas:
            vistas[e.text] = e.label_
    for nome, label in sorted(vistas.items(), key=lambda x: len(x[0]), reverse=True):
        nome_escaped = latex_escape(nome)
        marcado = f"\\textbf{{{nome_escaped}}}\\textsc{{[{label}]}}"
        texto = texto.replace(nome_escaped, marcado)
    return texto

latex = r"""\documentclass[a4paper,12pt]{article}
\usepackage[T1]{fontenc}
\usepackage[utf8]{inputenc}
\usepackage[portuguese]{babel}
\usepackage{hyperref}

\title{Música --- Análise com Modelos de Linguagem N-Gram e NER}
\author{Jéssica Cunha \\ SPLN 2025/26}
\date{}

\begin{document}
\maketitle

\begin{abstract}
As três frases mais representativas do artigo da Wikipédia sobre
\textit{Música}, selecionadas com base num modelo de linguagem
de bigramas com Laplace smoothing:

\begin{itemize}
"""

for frase in top3:
    latex += f"  \\item {latex_escape(frase)}\n"

latex += r"""\end{itemize}
\end{abstract}

\section{Fonte}
Texto recolhido de:
\begin{itemize}
  \item \url{https://pt.wikipedia.org/wiki/M\%C3\%BAsica}
\end{itemize}

\section{Corpo do Artigo}
Texto extraído da Wikipédia, organizado por secção.
As entidades nomeadas estão anotadas inline com \textbf{negrito}
e etiqueta \textsc{[tipo]}, identificadas com spaCy (\texttt{pt\_core\_news\_sm}).

"""

for seccao in artigo:
    latex += f"\\subsection*{{{latex_escape(seccao)}}}\n"
    for paragrafo in artigo[seccao]:
        p_escaped = latex_escape(paragrafo)
        p_anotado = anotar_entidades(p_escaped, doc.ents)
        latex += p_anotado + "\n\n"

latex += r"""
\begin{thebibliography}{1}
\bibitem{wikipedia_musica}
Wikipédia.
\textit{Música}.
Disponível em: \url{https://pt.wikipedia.org/wiki/M\%C3\%BAsica}.
Acedido em: março de 2026.
\end{thebibliography}

\end{document}
"""

with open("artigo_wikipedia_musica.tex", "w", encoding="utf-8") as f:
    f.write(latex)

print("Ficheiro gerado: artigo_wikipedia_musica.tex")
print(f"\nTop 3 frases escolhidas:")
for i, frase in enumerate(top3, 1):
    print(f"  {i}. {frase[:80]}...")