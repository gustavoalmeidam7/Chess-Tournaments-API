import re
import json
import requests
from bs4 import BeautifulSoup
from utils import get_hidden_fields
import time

inicio = time.time()

BASE_URL = "https://www.cbx.org.br"
URL      = f"{BASE_URL}/rating"
UF       = "RR"  # alterar para qualquer outro estado

session = requests.Session()

def extract_pages(soup):
    """
    Extrai de todos os links __doPostBack('...','Page$X') os números X.
    Retorna um set de inteiros.
    """
    pages = set()
    for a in soup.find_all("a", href=True):
        m = re.search(r"Page\$(\d+)", a["href"])
        if m:
            pages.add(int(m.group(1)))
    return pages

# 1) GET inicial para página 1 + filtro de UF
resp = session.get(URL)
soup = BeautifulSoup(resp.text, "html.parser")
hidden = get_hidden_fields(soup)

# monta dados do filtro de UF + primeiro postback
payload = {
    **hidden,
    "ctl00$ContentPlaceHolder1$cboUF": UF,
    "__EVENTTARGET":   "ctl00$ContentPlaceHolder1$cboUF",
    "__EVENTARGUMENT": "",
    "ctl00$ContentPlaceHolder1$btnBuscar": "Buscar"
}
resp = session.post(URL, data=payload)
soup = BeautifulSoup(resp.text, "html.parser")
hidden = get_hidden_fields(soup)

# descobre todas as páginas a visitar (inclui página 1)
to_visit = sorted(extract_pages(soup) | {1})
visited  = set()
all_players = []

while to_visit:
    page = to_visit.pop(0)
    if page in visited:
        continue
    visited.add(page)

    print(f"Scraping página {page} de UF = {UF}…")
    # faz o postback para cada página (GET apenas para 1 já feito)
    if page > 1:
        post = {
            **hidden,
            "__EVENTTARGET":   "ctl00$ContentPlaceHolder1$gdvMain",
            "__EVENTARGUMENT": f"Page${page}",
        }
        resp = session.post(URL, data=post)
        soup = BeautifulSoup(resp.text, "html.parser")
        hidden = get_hidden_fields(soup)

    # extrai tabela e linhas
    table = soup.find("table", class_="grid")
    if not table:
        continue

    # pega todas as tr diretas (sem descer nas aninhadas)
    rows = table.find_all("tr", recursive=False)

    # primeira linha é sempre cabeçalho
    headers = [th.get_text(strip=True) for th in rows[0].find_all("th")]

    # percorre linhas de dados
    for row in rows[1:]:
        # pula paginação
        if "grid-pager" in row.get("class", []):
            continue
        cells = row.find_all("td")
        if not cells:
            continue
        vals = [td.get_text(strip=True) for td in cells]
        rec = dict(zip(headers, vals))
        cbx_id = rec.get("ID CBX", "")
        rec["link"] = f"{BASE_URL}/jogador/{cbx_id}" if cbx_id else ""
        all_players.append(rec)

    # descobre novas páginas aparecendo no pager desta página
    new_pages = extract_pages(soup)
    for p in sorted(new_pages):
        if p not in visited and p not in to_visit:
            to_visit.append(p)

# grava resultado
resultado = {
    "UF":               UF,
    "total_paginas":    len(visited),
    "total_jogadores":  len(all_players),
    "jogadores":        all_players
}

with open(f"jogadores_{UF.lower()}.json", "w", encoding="utf-8") as f:
    json.dump(resultado, f, ensure_ascii=False, indent=4)

print(f"✔️  Coletados {len(all_players)} jogadores em {len(visited)} páginas.")  
print(f"⏱️  Tempo total: {time.time()-inicio:.2f} segundos")
