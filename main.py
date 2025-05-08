# Importa cada roteador da API 
from fastapi import FastAPI
from noticias_api import router as noticias_router
from comunicados_api import router as comunicados_router
from jogadores_api import router as jogadores_router
from torneios_api import router as torneios_router

# Informações básicas
app = FastAPI(
    title="CBX API - Confederação Brasileira de Xadrez",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Inclui cada sub-API
app.include_router(noticias_router)
app.include_router(comunicados_router)
app.include_router(jogadores_router)
app.include_router(torneios_router)
