import re
import requests
from bs4 import BeautifulSoup
import json
from utils import get_hidden_fields
import time
inicio = time.time()


BASE_URL      = 'https://www.cbx.org.br'
COMUNICADOS_URL = f'{BASE_URL}/comunicados'

session = requests.Session()

# Função para extrair todos os números de página atualmente visíveis no pager
def extract_pages(soup):
    pages = set()
    for a in soup.find_all("a", href=True):
        m = re.search(r"Page\$(\d+)", a["href"])
        if m:
            pages.add(int(m.group(1)))
    return pages

# Começamos sabendo apenas da página 1
to_visit = [1]
visited = set()
lista = []

# Pega os campos ocultos só uma vez (será atualizado dentro do loop)
resp = session.get(COMUNICADOS_URL)
soup = BeautifulSoup(resp.text, "html.parser")
hidden = get_hidden_fields(soup)

while to_visit:
    page = to_visit.pop(0)
    if page in visited:
        continue
    visited.add(page)

    print(f"==== Página {page} ====")

    # Se não for a primeira página, dispara o postback
    if page > 1:
        post = {
            **hidden,
            "__EVENTTARGET":   "ctl00$ContentPlaceHolder1$gdvMain",
            "__EVENTARGUMENT": f"Page${page}",
        }
        resp = session.post(COMUNICADOS_URL, data=post)
        soup = BeautifulSoup(resp.text, "html.parser")
        hidden = get_hidden_fields(soup)

    # Extrai as comunicações desta página
    for a in soup.find_all("a", id=re.compile(r"ContentPlaceHolder1_gdvMain_hlkTitulo_\d+")):
        titulo = a.get_text(strip=True)
        link   = BASE_URL + a["href"].strip()
        date_tag = a.find_next_sibling("span", class_="date")
        data     = date_tag.get_text(strip=True) if date_tag else ""
        lista.append({"titulo": titulo, "data": data, "link": link})

    # Descobre novas páginas e adiciona à fila
    novas = extract_pages(soup)
    for p in sorted(novas):
        if p not in visited and p not in to_visit:
            to_visit.append(p)

print(f"Total de comunicados: {len(lista)}")
# Salva em JSON
with open("comunicados.json", "w", encoding="utf-8") as f:
    json.dump(lista, f, ensure_ascii=False, indent=4)
fim = time.time()
print(f'Performance de {fim-inicio:.2f} segundos')