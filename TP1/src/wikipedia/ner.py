import json
import spacy
from collections import Counter
from spacy import displacy

nlp = spacy.load("pt_core_news_sm")

with open("wikipedia_musica.json", encoding="utf-8") as f:
    artigo = json.load(f)

texto_completo = ""
for seccao in artigo:
    for paragrafo in artigo[seccao]:
        texto_completo += paragrafo + "\n"

print(f"Texto total: {len(texto_completo)} caracteres")

doc = nlp(texto_completo)

def is_valida(ent):
    texto = ent.text.strip()
    if len(texto) <= 2:
        return False
    if len(texto.split()) > 5:
        return False
    ruido = {'veja', 'ver', 'exemplo', 'nota', 'tipo', 'forma',
             'consulte', 'indica', 'usado', 'criar'}
    if texto.lower().split()[0] in ruido:
        return False
    return True

orgs = set()
per  = set()
loc  = set()
misc = set()

for ent in doc.ents:
    if not is_valida(ent):
        continue
    if ent.label_ == "ORG":
        orgs.add(ent.text)
    elif ent.label_ == "PER":
        per.add(ent.text)
    elif ent.label_ == "LOC":
        loc.add(ent.text)
    else:
        misc.add(ent.text)

print(f"\nOrganizações : {orgs}")
print(f"Pessoas      : {per}")
print(f"Locais       : {loc}")
print(f"Outros (MISC): {misc}")

print("\n--- Top 10 entidades mais frequentes ---")
freq = Counter(ent.text for ent in doc.ents if is_valida(ent))
for ent, c in freq.most_common(10):
    print(f"  {ent!r:40} → {c}×")

# displacy.serve(doc, style="ent", port=5002)