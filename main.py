# Importa cada roteador da API 
from fastapi import FastAPI
from tournaments_api import router as tournaments_router

# Informações básicas
app = FastAPI(
    title="Chess Tournaments API",
    version="1.0.1",
    docs_url="/docs",
    redoc_url="/redoc"
)

app.include_router(tournaments_router)
