import requests
from bs4 import BeautifulSoup
import re
import json

url = "https://handbook.musescore.org/pt_br/appendix/glossary"
html_doc = requests.get(url)
soup = BeautifulSoup(html_doc.text, 'html.parser')


def limpar_texto(texto):
    texto = re.sub(r'arrow-up-right', '', texto)
    texto = re.sub(r'\\+', '', texto)
    texto = re.sub(r'\s+', ' ', texto)
    return texto.strip()

def limpar_nome(nome):
    nome = re.sub(r'\(.*?(AE|BE).*?\)', '', nome)  # remove qualquer parêntese com AE ou BE
    nome = re.sub(r'\*', '', nome)
    return nome.strip()

glossario = {}

for h3 in soup.find_all('h3'):
    letra = limpar_texto(h3.get_text()).replace('hashtag', '').strip()

    if letra == 'External links' or not letra:
        continue

    glossario[letra] = {}

    ul = h3.find_next_sibling('ul')
    if not ul:
        continue

    for li in ul.find_all('li', recursive=False):
        paragrafos = li.find_all('p')
        if not paragrafos:
            continue

        nome_raw = limpar_texto(paragrafos[0].get_text())
        if not nome_raw:
            continue

        variante = None
        if 'AE' in nome_raw:
            variante = 'AE'
        elif 'BE' in nome_raw:
            variante = 'BE'

        musescore_especifico = '*' in nome_raw
        nome = limpar_nome(nome_raw)

        definicao = ''
        if len(paragrafos) > 1:
            definicao = limpar_texto(paragrafos[1].get_text())

        glossario[letra][nome] = {
            'definicao': definicao,
            'variante': variante,
            'musescore_especifico': musescore_especifico
        }

glossario = {k: v for k, v in glossario.items() if v}

with open("musescore_glossario.json", "w", encoding="utf-8") as f:
    json.dump(glossario, f, indent=4, ensure_ascii=False)

print(json.dumps(dict(list(glossario.items())[:2]), indent=4, ensure_ascii=False))