import requests
from bs4 import BeautifulSoup
i = 0
url = 'https://www.cbx.org.br'
url_torneios = 'https://www.cbx.org.br/torneios'

def safe_find(parent, tag, **attrs):
    elem = parent.find(tag, attrs=attrs)
    return elem.get_text(strip=True) if elem else "None"

def safe_link(parent, tag, attr_name, **attrs):
    elem = parent.find(tag, attrs=attrs)
    return elem.get(attr_name, "").strip() if elem else "/None"

def safe_line(parent, tag, **attrs):
    elem = parent.find(tag,attrs=attrs)
    if not elem:
        return "None"
    for br in elem.find_all('br'):
        br.replace_with('\n')
    text = elem.get_text()
    return text.strip()

pagina = requests.get(url_torneios)
dados_pagina = BeautifulSoup(pagina.text, 'html.parser')

todos_torneios = dados_pagina.find_all('table', class_='torneios')

for table in todos_torneios:
    nome_torneio = safe_find(table,'span')
    id_torneio = safe_find(table,'span', id=f'ContentPlaceHolder1_gdvMain_lblIDTorneio_{i}').partition(':')[-1].strip()
    ritmo_torneio = safe_find(table,'span', id=f'ContentPlaceHolder1_gdvMain_lblRitmo_{i}').partition(':')[-1].strip()
    rating_torneio = safe_find(table, 'span', id=f'ContentPlaceHolder1_gdvMain_lblRating_{i}').partition(':')[-1].strip()
    organizador_torneio = safe_find(table, 'span', id=f'ContentPlaceHolder1_gdvMain_lblOrganizador_{i}').partition(':')[-1].strip()
    local_torneio = safe_find(table,'span',id=f'ContentPlaceHolder1_gdvMain_lblLocal_{i}').partition(':')[-1].strip()
    periodo_torneio = safe_find(table,'span',id=f'ContentPlaceHolder1_gdvMain_lblPeriodo_{i}').partition(':')[-1].strip()
    observacao_torneio = safe_line(table,'span',id=f'ContentPlaceHolder1_gdvMain_lblObs_{i}')
    regulamento_torneio = url + safe_link(table,'a', 'href',id=f'ContentPlaceHolder1_gdvMain_hlkTorneio_{i}')
    i += 1
    print(observacao_torneio)
print('FIM!')  
