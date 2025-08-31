
import os
import warnings
from typing import Any, Optional

import joblib
from fastapi import FastAPI, HTTPException, Query, Request, Depends, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from pydantic import BaseModel
from fastapi.templating import Jinja2Templates

# ---- Config ----
APP_NAME = "Prediction App"
MODEL_PATH = os.getenv("MODEL_PATH", "model.pkl")
SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-change-me")

app = FastAPI(title=APP_NAME, version="1.0.0", description="UI + API FastAPI (login + prédiction)")

# Static & templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Sessions (simple cookie session for demo)
app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY)

# CORS ouvert (facilite tests; restreindre en prod)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Masquer l'avertissement xgboost sur les modèles sérialisés d'ancienne version (facultatif)
warnings.filterwarnings("ignore", message=".*serialized model.*", category=UserWarning, module="xgboost")

# ---- Modèle ----
_model: Optional[Any] = None

def _load_model(path: str = MODEL_PATH):
    global _model
    _model = joblib.load(path)

@app.on_event("startup")
def startup_event():
    if os.path.exists(MODEL_PATH):
        try:
            _load_model(MODEL_PATH)
        except Exception as e:
            print(f"⚠️ Impossible de charger le modèle au démarrage: {e}")

def _ensure_model_loaded():
    if _model is None:
        raise HTTPException(status_code=500, detail=f"Modèle non chargé. Placez le fichier '{MODEL_PATH}' ou définissez MODEL_PATH.")

# ---- Schémas ----
class PredictIn(BaseModel):
    date: str

class PredictOut(BaseModel):
    date: str
    prediction: float

# ---- Auth minimale (DEMO) ----
# Remplacez par une vraie base/utilisateur en prod
USERS = {"admin": "admin123"}

def get_current_user(request: Request) -> Optional[str]:
    return request.session.get("user")

def login_required(request: Request):
    user = get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Non authentifié.")
    return user

# ---- Routes UI ----
@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    # Redirige vers /app si loggé, sinon /login
    if get_current_user(request):
        return RedirectResponse(url="/app", status_code=302)
    return RedirectResponse(url="/login", status_code=302)

@app.get("/login", response_class=HTMLResponse)
def login_view(request: Request):
    return templates.TemplateResponse("login.html", {"request": request, "error": None})

@app.post("/login", response_class=HTMLResponse)
def login_submit(request: Request, username: str = Form(...), password: str = Form(...)):
    if USERS.get(username) == password:
        request.session["user"] = username
        return RedirectResponse(url="/app", status_code=302)
    return templates.TemplateResponse("login.html", {"request": request, "error": "Identifiants invalides."})

@app.get("/logout")
def logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/login", status_code=302)

@app.get("/app", response_class=HTMLResponse)
def app_view(request: Request, user: str = Depends(login_required)):
    # Page avec le champ date + fetch() vers POST /predict
    return templates.TemplateResponse("app.html", {"request": request, "user": user})

# ---- Endpoints API ----
@app.get("/health")
def health():
    return {"status": "ok", "model_loaded": _model is not None, "model_path": MODEL_PATH}

@app.post("/reload-model")
def reload_model():
    _load_model(MODEL_PATH)
    return {"status": "reloaded", "model_type": type(_model).__name__}

@app.post("/predict", response_model=PredictOut)
def predict(payload: PredictIn):
    _ensure_model_loaded()
    try:
        y = _model.predict(payload.date)  # ou _model.predict([payload.date]) selon votre objet
        if hasattr(y, "__iter__") and not isinstance(y, (str, bytes)):
            y = float(list(y)[0])
        else:
            y = float(y)
        return PredictOut(date=payload.date, prediction=y)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Erreur de prédiction: {e}")

# GET pratique pour tests (navigateur)
@app.get("/predict", response_model=PredictOut)
def predict_get(date: str = Query(..., description="Ex: 23-06-2021")):
    return predict(PredictIn(date=date))
