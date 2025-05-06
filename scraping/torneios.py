import re
import json
import time
import requests
from bs4 import BeautifulSoup
from utils import get_hidden_fields, safe_find, safe_link, safe_line, after_colon

inicio = time.time()

BASE_URL      = "https://www.cbx.org.br"
TORNEIOS_URL  = f"{BASE_URL}/torneios"

# --- CONFIGURAÇÃO DE FILTRO ---
ANO = "2010"
# Cada mês tem seu número respectivo ao calendário, para selecionar 'Todos' deixe vazio ""
MES = ""

session = requests.Session()

def extract_pages(soup):
    pages = set()
    for a in soup.find_all("a", href=True):
        m = re.search(r"Page\$(\d+)", a["href"])
        if m:
            pages.add(int(m.group(1)))
    return pages

# 1) GET inicial para capturar __VIEWSTATE, etc.
resp = session.get(TORNEIOS_URL)
soup = BeautifulSoup(resp.text, "html.parser")
hidden = get_hidden_fields(soup)

# 2) POST inicial aplicando o filtro de Ano e Mês
post_data = {
    **hidden,
    # nome exato dos selects no formulário ASP.NET:
    "ctl00$ContentPlaceHolder1$cboAno": ANO,
    "ctl00$ContentPlaceHolder1$cboMes": MES,
    # dispara o postback no botão de busca (inspecione o name/id do botão)
    "ctl00$ContentPlaceHolder1$btnBuscar": "Buscar"
}
resp = session.post(TORNEIOS_URL, data=post_data)
soup = BeautifulSoup(resp.text, "html.parser")
hidden = get_hidden_fields(soup)

# 3) Descobre todas as páginas a visitar (inclui a página 1)
to_visit = sorted(extract_pages(soup) | {1})
visited  = set()

lista_torneios = []

# 4) Loop completo de paginação
while to_visit:
    page = to_visit.pop(0)
    if page in visited:
        continue
    visited.add(page)

    print(f"Página {page} de Ano={ANO}, Mês={MES}")

    if page > 1:
        post = {
            **hidden,
            "__EVENTTARGET":   "ctl00$ContentPlaceHolder1$gdvMain",
            "__EVENTARGUMENT": f"Page${page}",
        }
        resp = session.post(TORNEIOS_URL, data=post)
        soup = BeautifulSoup(resp.text, "html.parser")
        hidden = get_hidden_fields(soup)

    # agenda novas páginas encontradas neste pager
    for p in extract_pages(soup):
        if p not in visited and p not in to_visit:
            to_visit.append(p)

    # extrai torneios da página atual
    for i, table in enumerate(soup.find_all("table", class_="torneios")):
        t = {
            "pagina":          page,
            "nome":            safe_find(table, 'span', id=f'ContentPlaceHolder1_gdvMain_lblNomeTorneio_{i}'),
            "ID":              after_colon(safe_find(table, 'span', id=f'ContentPlaceHolder1_gdvMain_lblIDTorneio_{i}')),
            "situacao":        after_colon(safe_find(table, 'span', id=f'ContentPlaceHolder1_gdvMain_lblStatus_{i}')),
            "ritmo":           after_colon(safe_find(table, 'span', id=f'ContentPlaceHolder1_gdvMain_lblRitmo_{i}')),
            "rating":          after_colon(safe_find(table, 'span', id=f'ContentPlaceHolder1_gdvMain_lblRating_{i}')),
            "qt_jogadores":    after_colon(safe_find(table, 'span', id=f'ContentPlaceHolder1_gdvMain_lblQtJogadores_{i}')),
            "organizador":     after_colon(safe_find(table, 'span', id=f'ContentPlaceHolder1_gdvMain_lblOrganizador_{i}')),
            "local":           after_colon(safe_find(table, 'span', id=f'ContentPlaceHolder1_gdvMain_lblLocal_{i}')),
            "jogadores_fide":  after_colon(safe_find(table, 'span', id=f'ContentPlaceHolder1_gdvMain_lblQtJogadoresFIDE_{i}')),
            "periodo":         after_colon(safe_find(table, 'span', id=f'ContentPlaceHolder1_gdvMain_lblPeriodo_{i}')),
            "observacao":      after_colon(safe_line(table, 'span', id=f'ContentPlaceHolder1_gdvMain_lblObs_{i}')),
            "regulamento":     BASE_URL + safe_link(table, 'a', 'href', id=f'ContentPlaceHolder1_gdvMain_hlkTorneio_{i}')
        }
        lista_torneios.append(t)

resultado = {
    "ano":              ANO,
    "mês":              MES,    
    "total_paginas":    len(visited),
    "total_torneios":   len(lista_torneios),
    "torneios":         lista_torneios
}

# 5) Grava JSON final
with open(f"torneios_{ANO}_{MES}.json", "w", encoding="utf-8") as f:
    json.dump(resultado, f, ensure_ascii=False, indent=4)

print(f"✔️  Coletados {len(lista_torneios)} torneios em {len(visited)} páginas para Ano={ANO}, Mês={MES}")
print(f"⏱️  Tempo total: {time.time()-inicio:.2f}s")
