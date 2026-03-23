"""
run_all.py — Corre o pipeline completo do TP1
Estrutura esperada:
  run_all.py
  musescore/
      recolha_musescore.py   → musescore_glossario.json
      ngrams_musescore.py
      ner_musescore.py
      gerar_latex.py         → artigo_musescore.tex / .pdf
  wikipedia/
      recolha.py             → wikipedia_musica.json
      ngrams.py
      ner.py
      gerar_latex.py         → artigo.tex / .pdf
  pdf/
      recolha_manual.py      → manual_teoria_musical.json
      ngrams_manual.py
      ner_manual.py
      gerar_latex_manual.py  → artigo_manual.tex / .pdf
"""

import subprocess
import sys
import os

GREEN  = "\033[92m"
RED    = "\033[91m"
YELLOW = "\033[93m"
BOLD   = "\033[1m"
RESET  = "\033[0m"

def ok(msg):   print(f"  {GREEN}✓{RESET} {msg}")
def err(msg):  print(f"  {RED}✗{RESET} {msg}")
def info(msg): print(f"\n{BOLD}{YELLOW}▶ {msg}{RESET}")

ROOT = os.path.dirname(os.path.abspath(__file__))

def correr(pasta, script, descricao):
    cwd = os.path.join(ROOT, pasta)
    print(f"    → {pasta}/{script}", end=" ", flush=True)
    result = subprocess.run(
        [sys.executable, script],
        capture_output=True, text=True,
        cwd=cwd
    )
    if result.returncode == 0:
        ok(descricao)
    else:
        err(f"ERRO em {pasta}/{script}")
        print(result.stderr[-800:])
        sys.exit(1)

def compilar_latex(pasta, tex_file, pdf_file=None):
    if pdf_file is None:
        pdf_file = tex_file.replace(".tex", ".pdf")
    cwd = os.path.join(ROOT, pasta)
    print(f"    → pdflatex {pasta}/{tex_file}", end=" ", flush=True)
    for _ in range(2):
        result = subprocess.run(
            ["pdflatex", "-interaction=nonstopmode", tex_file],
            capture_output=True,
            cwd=cwd,
            encoding="utf-8",   # pdflatex no macOS usa latin-1
            errors="replace"      # caracteres inválidos substituídos por ?
        )
    if result.returncode == 0:
        ok(f"PDF gerado: {pasta}/{pdf_file}")
    else:
        err(f"ERRO ao compilar {pasta}/{tex_file}")
        for line in result.stdout.splitlines():
            if "Error" in line or "error" in line:
                print(f"      {line}")
        sys.exit(1)

def limpar_aux(pasta, base):
    cwd = os.path.join(ROOT, pasta)
    for ext in [".aux", ".log", ".out", ".toc"]:
        f = os.path.join(cwd, base + ext)
        if os.path.exists(f):
            os.remove(f)

# ════════════════════════════════════════════════════════════════════════════
print(f"\n{BOLD}{'═'*55}")
print("  TP1 — Pipeline completo  (SPLN 2025/26)")
print(f"{'═'*55}{RESET}")

info("FASE 1 — Recolha de texto")
correr("musescore", "recolha_musescore.py", "MuseScore Glossário   → musescore_glossario.json")
correr("wikipedia", "recolha.py",           "Wikipedia Música      → wikipedia_musica.json")
correr("pdf",       "recolha_manual.py",    "Manual Teoria Musical → manual_teoria_musical.json")

info("FASE 2 — Modelos de N-gramas")
correr("musescore", "ngrams_musescore.py", "N-gramas MuseScore")
correr("wikipedia", "ngrams.py",           "N-gramas Wikipedia Música")
correr("pdf",       "ngrams_manual.py",    "N-gramas Manual")

info("FASE 3 — NER com spaCy")
correr("musescore", "ner_musescore.py", "NER MuseScore")
correr("wikipedia", "ner.py",           "NER Wikipedia Música")
correr("pdf",       "ner_manual.py",    "NER Manual")

info("FASE 4 — Geração dos artigos LaTeX")
correr("musescore", "gerar_latex.py",        "LaTeX MuseScore        → artigo_musescore.tex")
correr("wikipedia", "gerar_latex.py",        "LaTeX Wikipedia Música → artigo.tex")
correr("pdf",       "gerar_latex_manual.py", "LaTeX Manual           → artigo_manual.tex")

info("FASE 5 — Compilação dos PDFs")
compilar_latex("musescore", "artigo_musescore.tex")
compilar_latex("wikipedia", "artigo_wikipedia_musica.tex")
compilar_latex("pdf",       "artigo_manual.tex")

info("Limpeza de ficheiros auxiliares")
limpar_aux("musescore", "artigo_musescore")
limpar_aux("wikipedia", "artigo_wikipedia_musica")
limpar_aux("pdf",       "artigo_manual")
ok("Ficheiros .aux/.log/.out removidos")

print(f"\n{BOLD}{'═'*55}")
print("  PDFs gerados:")
pdfs = [
    ("musescore", "artigo_musescore.pdf"),
    ("wikipedia", "artigo_wikipedia_musica.pdf"),
    ("pdf",       "artigo_manual.pdf"),
]
for pasta, pdf in pdfs:
    caminho = os.path.join(ROOT, pasta, pdf)
    existe = os.path.exists(caminho)
    simbolo = f"{GREEN}✓{RESET}" if existe else f"{RED}✗{RESET}"
    print(f"    {simbolo} {pasta}/{pdf}")
print(f"{'═'*55}{RESET}\n")