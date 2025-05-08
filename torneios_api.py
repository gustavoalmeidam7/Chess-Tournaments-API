import re
import requests
from bs4 import BeautifulSoup
from fastapi import APIRouter, Query, HTTPException
from datetime import datetime
from typing import Optional, List
from utils import get_hidden_fields, safe_find, safe_link, safe_line, after_colon

router = APIRouter(prefix="/torneios", tags=["torneios"])

BASE_URL = "https://www.cbx.org.br"
TORNEIOS_URL = f"{BASE_URL}/torneios"

def extract_pages(soup):
    pages = set()
    for a in soup.find_all("a", href=True):
        m = re.search(r"Page\$(\d+)", a["href"])
        if m:
            pages.add(int(m.group(1)))
    return pages

def scrape_torneios(
    ano: Optional[str],
    mes: Optional[str],
    max_pages: Optional[int]
) -> List[dict]:
    session = requests.Session()

    # Padrão para ano e mês atual se não fornecidos
    now = datetime.now()
    ano = ano or str(now.year)
    mes = mes or ""

    # 1) GET inicial
    resp = session.get(TORNEIOS_URL)
    if resp.status_code != 200:
        raise HTTPException(status_code=resp.status_code, detail="Erro ao acessar a página de torneios.")
    soup = BeautifulSoup(resp.text, "html.parser")
    hidden = get_hidden_fields(soup)

    # 2) POST para aplicar o filtro de ano/mês
    post_data = {
        **hidden,
        "ctl00$ContentPlaceHolder1$cboAno": ano,
        "ctl00$ContentPlaceHolder1$cboMes": mes,
        "ctl00$ContentPlaceHolder1$btnBuscar": "Buscar"
    }
    resp = session.post(TORNEIOS_URL, data=post_data)
    if resp.status_code != 200:
        raise HTTPException(status_code=resp.status_code, detail="Erro ao aplicar filtro.")
    soup = BeautifulSoup(resp.text, "html.parser")
    hidden = get_hidden_fields(soup)

    to_visit = sorted(extract_pages(soup) | {1})
    if max_pages:
        to_visit = [p for p in to_visit if p <= max_pages]

    visited = set()
    lista_torneios = []

    while to_visit:
        page = to_visit.pop(0)
        if page in visited:
            continue
        visited.add(page)

        if page > 1:
            post = {
                **hidden,
                "__EVENTTARGET":   "ctl00$ContentPlaceHolder1$gdvMain",
                "__EVENTARGUMENT": f"Page${page}",
            }
            resp = session.post(TORNEIOS_URL, data=post)
            if resp.status_code != 200:
                continue
            soup = BeautifulSoup(resp.text, "html.parser")
            hidden = get_hidden_fields(soup)

        # agenda novas páginas encontradas
        if not max_pages:
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

    return lista_torneios


@router.get("", response_model=List[dict])
def get_torneios(
    ano: Optional[str] = Query(None, min_length=4, max_length=4, description="Ano desejado, ex: 2025"),
    mes: Optional[str] = Query(None, min_length=1, max_length=2, description="Número do mês (1–12), ex: 5 para Maio"),
    paginas: Optional[int] = Query(None, ge=1, description="Número máximo de páginas a raspar")
):
    """
    Retorna lista de torneios da CBX filtrados por ano e mês.
    """
    return scrape_torneios(ano, mes, paginas)
