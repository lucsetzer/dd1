import os

from fastapi import FastAPI
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from routes.settings import router as settings_router

# Create FastAPI app FIRST
app = FastAPI(title="DocuDecipher")

# THEN import routers
from routes.dashboard import router as dashboard_router
from routes.auth import router as auth_router
from routes.docudecipher import router as docudecipher_router

# Include routers
app.include_router(dashboard_router)
app.include_router(auth_router)
app.include_router(docudecipher_router)
app.include_router(settings_router)

# Setup templates
templates = Jinja2Templates(directory="templates")

# Mount static files (if you have them)
if os.path.exists("static"):
    app.mount("/static", StaticFiles(directory="static"), name="static")

# Import routes (we'll create these next)
# from routes import auth, dashboard

# Include routers (uncomment when ready)
# app.include_router(auth.router)
# app.include_router(dashboard.router)

# Basic test route
@app.get("/")
async def root():
    return {"message": "DocuDecipher - Clean structure"}

# You'll add more route imports as you move them