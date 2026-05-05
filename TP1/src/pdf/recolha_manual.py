import re
import json

with open("manual_teoria_musical.txt", encoding="utf-8") as f:
    texto = f.read()

# Limpar cabeçalhos, números de página e linhas de índice
def limpar_linha(linha):
    s = linha.strip()
    if not s:
        return None
    if s in ("LXPRO", "Manual de Teoria Musical", "LXPRO Manual de Teoria Musical"):
        return None
    if re.match(r"^\d{1,2}$", s):
        return None
    if re.match(r"^~\s*\d+\s*~$", s):
        return None
    return s

# Agrupar linhas em parágrafos (linha vazia = fim de parágrafo)
paragrafos = []
paragrafo_atual = []

for linha in texto.split("\n"):
    limpa = limpar_linha(linha)
    if limpa:
        paragrafo_atual.append(limpa)
    else:
        if paragrafo_atual:
            texto_paragrafo = " ".join(paragrafo_atual)
            # Ignorar parágrafos sem ponto final (restos do índice)
            if len(texto_paragrafo) > 30 and "." in texto_paragrafo:
                paragrafos.append(texto_paragrafo)
            paragrafo_atual = []

if paragrafo_atual:
    texto_paragrafo = " ".join(paragrafo_atual)
    if len(texto_paragrafo) > 30 and "." in texto_paragrafo:
        paragrafos.append(texto_paragrafo)

artigo = {"Manual de Teoria Musical": paragrafos}

with open("manual_teoria_musical.json", "w", encoding="utf-8") as f:
    json.dump(artigo, f, indent=4, ensure_ascii=False)

print(f"Parágrafos extraídos: {len(paragrafos)}")