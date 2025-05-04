import time
import re
import requests
from bs4 import BeautifulSoup
import json
from utils import get_hidden_fields

inicio = time.time()

BASE_URL     = 'https://www.cbx.org.br'
NOTICIAS_URL = f'{BASE_URL}/noticias'

session = requests.Session()
resp = session.get(NOTICIAS_URL)
soup = BeautifulSoup(resp.text, 'html.parser')
hidden = get_hidden_fields(soup)

# Descobre quantas páginas há
page_numbers = [int(a.text) for a in soup.find_all("a", href=True) if a.text.isdigit()]
num_pages = max(page_numbers) if page_numbers else 1
print(f"Encontradas {num_pages} páginas de notícias.")

lista_noticias = []

for page in range(1, num_pages + 1):
    print(f"==== Página {page} ====")
    if page > 1:
        post_data = {
            **hidden,
            "__EVENTTARGET":   "ctl00$ContentPlaceHolder1$gdvMain",
            "__EVENTARGUMENT": f"Page${page}",
        }
        resp = session.post(NOTICIAS_URL, data=post_data)
        soup = BeautifulSoup(resp.text, 'html.parser')
        hidden = get_hidden_fields(soup)

    # Para esta página, pegue todos os links de notícia
    links_noticia = soup.find_all(
        "a",
        id=re.compile(r"ContentPlaceHolder1_gdvMain_hlkTitulo_\d+")
    )

    noticias_pagina = []
    for a in links_noticia:
        titulo = a.get_text(strip=True)
        link   = BASE_URL + a["href"].strip()
        date_tag = a.find_next_sibling("span", class_="date")
        data     = date_tag.get_text(strip=True) if date_tag else ""
        noticias_pagina.append({
            "titulo": titulo,
            "data":   data,
            "link":   link
        })
    lista_noticias.extend(noticias_pagina)

# Ao final do loop, salva e imprime tudo
with open("noticias.json", "w", encoding="utf-8") as f:
    json.dump(lista_noticias, f, ensure_ascii=False, indent=4)

print(f"Total de notícias coletadas: {len(lista_noticias)}")

fim = time.time()
print(f'Performance de {fim - inicio:.2f} segundos')
