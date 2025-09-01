# Dockerfile
# 1. Partir d'une image Python officielle
FROM python:3.12-slim

# 2. Définir le répertoire de travail dans le conteneur
WORKDIR /app

# Ajoute le dossier src au chemin de recherche des modules Python
ENV PYTHONPATH="/app/src:${PYTHONPATH}"

# Désactive la BDD par défaut (HF)
ENV DATABASE_ENABLED=false

# 3. Copier les fichiers nécessaires
COPY requirements.txt .
COPY src/ ./src/
COPY models/ ./models/

# 4. Installer uv et les dépendances
RUN pip install uv
RUN uv pip install --system --no-cache-dir -r requirements.txt

# 5. Exposer le port sur lequel l'API va tourner
#EXPOSE 8000

# 6. Commande pour lancer l'API au démarrage du conteneur
#CMD ["uvicorn", "futurisys_churn_api.api.main:app", "--host", "0.0.0.0", "--port", "8000", "--app-dir", "src/"]

# HF écoute via $PORT (généralement 7860)
EXPOSE 7860

# Important: utiliser $PORT
CMD ["sh", "-c", "uvicorn futurisys_churn_api.api.main:app --host 0.0.0.0 --port ${PORT:-7860} --app-dir src/"]