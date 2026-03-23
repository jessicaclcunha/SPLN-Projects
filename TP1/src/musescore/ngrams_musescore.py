import json
import re
from collections import Counter
from math import log

with open("musescore_glossario.json", encoding="utf-8") as f:
    glossario = json.load(f)

frases = []
for letra in glossario:
    for termo in glossario[letra]:
        definicao = glossario[letra][termo]["definicao"]
        if definicao:
            frases.append(definicao)

print(f"Total de definições: {len(frases)}")

def limpar(texto):
    texto = texto.lower()
    texto = re.sub(r"[^\wÀ-ú\s]", " ", texto)  # manter letras e acentos
    texto = re.sub(r"\s+", " ", texto)
    return texto.strip()

def tokenizar(texto):
    return [t for t in limpar(texto).split() if len(t) >= 2]

corpus = []
frases_tokenizadas = []

for frase in frases:
    tokens = tokenizar(frase)
    if tokens:
        frases_tokenizadas.append((frase, tokens))
        corpus.extend(tokens)

V = len(set(corpus))  # tamanho do vocabulário
N = len(corpus)       # total de tokens

print(f"Total de tokens     : {N}")
print(f"Vocabulário         : {V}")

def build_ngrams(tokens, n):
    return Counter(tuple(tokens[i:i+n]) for i in range(len(tokens) - n + 1))

uni = build_ngrams(corpus, 1)
bi  = build_ngrams(corpus, 2)
tri = build_ngrams(corpus, 3)

print(f"Unigramas           : {len(uni)}")
print(f"Bigramas            : {len(bi)}")
print(f"Trigramas           : {len(tri)}")

print("\nTop-10 bigramas:")
for (w1, w2), c in bi.most_common(10):
    print(f"  '{w1} {w2}'  →  {c}×")

def p1(w):
    return (uni.get((w,), 0) + 1) / (N + V)

def p2(w1, w2):
    return (bi.get((w1, w2), 0) + 1) / (uni.get((w1,), 0) + V)

def p3(w1, w2, w3):
    return (tri.get((w1, w2, w3), 0) + 1) / (bi.get((w1, w2), 0) + V)

def score_frase(tokens):
    if len(tokens) < 8:
        return float('-inf')
    score = 0
    for i in range(len(tokens) - 1):
        score += log(p2(tokens[i], tokens[i+1]))
    return score / (len(tokens) - 1)

frases_scored = []
for frase, tokens in frases_tokenizadas:
    s = score_frase(tokens)
    frases_scored.append((s, frase))

frases_scored.sort(reverse=True)

print("\n--- Top 3 frases mais representativas ---")
for i, (s, frase) in enumerate(frases_scored[:3], 1):
    print(f"\n{i}. (score={s:.4f})")
    print(f"   {frase}")

print("\n--- Bottom 3 frases menos representativas ---")
validas = [(s, f) for s, f in frases_scored if s != float('-inf')]
for i, (s, frase) in enumerate(validas[-3:], 1):
    print(f"\n{i}. (score={s:.4f})")
    print(f"   {frase}")