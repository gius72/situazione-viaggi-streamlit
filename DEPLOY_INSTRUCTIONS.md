# 🚀 Istruzioni Deploy Streamlit su Render.com

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
- `requirements.txt` (dipendenze)
- `README.md` (opzionale)

**Metodo 1 - Via Web:**
1. Click "uploading an existing file"
2. Trascina i file o click "choose your files"
3. Commit changes

**Metodo 2 - Via Git (se installato):**
```bash
git clone https://github.com/TUO_USERNAME/situazione-viaggi-streamlit.git
cd situazione-viaggi-streamlit
# Copia i file nella cartella
git add .
git commit -m "Initial commit"
git push origin main
```

## 🌐 Step 2: Deploy su Render.com

### 2.1 Crea Account Render
1. Vai su https://render.com
2. Click "Get Started for Free"
3. Registrati con GitHub (consigliato)

### 2.2 Crea Web Service
1. Nel dashboard Render, click "New +"
2. Seleziona "Web Service"
3. Click "Connect" accanto al tuo repository GitHub
4. Se non vedi il repo, click "Configure GitHub App"

### 2.3 Configurazione Deploy
Compila i campi:

**Basic Info:**
- **Name:** `situazione-viaggi` (o nome a scelta)
- **Region:** Frankfurt (più vicino all'Italia)
- **Branch:** `main`
- **Runtime:** `Python 3`

**Build & Deploy:**
- **Build Command:** `pip install -r requirements.txt`
- **Start Command:** `streamlit run streamlit_app.py --server.port=$PORT --server.address=0.0.0.0`
- **Runtime Environment:** `Python 3.9`

**Advanced (opzionale):**
- **Environment Variables:** Nessuna necessaria per ora

### 2.4 Deploy
1. Click "Create Web Service"
2. Render inizierà il build automaticamente
3. Attendi 5-10 minuti per il primo deploy

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
1. Modifica `streamlit_app.py` localmente
2. Carica su GitHub (via web o git push)
3. Render rileverà automaticamente le modifiche
4. Auto-deploy in 2-3 minuti

### 4.2 Monitoraggio
- Dashboard Render mostra logs e status
- In caso di errori, controlla i logs

## ⚙️ Step 5: Configurazioni Avanzate (Opzionali)

### 5.1 Dominio Personalizzato
- Piano a pagamento Render ($7/mese)
- Aggiungi il tuo dominio nelle impostazioni

### 5.2 Variabili d'Ambiente
Se necessarie, aggiungi in Render Dashboard:
- Settings → Environment
- Add Environment Variable

### 5.3 Risorse
Piano gratuito Render:
- 512MB RAM
- 0.1 CPU
- 750 ore/mese
- Si "addormenta" dopo 15 min di inattività

## 🆘 Troubleshooting

### Errore Build
- Controlla `requirements.txt`
- Verifica sintassi Python
- Guarda logs in Render Dashboard

### App Non Si Carica
- Controlla Start Command
- Verifica porta $PORT
- Controlla logs per errori

### File Upload Non Funziona
- Limite 200MB per file su Render gratuito
- Considera compressione file Excel

## 📞 Supporto
- Render Docs: https://render.com/docs
- Streamlit Docs: https://docs.streamlit.io
- GitHub Issues nel tuo repository

## 🎯 Risultato Finale
✅ App web accessibile da qualsiasi browser
✅ Upload file Excel funzionante
✅ Tutte le funzionalità desktop disponibili
✅ Auto-deploy ad ogni modifica GitHub
✅ Gratuito (con limitazioni)