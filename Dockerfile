FROM python:3.9-slim

WORKDIR /app

# Installa dipendenze di sistema
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    software-properties-common \
    && rm -rf /var/lib/apt/lists/*

# Copia i file necessari
COPY requirements.txt .
COPY streamlit_app.py .
COPY business_logic.py .

# Installa le dipendenze Python
RUN pip install --no-cache-dir -r requirements.txt

# Esponi la porta per Streamlit
EXPOSE 8501

# Comando per avviare l'app
CMD streamlit run streamlit_app.py --server.port=${PORT:-8501} --server.address=0.0.0.0