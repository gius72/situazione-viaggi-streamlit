# 🐳 Deploy con Docker su Render.com

## 📋 Prerequisiti
- Account GitHub (gratuito)
- Account Render.com (gratuito)

## 🔧 Step 1: Preparazione Repository GitHub

### 1.1 Crea Repository su GitHub
1. Vai su https://github.com
2. Click "New repository"
3. Nome: `situazione-viaggi-streamlit`
4. Seleziona "Public" (per piano gratuito Render)
5. Click "Create repository"

### 1.2 Upload Files
Carica questi file nel repository:
- `streamlit_app.py` (file principale)
- `business_logic.py` (logica di business)
- `requirements.txt` (dipendenze)
- `Dockerfile` (configurazione Docker)
- `render.yaml` (configurazione Render)
- `README.md` (documentazione)

## 🌐 Step 2: Deploy su Render.com

### 2.1 Crea Account Render
1. Vai su https://render.com
2. Click "Get Started for Free"
3. Registrati con GitHub (consigliato)

### 2.2 Deploy con Blueprint
1. Nel dashboard Render, click "New +"
2. Seleziona "Blueprint"
3. Connetti il tuo repository GitHub
4. Render rileverà automaticamente il file `render.yaml`
5. Click "Apply Blueprint"

### 2.3 Alternativa: Deploy Manuale
Se il Blueprint non funziona:
1. Nel dashboard Render, click "New +"
2. Seleziona "Web Service"
3. Connetti il tuo repository GitHub
4. Seleziona "Docker" come runtime
5. Lascia vuoti i campi Build Command e Start Command
6. Click "Create Web Service"

## 🔗 Step 3: Accesso all'App

### 3.1 URL dell'App
- L'URL sarà: `https://situazione-viaggi.onrender.com`
- (sostituisci con il nome che hai scelto)

### 3.2 Test Funzionalità
1. Apri l'URL nel browser
2. Testa upload dei file Excel
3. Verifica tutte le funzionalità

## 🔄 Step 4: Aggiornamenti

### 4.1 Modifiche al Codice
1. Modifica i file localmente
2. Carica su GitHub (via web o git push)
3. Render rileverà automaticamente le modifiche
4. Auto-deploy in 5-10 minuti

## ⚙️ Configurazioni Avanzate

### Limiti Piano Gratuito
- 512MB RAM
- 0.1 CPU
- 750 ore/mese
- Si "addormenta" dopo 15 min di inattività

### Problemi Comuni
- **Build lenta**: Il primo build Docker può richiedere 10-15 minuti
- **Timeout**: Se l'app non risponde entro 30 secondi, Render mostrerà un errore
- **Memoria**: Se l'app usa più di 512MB, potrebbe essere terminata

## 📞 Supporto
- Render Docs: https://render.com/docs
- Streamlit Docs: https://docs.streamlit.io