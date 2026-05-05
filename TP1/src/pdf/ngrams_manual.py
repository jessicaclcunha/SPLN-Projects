import json
import re
from collections import Counter
from math import log

with open("manual_teoria_musical.json", encoding="utf-8") as f:
    artigo = json.load(f)

frases = []
for seccao in artigo:
    for paragrafo in artigo[seccao]:
        for frase in re.split(r'(?<=[.!?])\s+', paragrafo):
            if frase.strip():
                frases.append(frase.strip())

print(f"Total de frases: {len(frases)}")

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

def build_ngrams(tokens, n):
    return Counter(tuple(tokens[i:i+n]) for i in range(len(tokens) - n + 1))

uni = build_ngrams(corpus, 1)
bi  = build_ngrams(corpus, 2)

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

print("\n--- Top 3 frases mais representativas ---")
for i, (s, frase) in enumerate(frases_scored[:3], 1):
    print(f"\n{i}. (score={s:.4f})\n   {frase}")

# Guardar top3
top3 = [frase for _, frase in frases_scored[:3]]
with open("manual_ngrams.json", "w", encoding="utf-8") as f:
    json.dump({"top3": top3}, f, indent=4, ensure_ascii=False)

print("\nGuardado em manual_ngrams.json")