import requests
from bs4 import BeautifulSoup
import json
from utils import get_hidden_fields, safe_find, after_colon

BASE_URL = "https://www.cbx.org.br"
URL = f"{BASE_URL}/rating"
session = requests.Session()

# GET inicial e postback de SP (igual antes)...
resp = session.get(URL)
soup = BeautifulSoup(resp.text, "html.parser")
hidden = get_hidden_fields(soup)

post_data = {
    **hidden,
    "ctl00$ContentPlaceHolder1$cboUF": "SP",
    "__EVENTTARGET":   "ctl00$ContentPlaceHolder1$cboUF",
    "__EVENTARGUMENT": "",
    "ctl00$ContentPlaceHolder1$btnBuscar": "Buscar"
}
resp2 = session.post(URL, data=post_data)
soup2 = BeautifulSoup(resp2.text, "html.parser")

# Localiza a tabela
table = soup2.find("table", class_="grid")

# Captura o total
total = after_colon(safe_find(table, "caption"))

# Pega todas as linhas
all_rows = table.find_all("tr")

# 1) Cabeçalho: a primeira linha
header_cells = all_rows[0].find_all("th")
colunas = [th.get_text(strip=True) for th in header_cells]

# 2) Corpo: todas as outras linhas
dados = []
for row in all_rows[1:]:
    # Some tables podem ter <th> também em linhas de agrupamento; aqui assumimos <td>
    cells = row.find_all("td")
    if not cells:
        continue  # pula linhas sem <td>
    valores = [td.get_text(strip=True) for td in cells]
    registro = dict(zip(colunas, valores))
    cbx_id = registro.get("ID CBX", "").strip()
    registro["link"] = f"{BASE_URL}/jogador/{cbx_id}" if cbx_id else ""

    dados.append(registro)

# Monta o JSON final
resultado = {
    "total_jogadores": total,
    "jogadores": dados
}

# Salva
with open("jogadores_sp.json", "w", encoding="utf-8") as f:
    json.dump(resultado, f, ensure_ascii=False, indent=4)
