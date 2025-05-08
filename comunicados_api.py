import re
import json
import requests
from fastapi import FastAPI, Query, HTTPException
from bs4 import BeautifulSoup
from utils import get_hidden_fields
from typing import List, Optional

app = FastAPI(
    title="CBX Comunicados API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

BASE_URL = 'https://www.cbx.org.br'
COMUNICADOS_URL = f'{BASE_URL}/comunicados'


def scrape_comunicados(max_pages: Optional[int] = None) -> List[dict]:
    session = requests.Session()
    resp = session.get(COMUNICADOS_URL)
    if resp.status_code != 200:
        raise HTTPException(status_code=resp.status_code, detail="Erro ao acessar página de comunicados")
    soup = BeautifulSoup(resp.text, 'html.parser')
    hidden = get_hidden_fields(soup)

    # função interna para extrair páginas
    def extract_pages(soup):
        pages = set()
        for a in soup.find_all("a", href=True):
            m = re.search(r"Page\$(\d+)", a["href"])
            if m:
                pages.add(int(m.group(1)))
        return pages

    # descobrir páginas iniciais
    pages_to_visit = [1]
    visited = set()
    comunicados = []

    # limitar total de páginas
    first_pages = extract_pages(soup) | {1}
    if max_pages:
        # considera apenas até max_pages
        pages_to_visit = [p for p in sorted(first_pages) if p <= max_pages]
    else:
        pages_to_visit = sorted(first_pages)

    while pages_to_visit:
        page = pages_to_visit.pop(0)
        if page in visited:
            continue
        visited.add(page)

        # postback para outras páginas
        if page > 1:
            post_data = {
                **hidden,
                "__EVENTTARGET": "ctl00$ContentPlaceHolder1$gdvMain",
                "__EVENTARGUMENT": f"Page${page}",
            }
            resp = session.post(COMUNICADOS_URL, data=post_data)
            if resp.status_code != 200:
                raise HTTPException(status_code=resp.status_code, detail=f"Erro na página {page}")
            soup = BeautifulSoup(resp.text, 'html.parser')
            hidden = get_hidden_fields(soup)

        # coleta comunicados da página
        for a in soup.find_all("a", id=re.compile(r"ContentPlaceHolder1_gdvMain_hlkTitulo_\d+")):
            titulo = a.get_text(strip=True)
            link = BASE_URL + a["href"].strip()
            date_tag = a.find_next_sibling("span", class_="date")
            data_text = date_tag.get_text(strip=True) if date_tag else ""
            comunicados.append({
                "titulo": titulo,
                "data": data_text,
                "link": link
            })

        # agenda próximas páginas
        if not max_pages:
            novas = extract_pages(soup)
            for p in sorted(novas):
                if p not in visited and p not in pages_to_visit:
                    pages_to_visit.append(p)

    return comunicados


@app.get("/comunicados", response_model=List[dict])
def get_comunicados(paginas: Optional[int] = Query(None, ge=1, description="Número máximo de páginas a raspar")):
    """
    Retorna lista de comunicados da CBX.
    Parâmetro opcional 'paginas' limita quantas páginas serão raspadas.
    """
    return scrape_comunicados(max_pages=paginas)
