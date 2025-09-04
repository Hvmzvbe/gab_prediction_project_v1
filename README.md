
# 📊 Prediction App — FastAPI

Application web (UI + API) permettant de **prédire un montant à partir d’une date donnée**, basée sur un modèle de machine learning (**XGBoost**). Déployable en **conteneur Docker**.

---

## 🚀 Fonctionnalités

- 🔐 Authentification (login/logout) avec session
- 🌐 Interface utilisateur moderne (HTML/CSS avec animations)
- 📅 Prédiction par date via un modèle ML (`model.pkl`)
- 🖥️ API REST (FastAPI + Pydantic)
- ⚡ Endpoints santé (`/health`) et rechargement du modèle (`/reload-model`)
- 🐳 Déploiement simple via Docker

---

## 📂 Structure du projet

```
.
├── main.py              # Application FastAPI principale (routes, sessions, templates)
├── date_predictor.py    # Classe utilitaire pour features + lags et prédictions par date
├── model.pkl            # Modèle ML sérialisé (doit exposer .predict(date))
├── requirements.txt     # Dépendances Python
├── templates/           # Gabarits Jinja2 pour l'UI
│   ├── login.html
│   └── app.html
└── static/
    └── styles.css       # Styles CSS
```

> 🔎 **Note** : `main.py` s’attend à trouver `templates/` et `static/` aux chemins ci‑dessus et charge `model.pkl` au démarrage.

---

## ⚙️ Installation & Lancement (sans Docker)

### 1) Cloner le dépôt
```bash
git clone https://github.com/Hvmzvbe/gab_pred.git
cd gab_pred
```

### 2) Créer un environnement virtuel
```bash
python -m venv .venv
# Linux/Mac
source .venv/bin/activate
# Windows
.venv\Scripts\activate
```

### 3) Installer les dépendances
```bash
pip install -r requirements.txt
```

### 4) Variables d’environnement (optionnel mais recommandé)
```bash
# chemin du modèle (par défaut: model.pkl)
export MODEL_PATH="model.pkl"
# clé de session (IMPORTANT en prod)
export SECRET_KEY="change-me-in-prod"
```

### 5) Lancer l’application
```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```
👉 Application disponible sur : http://localhost:8000

---

## 🐳 Déploiement avec Docker

### 1) Construire l’image
```bash
docker build -t hamzabe/gab-predict:v1 .
```

### 2) Lancer un conteneur
```bash
docker run -d --name gab-predict -p 8000:8000 hamzabe/gab-predict:v1
```
👉 Application disponible sur : http://localhost:8000

### 3) (Optionnel) Monter un modèle externe
```bash
# remplace le modèle de l'image par un fichier local
docker run -d --name gab-predict -p 8000:8000 \
  -e MODEL_PATH="/app/model.pkl" \
  -v "$PWD/model.pkl:/app/model.pkl" \
  hamzabe/gab-predict:v1
```

### 4) Pousser l’image sur Docker Hub
```bash
docker login
docker push hamzabe/gab-predict:v1
```

---

## 🔐 Authentification

- Identifiants par défaut (démo) : **admin / admin123**
- Modifiables dans `main.py` (`USERS`)
- ⚠️ En production, utilisez une solution d’auth robuste et changez `SECRET_KEY`

---

## 📡 Endpoints principaux

| Méthode | Route                             | Description                                  |
|--------:|-----------------------------------|----------------------------------------------|
| `GET`   | `/login`                          | Page de connexion                             |
| `POST`  | `/login`                          | Authentification                              |
| `GET`   | `/app`                            | Interface principale (formulaire de prédiction) |
| `POST`  | `/predict`                        | Prédire un montant à partir d’une date (JSON) |
| `GET`   | `/predict?date=23-06-2021`        | Prédiction via query string                   |
| `GET`   | `/health`                         | État de l’app et du modèle                    |
| `POST`  | `/reload-model`                   | Recharger `model.pkl`                         |

### Exemple `POST /predict`
```bash
curl -X POST "http://localhost:8000/predict" \
  -H "Content-Type: application/json" \
  -d '{"date":"23-06-2021"}'
```
Réponse :
```json
{
  "date": "23-06-2021",
  "prediction": 19500.75
}
```

> 📅 **Format de date** : l’UI et l’API acceptent des dates au format `JJ-MM-AAAA` (ex: `23-06-2021`).

---

## 🧠 Détails ML

- Le modèle est sérialisé dans `model.pkl` et **doit exposer** une méthode `predict(date)`.
- `date_predictor.py` inclut une classe `DatePredictor` qui :  
  - génère des features calendrier (`jour`, `mois`, `annee`, `jour_de_la_semaine`)  
  - gère des **lags** (par défaut 364/728/1092 jours) pour les prédictions séquentielles  
- `main.py` charge le modèle au démarrage et appelle `model.predict(payload.date)` dans l’endpoint `/predict`.

---

## 🧪 Développement & Debug

- Santé de l’app : `GET /health`
- Rechargement du modèle (sans redémarrer) : `POST /reload-model`
- CORS : ouvert (`*`) par défaut pour simplifier les tests front

---

## 🔧 Technologies

- **Backend** : [FastAPI](https://fastapi.tiangolo.com/), [Uvicorn](https://www.uvicorn.org/)
- **ML** : [XGBoost](https://xgboost.ai/), [scikit-learn](https://scikit-learn.org/), [pandas](https://pandas.pydata.org/)
- **Frontend** : HTML5, CSS3, [Jinja2](https://jinja.palletsprojects.com/)
- **Sessions** : Starlette Middleware
- **Sérialisation** : Joblib
- **Conteneurisation** : Docker

---

## ✅ Checklist Prod

- [ ] Définir `SECRET_KEY` par une valeur forte (env var)  
- [ ] Changer les identifiants par défaut  
- [ ] Ajouter des logs/monitoring  
- [ ] Restreindre CORS (`allow_origins`)  
- [ ] Sauvegarder et versionner le modèle (`model.pkl`)  

