# Utilisez une image Python officielle comme base
FROM python:3.10-slim

# Mettre à jour et installer les outils nécessaires
RUN apt-get update && apt-get install -y \
    git \
    curl \
    build-essential \
    libffi-dev  # Dépendance pour Flask-Bcrypt

# Installation de Poetry
RUN curl -sSL https://install.python-poetry.org | python3 -

# Ajouter Poetry au PATH
ENV PATH="/root/.local/bin:$PATH"

# Désactiver l'interaction de Poetry, créer des environnements virtuels, et définir les répertoires de cache et d'accueil
ENV POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_CREATE=false \
    POETRY_CACHE_DIR='/var/cache/pypoetry' \
    POETRY_HOME='/root/.local'

# Définir le répertoire de travail dans le conteneur
WORKDIR /app

# Copier les fichiers de l'application (pyproject.toml, poetry.lock)
COPY pyproject.toml poetry.lock /app/

# Installer les dépendances à partir de pyproject.toml (y compris flask-bcrypt)
RUN poetry install --no-root --no-dev

# Copier le reste des fichiers de l'application
COPY . /app

# Exposer le port 5000
EXPOSE 5000

# Commande pour démarrer l'application Flask
CMD ["python3", "-m", "flask", "run", "--host=0.0.0.0"]
