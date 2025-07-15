# 🚛 Situazione Viaggi - Web App

Applicazione web per l'analisi di ritardi e anticipi nei viaggi Italia/Estero.

## 🌟 Funzionalità

### 📊 Quadranti Principali
- **Ritardi Italia/Estero**: Analisi ritardi con stati modificabili
- **Anticipi Italia/Estero**: Viaggi in anticipo rispetto alla programmazione
- **Viaggi a Piazzale Mancanti**: Controllo viaggi non presentati
- **Viaggi Bloccati**: Viaggi con stato PROGR
- **Ritardo Scarico**: Responsabilità Trasporto/Magazzino
- **Anticipi Scarico**: Scarichi completati in tempo

### 🔧 Funzionalità Avanzate
- Upload file Excel/CSV (Shipment, Click, ZLOADPLAN)
- Filtri automatici per data di riferimento
- Stati modificabili nei quadranti ritardi
- Esportazione Excel con formattazione
- Riepilogo automatico con conteggi
- Sistema Undo per eliminazione righe
- Copia dati negli appunti

## 🚀 Utilizzo Locale

### Installazione
```bash
pip install -r requirements.txt
```

### Avvio
```bash
streamlit run streamlit_app.py
```

L'app sarà disponibile su: http://localhost:8501

## 🌐 Deploy Online

Segui le istruzioni in `DEPLOY_INSTRUCTIONS.md` per il deploy su Render.com

## 📁 Struttura File

```
├── streamlit_app.py          # App principale
├── business_logic.py         # Logica di business
├── requirements.txt          # Dipendenze Python
├── DEPLOY_INSTRUCTIONS.md    # Guida deploy
└── README.md                # Questo file
```

## 📋 File Supportati

- **Shipment Tracking**: Excel (.xlsx, .xls) o CSV
- **Click**: Excel (.xlsx, .xls) o CSV (header riga 4)
- **SAP ZLOADPLAN**: Excel (.xlsx, .xls) o CSV

## 🔄 Workflow Tipico

1. **Carica i 3 file** nella sidebar
2. **Imposta data di riferimento**
3. **Popola quadranti** (singoli o tutti insieme)
4. **Modifica stati** se necessario
5. **Esporta risultati** in Excel
6. **Copia riepilogo** per reporting

## ⚙️ Configurazione

### Limiti File
- Dimensione massima: 200MB (Render gratuito)
- Formati supportati: XLSX, XLS, CSV
- Encoding: UTF-8 consigliato

### Performance
- Ottimizzato per file fino a 50k righe
- Cache automatica dei risultati
- Elaborazione in background

## 🆘 Troubleshooting

### File Non Si Carica
- Verifica formato (Excel/CSV)
- Controlla dimensione (<200MB)
- Prova a salvare come nuovo file Excel

### Errori Colonne
- Verifica nomi colonne nei file
- Controlla spazi extra nei nomi
- Usa file template se disponibili

### Performance Lenta
- Riduci dimensione file se possibile
- Usa filtri per limitare i dati
- Considera split dei file grandi

## 📞 Supporto

Per problemi o richieste di funzionalità, crea un issue nel repository GitHub.

## 🔄 Versioni

- **v1.0**: Conversione da desktop a web
- **v1.1**: Aggiunta funzionalità undo
- **v1.2**: Miglioramenti performance
- **v2.0**: Deploy cloud ready

## 📄 Licenza

Uso interno aziendale.