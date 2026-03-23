import json
import spacy
from collections import Counter

nlp = spacy.load("pt_core_news_sm")

with open("musescore_glossario.json", encoding="utf-8") as f:
    glossario = json.load(f)

texto_completo = ""
for letra in glossario:
    for termo in glossario[letra]:
        definicao = glossario[letra][termo]["definicao"]
        if definicao:
            texto_completo += definicao + "\n"

print(f"Texto total: {len(texto_completo)} caracteres")

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

print("\n--- Top entidades mais frequentes ---")
freq = Counter(ent.text for ent in doc.ents if is_valida(ent))
for ent, c in freq.most_common(10):
    print(f"  {ent!r:35} → {c}×")
    
# from spacy import displacy
# displacy.serve(doc, style="ent", port=5002)