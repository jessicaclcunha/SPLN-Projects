import requests
from bs4 import BeautifulSoup
import re
import json

url = "https://pt.wikipedia.org/wiki/M%C3%BAsica"
html_doc = requests.get(url, headers={
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/120.0.0.0 Safari/537.36"
})
html_doc.raise_for_status()
soup = BeautifulSoup(html_doc.text, 'html.parser')

conteudo = (
    soup.find('div', class_='mw-parser-output') or
    soup.find('div', id='mw-content-text')
)
if conteudo is None:
    raise RuntimeError(
        "Não foi possível encontrar o conteúdo da página.\n"
        f"Título da página recebida: {soup.title.string if soup.title else 'desconhecido'}\n"
        "Possível bloqueio ou CAPTCHA da Wikipedia. Tenta correr o script mais tarde."
    )

def limpar_texto(texto):
    texto = re.sub(r'\[\d+\]', '', texto)        # refs numéricas [1]
    texto = re.sub(r'\[[a-z]\]', '', texto)      # refs letra [a]
    texto = re.sub(r'\[editar[^\]]*\]', '', texto)  # "[editar | editar código]"
    texto = re.sub(r'\s+', ' ', texto)
    return texto.strip()

ignorar = {
    'Ver também', 'Referências', 'Ligações externas', 'Notas',
    'Bibliografia', 'Leitura adicional', 'Galeria',
    'Notas e referências', 'Referências bibliográficas'
}

artigo = {}
seccao_atual = 'Introdução'
artigo[seccao_atual] = []

for elem in conteudo.find_all(['h2', 'h3', 'p']):
    if elem.name in ('h2', 'h3'):
        nome = limpar_texto(elem.get_text())
        if nome and nome not in ignorar:
            seccao_atual = nome
            artigo.setdefault(seccao_atual, [])
        else:
            seccao_atual = '__ignorar__'

    elif elem.name == 'p':
        if seccao_atual == '__ignorar__':
            continue
        texto = limpar_texto(elem.get_text())
        if len(texto) > 30 and seccao_atual in artigo:
            artigo[seccao_atual].append(texto)

artigo = {k: v for k, v in artigo.items() if v}

with open("wikipedia_musica.json", "w", encoding="utf-8") as f:
    json.dump(artigo, f, indent=4, ensure_ascii=False)

print(f"Secções extraídas: {len(artigo)}")
for seccao, paragrafos in artigo.items():
    print(f"  {seccao}: {len(paragrafos)} parágrafos")