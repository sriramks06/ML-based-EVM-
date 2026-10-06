from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.api import routes_projects, routes_evm, routes_prediction, routes_risk, routes_recommendations, routes_analyze

app = FastAPI(
    title="ML-Enhanced EVM API",
    description="API for Machine Learning enhanced Earned Value Management forecasting and risk analysis.",
    version="1.0.0"
)

# CORS configuration for future React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, restrict this to frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health", tags=["Health"])
def health_check():
    return {"status": "healthy"}

# Include Routers
app.include_router(routes_projects.router)
app.include_router(routes_evm.router)
app.include_router(routes_prediction.router)
app.include_router(routes_risk.router)
app.include_router(routes_recommendations.router)
app.include_router(routes_analyze.router)
