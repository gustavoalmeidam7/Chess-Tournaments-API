import requests
from bs4 import BeautifulSoup
import json
import time
inicio = time.time()


BASE_URL       = 'https://www.cbx.org.br'
TORNEIOS_URL   = f'{BASE_URL}/torneios'

def get_hidden_fields(soup):
    """Retorna os campos ASP.NET necessários para postback."""
    return {
        "__VIEWSTATE":          soup.find("input", {"name": "__VIEWSTATE"})["value"],
        "__VIEWSTATEGENERATOR": soup.find("input", {"name": "__VIEWSTATEGENERATOR"})["value"],
        "__EVENTVALIDATION":    soup.find("input", {"name": "__EVENTVALIDATION"})["value"],
    }

def safe_find(parent, tag, **attrs):
    elem = parent.find(tag, attrs=attrs)
    return elem.get_text(strip=True) if elem else ""

def safe_link(parent, tag, attr_name, **attrs):
    elem = parent.find(tag, attrs=attrs)
    return elem.get(attr_name, "").strip() if elem else ""

def safe_line(parent, tag, **attrs):
    elem = parent.find(tag, attrs=attrs)
    if not elem:
        return ""
    for br in elem.find_all('br'):
        br.replace_with('\n')
    return elem.get_text().strip()

def after_colon(text):
    return text.partition(':')[-1].strip()

# Inicia sessão (para manter cookies e estado)
session = requests.Session()

# 1) Faz GET inicial
resp = session.get(TORNEIOS_URL)
soup = BeautifulSoup(resp.text, 'html.parser')

# 2) Extrai campos ocultos
hidden = get_hidden_fields(soup)

# 3) Descobre número total de páginas
pagination_links = soup.find_all("a", href=True)
page_numbers = [int(a.text) for a in pagination_links if a.text.isdigit()]
num_pages = max(page_numbers) if page_numbers else 1

print(f"Encontradas {num_pages} páginas de torneios.")

# 4) Lista para resultados
lista_torneios = []

# 5) Loop por cada página
for page in range(1, num_pages + 1):
    print(f"==== Página {page} ====")
    if page > 1:
        # Prepara dados do postback
        post_data = {
            **hidden,
            "__EVENTTARGET":   "ctl00$ContentPlaceHolder1$gdvMain",
            "__EVENTARGUMENT": f"Page${page}",
        }
        resp = session.post(TORNEIOS_URL, data=post_data)
        soup = BeautifulSoup(resp.text, 'html.parser')
        hidden = get_hidden_fields(soup)

    # Extrai as tabelas de torneio
    tabelas = soup.find_all('table', class_='torneios')
    for i, table in enumerate(tabelas):
        torneio = {
            "nome":         safe_find(table, 'span', id=f'ContentPlaceHolder1_gdvMain_lblNomeTorneio_{i}'),
            "ID":           after_colon(safe_find(table, 'span', id=f'ContentPlaceHolder1_gdvMain_lblIDTorneio_{i}')),
            "ritmo":        after_colon(safe_find(table, 'span', id=f'ContentPlaceHolder1_gdvMain_lblRitmo_{i}')),
            "rating":       after_colon(safe_find(table, 'span', id=f'ContentPlaceHolder1_gdvMain_lblRating_{i}')),
            "organizador":  after_colon(safe_find(table, 'span', id=f'ContentPlaceHolder1_gdvMain_lblOrganizador_{i}')),
            "local":        after_colon(safe_find(table, 'span', id=f'ContentPlaceHolder1_gdvMain_lblLocal_{i}')),
            "periodo":      after_colon(safe_find(table, 'span', id=f'ContentPlaceHolder1_gdvMain_lblPeriodo_{i}')),
            "observacao":   after_colon(safe_line(table, 'span', id=f'ContentPlaceHolder1_gdvMain_lblObs_{i}')),
            "regulamento":  BASE_URL + safe_link(table, 'a', 'href', id=f'ContentPlaceHolder1_gdvMain_hlkTorneio_{i}'),
        }
        lista_torneios.append(torneio)

# 6) Salvar em JSON
with open("torneios.json", "w", encoding="utf-8") as f:
    json.dump(lista_torneios, f, ensure_ascii=False, indent=4)

print(f"Total de torneios coletados: {len(lista_torneios)}")
fim = time.time()

performance = fim - inicio
print(f'Performance de {performance:.2f} segundos')
