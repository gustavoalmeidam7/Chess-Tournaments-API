from bs4 import BeautifulSoup

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

#Por Emerson Machado 04/05/2025

# utils.py
from bs4 import BeautifulSoup

def get_hidden_fields(soup):
    return {
        "__VIEWSTATE":          soup.find("input", {"name": "__VIEWSTATE"})["value"],
        "__VIEWSTATEGENERATOR": soup.find("input", {"name": "__VIEWSTATEGENERATOR"})["value"],
        "__EVENTVALIDATION":    soup.find("input", {"name": "__EVENTVALIDATION"})["value"],
    }