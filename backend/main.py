from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from config import settings
from routers import auth, portfolio, trade, analyze

app = FastAPI(title="Robinhood AI Bridge", version="2.0.0")

# Validate config on startup
settings.validate_required()

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(portfolio.router, prefix="/api", tags=["Portfolio"])
app.include_router(trade.router, prefix="/api", tags=["Trade"])
app.include_router(analyze.router, prefix="/api", tags=["Analysis"])

@app.get("/")
def health_check():
    return {"status": "ok", "version": "2.0.0", "message": "Robinhood AI Bridge Backend Running"}
