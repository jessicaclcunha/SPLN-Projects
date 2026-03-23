import json
import re
from collections import Counter
from math import log

with open("wikipedia_musica.json", encoding="utf-8") as f:
    artigo = json.load(f)

# Extrair frases de todos os parágrafos
frases = []
for seccao in artigo:
    for paragrafo in artigo[seccao]:
        for frase in re.split(r'(?<=[.!?])\s+', paragrafo):
            if frase.strip():
                frases.append(frase.strip())

print(f"Total de frases: {len(frases)}")

# Tokenização
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

V = len(set(corpus))
N = len(corpus)
print(f"Tokens: {N}  |  Vocabulário: {V}")

# Construção dos n-gramas
def build_ngrams(tokens, n):
    return Counter(tuple(tokens[i:i+n]) for i in range(len(tokens) - n + 1))

uni = build_ngrams(corpus, 1)
bi  = build_ngrams(corpus, 2)

print(f"Unigramas: {len(uni)}  |  Bigramas: {len(bi)}")

print("\nTop-10 bigramas:")
for (w1, w2), c in bi.most_common(10):
    print(f"  '{w1} {w2}'  →  {c}×")

# Probabilidade bigrama com Laplace smoothing
def p2(w1, w2):
    return (bi.get((w1, w2), 0) + 1) / (uni.get((w1,), 0) + V)

# Score de uma frase (log-prob média dos bigramas)
def score_frase(tokens):
    if len(tokens) < 8:
        return float('-inf')
    score = sum(log(p2(tokens[i], tokens[i+1])) for i in range(len(tokens) - 1))
    return score / (len(tokens) - 1)

# Ordenar frases por score
frases_scored = sorted(
    [(score_frase(tokens), frase) for frase, tokens in frases_tokenizadas],
    reverse=True
)

print("\n--- Top 3 frases mais representativas ---")
for i, (s, frase) in enumerate(frases_scored[:3], 1):
    print(f"\n{i}. (score={s:.4f})\n   {frase}")