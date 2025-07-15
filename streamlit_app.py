import streamlit as st
import pandas as pd
import io
import base64
from datetime import datetime, timedelta
import openpyxl
from openpyxl.utils.dataframe import dataframe_to_rows
from openpyxl.worksheet.table import Table, TableStyleInfo
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode, DataReturnMode

# Importa le funzioni di business logic
from business_logic import *
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode, DataReturnMode
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode, DataReturnMode

# --- Costanti ---
STATO_OPTIONS = [
    "Manca", "Manca (occupa spazio)", "Respinto", "Respinto (occupa spazio)",
    "Stralcio", "Stralcio (occupa spazio)", "In carico"
]
RITARDI_COLS = [
    "Nr. Viaggio", "Descrizione Trasportatore", "Data di carico", "Orario di presentazione da",
    "Descr.Info Standing Trailer Pianificato", "Nazione Dest", "Porta", "Stato"
]

# --- Funzioni di utilità (identiche) ---
def robust_parse_date(val):
    try:
        if isinstance(val, (pd.Timestamp, datetime)):
            return val
        if isinstance(val, str) and "-" in val and len(val.split("-")[0]) == 4:
            return pd.to_datetime(val, errors="coerce", dayfirst=False)
        return pd.to_datetime(val, errors="coerce", dayfirst=True)
    except Exception:
        return pd.NaT

def get_col(df, variants):
    for v in variants:
        for c in df.columns:
            if c.replace(" ", "").strip().lower() == v.replace(" ", "").strip().lower():
                return c
    return None

# --- Funzioni di business (identiche al desktop) ---

def incrocio_ritardi(shipment_df, zloadplan_df, click_df):
    v_shi = get_col(shipment_df, ["Nr. Viaggio"])
    v_zlp = get_col(zloadplan_df, ["Viaggio"])
    v_cli = get_col(click_df, ["Numero Viaggio", "Pianificazione Spedizioni", "Viaggio", "ID Viaggio"])
    porta_cli = get_col(click_df, ["Porta", "porta", "PORTA", "Porta Carico", "PortaCarico"])
    naz_dest_zlp = get_col(zloadplan_df, ["Nazione Dest"])
    if v_shi is None or v_zlp is None or v_cli is None:
        raise ValueError(f"Colonne viaggio mancanti")
    if porta_cli is None:
        raise ValueError(f"Colonna 'Porta' non trovata nel file Click")
    if naz_dest_zlp is None:
        raise ValueError(f"Colonna 'Nazione Dest' non trovata nel file ZLOADPLAN")
    
    df = pd.merge(shipment_df, zloadplan_df[[v_zlp, naz_dest_zlp]].drop_duplicates(), left_on=v_shi, right_on=v_zlp, how="inner")
    df = pd.merge(df, click_df[[v_cli, porta_cli]].drop_duplicates(), left_on=v_shi, right_on=v_cli, how="inner")
    
    result = pd.DataFrame()
    col_map = {
        "Nr. Viaggio": v_shi,
        "Descrizione Trasportatore": get_col(shipment_df, ["Descrizione Trasportatore"]),
        "Data di carico": get_col(shipment_df, ["Data di carico", "Data Carico"]),
        "Orario di presentazione da": get_col(shipment_df, ["Orario di presentazione da"]),
        "Descr.Info Standing Trailer Pianificato": get_col(shipment_df, ["Descr.Info Standing Trailer Pianificato"]),
        "Nazione Dest": naz_dest_zlp,
        "Porta": porta_cli,
    }
    
    for col in RITARDI_COLS:
        if col == "Stato":
            stati = []
            checkin_col = get_col(shipment_df, ["Data Check-in Effettiva"])
            reg_pos_col = get_col(shipment_df, ["Data Reg.C.I.Pos."])
            descr_trailer_col = get_col(shipment_df, ["Descr.Info Standing Trailer Pianificato"])
            
            for i in range(len(df)):
                checkin_valorizzato = False
                reg_pos_valorizzato = False
                porta_valorizzata = False
                descr_trailer = ""
                
                if checkin_col and checkin_col in df.columns:
                    val = df.iloc[i][checkin_col]
                    checkin_valorizzato = pd.notnull(val) and str(val).strip() != ""
                
                if reg_pos_col and reg_pos_col in df.columns:
                    val = df.iloc[i][reg_pos_col]
                    reg_pos_valorizzato = pd.notnull(val) and str(val).strip() != ""
                
                if porta_cli in df.columns:
                    val = df.iloc[i][porta_cli]
                    porta_valorizzata = pd.notnull(val) and str(val).strip() != ""
                
                if descr_trailer_col and descr_trailer_col in df.columns:
                    val = df.iloc[i][descr_trailer_col]
                    descr_trailer = str(val).strip().upper() if pd.notnull(val) else ""
                
                if ((not checkin_valorizzato and descr_trailer == "ORARIO FISSO") or (not reg_pos_valorizzato and descr_trailer == "A PIAZZALE")) and not porta_valorizzata:
                    stati.append("Manca")
                elif ((not checkin_valorizzato and descr_trailer == "ORARIO FISSO") or (not reg_pos_valorizzato and descr_trailer == "A PIAZZALE")) and porta_valorizzata:
                    stati.append("Manca (occupa spazio)")
                elif ((checkin_valorizzato and descr_trailer == "ORARIO FISSO") or (reg_pos_valorizzato and descr_trailer == "A PIAZZALE")) and not porta_valorizzata:
                    stati.append("In carico")
                else:
                    stati.append("Manca")
            
            result[col] = stati
        else:
            result[col] = df[col_map[col]] if col_map[col] in df.columns else ""
    return result

# --- Configurazione pagina ---
st.set_page_config(
    page_title="Situazione Viaggi - Ritardi e Anticipi",
    page_icon="🚛",
    layout="wide"
)

# --- Inizializzazione session state ---
if 'shipment_df' not in st.session_state:
    st.session_state.shipment_df = None
if 'zloadplan_df' not in st.session_state:
    st.session_state.zloadplan_df = None
if 'click_df' not in st.session_state:
    st.session_state.click_df = None
if 'data_riferimento' not in st.session_state:
    st.session_state.data_riferimento = None
if 'undo_stack' not in st.session_state:
    st.session_state.undo_stack = []

# --- Header ---
st.title("🚛 Situazione Viaggi - Ritardi e Anticipi Italia/Estero")
st.markdown("---")

# --- Sidebar per upload files ---
with st.sidebar:
    st.header("📁 Carica File")
    
    # Upload Shipment
    shipment_file = st.file_uploader(
        "Carica file Shipment Tracking",
        type=['xlsx', 'xls', 'csv'],
        key="shipment"
    )
    
    # Upload Click
    click_file = st.file_uploader(
        "Carica file Click",
        type=['xlsx', 'xls', 'csv'],
        key="click"
    )
    
    # Upload ZLOADPLAN
    zloadplan_file = st.file_uploader(
        "Carica file SAP ZLOADPLAN",
        type=['xlsx', 'xls', 'csv'],
        key="zloadplan"
    )
    
    st.markdown("---")
    
    # Data di riferimento
    st.header("📅 Data di Riferimento")
    data_riferimento = st.date_input(
        "Seleziona data di riferimento",
        value=None,
        help="Data per il calcolo di ritardi e anticipi"
    )
    
    if data_riferimento:
        st.session_state.data_riferimento = data_riferimento
        st.success(f"Data impostata: {data_riferimento.strftime('%d/%m/%Y')}")

# --- Funzioni di caricamento file ---
def load_file(uploaded_file, file_type=""):
    if uploaded_file is not None:
        try:
            if uploaded_file.name.endswith('.csv'):
                if file_type == "click":
                    df = pd.read_csv(uploaded_file, dtype=str, header=3)
                else:
                    df = pd.read_csv(uploaded_file, dtype=str)
            else:
                if file_type == "click":
                    df = pd.read_excel(uploaded_file, dtype=str, header=3)
                else:
                    df = pd.read_excel(uploaded_file, dtype=str)
            
            df.columns = [c.strip() for c in df.columns]
            
            # Gestione speciale per file Click
            if file_type == "click":
                if "Pianificazione Spedizioni" in df.columns and "Numero Viaggio" not in df.columns:
                    df.rename(columns={"Pianificazione Spedizioni": "Numero Viaggio"}, inplace=True)
            
            # Rimozione duplicati per ZLOADPLAN
            if file_type == "zloadplan":
                v_col = get_col(df, ["Viaggio"])
                if v_col:
                    original_count = len(df)
                    df = df.drop_duplicates(subset=[v_col])
                    removed_count = original_count - len(df)
                    if removed_count > 0:
                        st.info(f"Rimossi {removed_count} duplicati dal file ZLOADPLAN")
            
            return df
        except Exception as e:
            st.error(f"Errore nel caricamento del file {file_type}: {str(e)}")
            return None
    return None

# --- Caricamento files ---
if shipment_file:
    st.session_state.shipment_df = load_file(shipment_file, "shipment")
    if st.session_state.shipment_df is not None:
        st.sidebar.success(f"✅ Shipment caricato ({len(st.session_state.shipment_df)} righe)")

if click_file:
    st.session_state.click_df = load_file(click_file, "click")
    if st.session_state.click_df is not None:
        st.sidebar.success(f"✅ Click caricato ({len(st.session_state.click_df)} righe)")

if zloadplan_file:
    st.session_state.zloadplan_df = load_file(zloadplan_file, "zloadplan")
    if st.session_state.zloadplan_df is not None:
        st.sidebar.success(f"✅ ZLOADPLAN caricato ({len(st.session_state.zloadplan_df)} righe)")

# --- Status files ---
col1, col2, col3 = st.columns(3)
with col1:
    if st.session_state.shipment_df is not None:
        st.success("📊 Shipment Tracking: Caricato")
    else:
        st.warning("📊 Shipment Tracking: Non caricato")

with col2:
    if st.session_state.click_df is not None:
        st.success("📊 Click: Caricato")
    else:
        st.warning("📊 Click: Non caricato")

with col3:
    if st.session_state.zloadplan_df is not None:
        st.success("📊 ZLOADPLAN: Caricato")
    else:
        st.warning("📊 ZLOADPLAN: Non caricato")

st.markdown("---")

# --- Pulsanti di controllo ---
col1, col2, col3 = st.columns(3)

# --- Funzioni di popolamento ---
def popola_ritardi_italia_estero():
    try:
        if st.session_state.shipment_df is None or st.session_state.zloadplan_df is None or st.session_state.click_df is None:
            st.error("Caricare tutti i file necessari!")
            return False
        if st.session_state.data_riferimento is None:
            st.error("Selezionare la data di riferimento!")
            return False
        
        with st.spinner("Popolamento ritardi in corso..."):
            df_ritardi = incrocio_ritardi(st.session_state.shipment_df, st.session_state.zloadplan_df, st.session_state.click_df)
            df_it = filtra_ritardi(df_ritardi, "IT", st.session_state.data_riferimento)
            df_est = filtra_ritardi(df_ritardi, "ESTERO", st.session_state.data_riferimento)
            
            st.session_state.ritardi_italia = df_it
            st.session_state.ritardi_estero = df_est
            
            st.success(f"Popolati i quadranti Ritardi ITALIA ({len(df_it)} righe) / ESTERO ({len(df_est)} righe)")
            return True
    except Exception as e:
        st.error(f"Errore: {str(e)}")
        return False

def popola_anticipi_italia_estero():
    try:
        if st.session_state.shipment_df is None or st.session_state.zloadplan_df is None:
            st.error("Caricare Shipment Tracking e SAP ZLOADPLAN!")
            return False
        if st.session_state.data_riferimento is None:
            st.error("Selezionare la data di riferimento!")
            return False
        
        with st.spinner("Popolamento anticipi in corso..."):
            df_it = filtra_anticipi(st.session_state.shipment_df, st.session_state.zloadplan_df, "IT", st.session_state.data_riferimento)
            df_est = filtra_anticipi(st.session_state.shipment_df, st.session_state.zloadplan_df, "ESTERO", st.session_state.data_riferimento)
            
            st.session_state.anticipi_italia = df_it
            st.session_state.anticipi_estero = df_est
            
            st.success(f"Popolati i quadranti Anticipi ITALIA ({len(df_it)} righe) / ESTERO ({len(df_est)} righe)")
            return True
    except Exception as e:
        st.error(f"Errore: {str(e)}")
        return False

def popola_mezzi_mancanti():
    try:
        if st.session_state.shipment_df is None or st.session_state.data_riferimento is None:
            return False
        
        with st.spinner("Popolamento viaggi mancanti in corso..."):
            df, msg = viaggi_piazzale_mancanti(st.session_state.shipment_df, st.session_state.data_riferimento)
            st.session_state.mezzi_mancanti = df if df is not None else pd.DataFrame()
            st.success(msg)
            return True
    except Exception as e:
        st.error(f"Errore: {str(e)}")
        return False

def popola_viaggi_bloccati():
    try:
        if st.session_state.zloadplan_df is None or st.session_state.data_riferimento is None:
            return False
        
        with st.spinner("Popolamento viaggi bloccati in corso..."):
            df, msg = viaggi_bloccati(st.session_state.zloadplan_df, st.session_state.data_riferimento)
            st.session_state.viaggi_bloccati = df if df is not None else pd.DataFrame()
            st.success(msg)
            return True
    except Exception as e:
        st.error(f"Errore: {str(e)}")
        return False

def popola_ritardo_scarico():
    try:
        if st.session_state.shipment_df is None or st.session_state.data_riferimento is None:
            return False
        
        with st.spinner("Popolamento ritardi scarico in corso..."):
            df = filtra_ritardo_scarico(st.session_state.shipment_df, st.session_state.data_riferimento)
            st.session_state.ritardo_scarico = df if df is not None else pd.DataFrame()
            st.success(f"Trovati {len(df)} ritardi scarico")
            return True
    except Exception as e:
        st.error(f"Errore: {str(e)}")
        return False

def popola_anticipi_scarico():
    try:
        if st.session_state.shipment_df is None or st.session_state.data_riferimento is None:
            return False
        
        with st.spinner("Popolamento anticipi scarico in corso..."):
            df = filtra_anticipi_scarico(st.session_state.shipment_df, st.session_state.data_riferimento)
            st.session_state.anticipi_scarico = df if df is not None else pd.DataFrame()
            st.success(f"Trovati {len(df)} anticipi scarico")
            return True
    except Exception as e:
        st.error(f"Errore: {str(e)}")
        return False

def popola_tutti_i_quadranti():
    if all([st.session_state.shipment_df is not None, 
            st.session_state.zloadplan_df is not None, 
            st.session_state.click_df is not None,
            st.session_state.data_riferimento is not None]):
        
        with st.spinner("Popolamento tutti i quadranti in corso..."):
            progress_text = "Operazione in corso. Attendere..."
            progress_bar = st.progress(0, text=progress_text)
            
            # Popola ritardi
            popola_ritardi_italia_estero()
            progress_bar.progress(16, text="Ritardi popolati (16%)")
            
            # Popola anticipi
            popola_anticipi_italia_estero()
            progress_bar.progress(33, text="Anticipi popolati (33%)")
            
            # Popola mezzi mancanti
            popola_mezzi_mancanti()
            progress_bar.progress(50, text="Mezzi mancanti popolati (50%)")
            
            # Popola viaggi bloccati
            popola_viaggi_bloccati()
            progress_bar.progress(66, text="Viaggi bloccati popolati (66%)")
            
            # Popola ritardo scarico
            popola_ritardo_scarico()
            progress_bar.progress(83, text="Ritardo scarico popolato (83%)")
            
            # Popola anticipi scarico
            popola_anticipi_scarico()
            progress_bar.progress(100, text="Completato (100%)")
            
            # Aggiorna riepilogo
            aggiorna_riepilogo()
            
            st.success("Tutti i quadranti popolati con successo!")
            return True
    else:
        st.error("Caricare tutti i file e impostare la data di riferimento!")
        return False

# --- Pulsanti di controllo ---
col1, col2, col3 = st.columns(3)

with col1:
    if st.button("🔄 Popola Ritardi Italia/Estero", use_container_width=True):
        if all([st.session_state.shipment_df is not None, 
                st.session_state.zloadplan_df is not None, 
                st.session_state.click_df is not None,
                st.session_state.data_riferimento is not None]):
            popola_ritardi_italia_estero()
            st.rerun()
        else:
            st.error("Caricare tutti i file e impostare la data di riferimento!")

with col2:
    if st.button("📈 Popola Anticipi Italia/Estero", use_container_width=True):
        if all([st.session_state.shipment_df is not None, 
                st.session_state.zloadplan_df is not None,
                st.session_state.data_riferimento is not None]):
            popola_anticipi_italia_estero()
            st.rerun()
        else:
            st.error("Caricare Shipment, ZLOADPLAN e impostare la data di riferimento!")

with col3:
    if st.button("🚀 Popola Tutti i Quadranti", use_container_width=True):
        if all([st.session_state.shipment_df is not None, 
                st.session_state.zloadplan_df is not None, 
                st.session_state.click_df is not None,
                st.session_state.data_riferimento is not None]):
            popola_tutti_i_quadranti()
            st.rerun()
        else:
            st.error("Caricare tutti i file e impostare la data di riferimento!")

st.markdown("---")

# --- Funzioni per tabelle interattive ---
def create_interactive_grid(df, key, editable_columns=None, height=300):
    """Crea una tabella interattiva con AgGrid"""
    if df is None or df.empty:
        return None
    
    gb = GridOptionsBuilder.from_dataframe(df)
    gb.configure_default_column(resizable=True, filterable=True, sortable=True)
    
    # Configura colonne editabili
    if editable_columns:
        for col in editable_columns:
            if col in df.columns:
                gb.configure_column(col, editable=True)
    
    # Configura colonna Stato con dropdown se presente
    if "Stato" in df.columns:
        gb.configure_column("Stato", 
                          editable=True,
                          cellEditor="agSelectCellEditor",
                          cellEditorParams={
                              'values': STATO_OPTIONS
                          })
    
    gb.configure_selection(selection_mode="multiple", use_checkbox=True)
    gb.configure_grid_options(domLayout='normal')
    grid_options = gb.build()
    
    return AgGrid(
        df,
        gridOptions=grid_options,
        height=height,
        data_return_mode=DataReturnMode.FILTERED_AND_SORTED,
        update_mode=GridUpdateMode.MODEL_CHANGED,
        fit_columns_on_grid_load=True,
        key=key
    )

def download_excel(df, filename="export.xlsx"):
    """Crea un link per scaricare il dataframe come Excel"""
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False)
        workbook = writer.book
        worksheet = writer.sheets['Sheet1']
        
        # Formattazione
        for col in worksheet.columns:
            max_length = 0
            column = col[0].column_letter
            for cell in col:
                if cell.value:
                    max_length = max(max_length, len(str(cell.value)))
            adjusted_width = (max_length + 2)
            worksheet.column_dimensions[column].width = adjusted_width
    
    b64 = base64.b64encode(output.getvalue()).decode()
    href = f'<a href="data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;base64,{b64}" download="{filename}">📥 Scarica Excel</a>'
    return href

# --- Inizializzazione quadranti in session state ---
if 'ritardi_italia' not in st.session_state:
    st.session_state.ritardi_italia = pd.DataFrame()
if 'ritardi_estero' not in st.session_state:
    st.session_state.ritardi_estero = pd.DataFrame()
if 'anticipi_italia' not in st.session_state:
    st.session_state.anticipi_italia = pd.DataFrame()
if 'anticipi_estero' not in st.session_state:
    st.session_state.anticipi_estero = pd.DataFrame()
if 'mezzi_mancanti' not in st.session_state:
    st.session_state.mezzi_mancanti = pd.DataFrame()
if 'viaggi_bloccati' not in st.session_state:
    st.session_state.viaggi_bloccati = pd.DataFrame()
if 'ritardo_scarico' not in st.session_state:
    st.session_state.ritardo_scarico = pd.DataFrame()
if 'anticipi_scarico' not in st.session_state:
    st.session_state.anticipi_scarico = pd.DataFrame()

# --- Placeholder per i quadranti ---
st.header("📊 Quadranti")

# Quadranti superiori
col1, col2 = st.columns(2)
with col1:
    st.subheader("🇮🇹 Ritardi ITALIA")
    ritardi_italia_result = create_interactive_grid(st.session_state.ritardi_italia, "ritardi_italia", editable_columns=["Stato"])
    if ritardi_italia_result is not None and len(st.session_state.ritardi_italia) > 0:
        st.markdown(download_excel(ritardi_italia_result["data"], "ritardi_italia.xlsx"), unsafe_allow_html=True)
    
with col2:
    st.subheader("🌍 Ritardi ESTERO")
    ritardi_estero_result = create_interactive_grid(st.session_state.ritardi_estero, "ritardi_estero", editable_columns=["Stato"])
    if ritardi_estero_result is not None and len(st.session_state.ritardi_estero) > 0:
        st.markdown(download_excel(ritardi_estero_result["data"], "ritardi_estero.xlsx"), unsafe_allow_html=True)

col3, col4 = st.columns(2)
with col3:
    st.subheader("🇮🇹 Anticipi ITALIA")
    anticipi_italia_result = create_interactive_grid(st.session_state.anticipi_italia, "anticipi_italia")
    if anticipi_italia_result is not None and len(st.session_state.anticipi_italia) > 0:
        st.markdown(download_excel(anticipi_italia_result["data"], "anticipi_italia.xlsx"), unsafe_allow_html=True)
    
with col4:
    st.subheader("🌍 Anticipi ESTERO")
    anticipi_estero_result = create_interactive_grid(st.session_state.anticipi_estero, "anticipi_estero")
    if anticipi_estero_result is not None and len(st.session_state.anticipi_estero) > 0:
        st.markdown(download_excel(anticipi_estero_result["data"], "anticipi_estero.xlsx"), unsafe_allow_html=True)

# Quadranti inferiori
col5, col6 = st.columns(2)
with col5:
    st.subheader("🚛 Viaggi a piazzale mancanti")
    mezzi_mancanti_result = create_interactive_grid(st.session_state.mezzi_mancanti, "mezzi_mancanti")
    if mezzi_mancanti_result is not None and len(st.session_state.mezzi_mancanti) > 0:
        st.markdown(download_excel(mezzi_mancanti_result["data"], "mezzi_mancanti.xlsx"), unsafe_allow_html=True)
    
with col6:
    st.subheader("🚫 Viaggi Bloccati")
    viaggi_bloccati_result = create_interactive_grid(st.session_state.viaggi_bloccati, "viaggi_bloccati")
    if viaggi_bloccati_result is not None and len(st.session_state.viaggi_bloccati) > 0:
        st.markdown(download_excel(viaggi_bloccati_result["data"], "viaggi_bloccati.xlsx"), unsafe_allow_html=True)

col7, col8 = st.columns(2)
with col7:
    st.subheader("⏰ Ritardo Scarico")
    ritardo_scarico_result = create_interactive_grid(st.session_state.ritardo_scarico, "ritardo_scarico")
    if ritardo_scarico_result is not None and len(st.session_state.ritardo_scarico) > 0:
        st.markdown(download_excel(ritardo_scarico_result["data"], "ritardo_scarico.xlsx"), unsafe_allow_html=True)
    
with col8:
    st.subheader("⚡ Anticipi scarico")
    anticipi_scarico_result = create_interactive_grid(st.session_state.anticipi_scarico, "anticipi_scarico")
    if anticipi_scarico_result is not None and len(st.session_state.anticipi_scarico) > 0:
        st.markdown(download_excel(anticipi_scarico_result["data"], "anticipi_scarico.xlsx"), unsafe_allow_html=True)

# --- Sistema Undo ---
if 'undo_stack' not in st.session_state:
    st.session_state.undo_stack = []

def add_to_undo_stack(operation):
    """Aggiunge un'operazione allo stack undo"""
    st.session_state.undo_stack.append(operation)
    if len(st.session_state.undo_stack) > 10:  # Mantieni solo le ultime 10 operazioni
        st.session_state.undo_stack.pop(0)

def undo_last_operation():
    """Annulla l'ultima operazione"""
    if not st.session_state.undo_stack:
        st.warning("Nessuna operazione da annullare")
        return
    
    operation = st.session_state.undo_stack.pop()
    quadrant = operation['quadrant']
    row_data = operation['data']
    row_index = operation['index']
    
    # Ripristina la riga nel quadrante appropriato
    if quadrant in st.session_state:
        df = st.session_state[quadrant]
        # Inserisci la riga nella posizione originale o alla fine
        if row_index < len(df):
            df_top = df.iloc[:row_index]
            df_bottom = df.iloc[row_index:]
            df_new = pd.concat([df_top, pd.DataFrame([row_data]), df_bottom], ignore_index=True)
        else:
            df_new = pd.concat([df, pd.DataFrame([row_data])], ignore_index=True)
        st.session_state[quadrant] = df_new
        st.success(f"Riga ripristinata nel quadrante {quadrant}")
        st.rerun()

# --- Funzione per aggiornare il riepilogo ---
def aggiorna_riepilogo():
    """Aggiorna il riepilogo con i conteggi dei quadranti"""
    # Conta anticipi
    anticipi_italia = len(st.session_state.anticipi_italia)
    anticipi_estero = len(st.session_state.anticipi_estero)
    out_anticipo = anticipi_italia + anticipi_estero
    
    # Conta ritardi per stato
    out_rit_mag = 0
    out_rit_trasp = 0
    
    for df_name in ["ritardi_italia", "ritardi_estero"]:
        df = st.session_state[df_name]
        if not df.empty and "Stato" in df.columns:
            for _, row in df.iterrows():
                stato = row["Stato"]
                if stato == "In carico":
                    out_rit_mag += 1
                elif "Manca" in stato or "Respinto" in stato or "Stralcio" in stato:
                    out_rit_trasp += 1
    
    # Conta viaggi bloccati
    out_vgg_block = len(st.session_state.viaggi_bloccati)
    
    # Conta ritardi scarico per responsabilità
    in_rit_mag = 0
    in_rit_trasp = 0
    
    df = st.session_state.ritardo_scarico
    if not df.empty and "Responsabilità" in df.columns:
        for _, row in df.iterrows():
            resp = row["Responsabilità"]
            if resp == "MAGAZZINO":
                in_rit_mag += 1
            elif resp == "TRASPORTO":
                in_rit_trasp += 1
    
    # Conta anticipi scarico
    in_anticipi = len(st.session_state.anticipi_scarico)
    
    # Salva i valori nel session state
    st.session_state.riepilogo = {
        'out_anticipo': out_anticipo,
        'out_rit_mag': out_rit_mag, 
        'out_rit_trasp': out_rit_trasp,
        'out_vgg_block': out_vgg_block,
        'viaggi_mancanti': len(st.session_state.mezzi_mancanti),
        'in_rit_mag': in_rit_mag,
        'in_rit_trasp': in_rit_trasp,
        'in_anticipi': in_anticipi
    }
    
    return st.session_state.riepilogo

# --- Funzione per copiare il riepilogo in formato Excel ---
def copia_riepilogo_excel():
    """Crea una stringa con i valori del riepilogo in formato Excel"""
    if 'riepilogo' not in st.session_state:
        aggiorna_riepilogo()
    
    # Crea riga con 16 colonne
    riga = [""] * 16
    
    # Popola le colonne specificate
    riga[1] = str(st.session_state.riepilogo['out_anticipo'])      # 2: OUT: Anticipo
    riga[2] = str(st.session_state.riepilogo['out_rit_mag'])       # 3: OUT: Rit Mag
    riga[3] = str(st.session_state.riepilogo['out_rit_trasp'])     # 4: OUT: Rit Trasp
    riga[8] = str(st.session_state.riepilogo['out_vgg_block'])     # 9: OUT: Vgg Block
    riga[9] = str(st.session_state.riepilogo['viaggi_mancanti'])   # 10: OUT: Vgg Block o mancanti
    riga[11] = str(st.session_state.riepilogo['in_rit_mag'])       # 12: IN: Rit Mag
    riga[12] = str(st.session_state.riepilogo['in_rit_trasp'])     # 13: IN: Rit Trasp
    riga[13] = str(st.session_state.riepilogo['in_anticipi'])      # 14: IN: Anticipi
    
    return '\t'.join(riga)

# --- Riepilogo ---
st.markdown("---")
st.header("📋 Riepilogo")

# Aggiorna riepilogo se ci sono dati
has_data = any([
    not st.session_state.ritardi_italia.empty,
    not st.session_state.ritardi_estero.empty,
    not st.session_state.anticipi_italia.empty,
    not st.session_state.anticipi_estero.empty,
    not st.session_state.mezzi_mancanti.empty,
    not st.session_state.viaggi_bloccati.empty,
    not st.session_state.ritardo_scarico.empty,
    not st.session_state.anticipi_scarico.empty
])

if has_data:
    riepilogo = aggiorna_riepilogo()
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("OUT: Anticipo", riepilogo['out_anticipo'])
        st.metric("OUT: Rit Mag", riepilogo['out_rit_mag'])
    with col2:
        st.metric("OUT: Rit Trasp", riepilogo['out_rit_trasp'])
        st.metric("OUT: Vgg Block", riepilogo['out_vgg_block'])
    with col3:
        st.metric("IN: Rit Mag", riepilogo['in_rit_mag'])
        st.metric("IN: Rit Trasp", riepilogo['in_rit_trasp'])
    with col4:
        st.metric("IN: Anticipi", riepilogo['in_anticipi'])
        st.metric("Viaggi Mancanti", riepilogo['viaggi_mancanti'])
    
    # Pulsante per copiare il riepilogo
    if st.button("📋 Copia Riepilogo Excel", use_container_width=True):
        riepilogo_text = copia_riepilogo_excel()
        st.code(riepilogo_text, language=None)
        st.success("Riepilogo copiato! Usa CTRL+C per copiare il testo qui sopra")
    
    # Sistema Undo
    if st.session_state.undo_stack:
        st.markdown("---")
        st.subheader("↩️ Sistema Undo")
        st.write(f"Operazioni disponibili da annullare: {len(st.session_state.undo_stack)}")
        if st.button("↩️ Annulla ultima operazione"):
            undo_last_operation()
        if len(st.session_state.undo_stack) > 1:
            if st.button("↩️ Annulla tutte le operazioni"):
                while st.session_state.undo_stack:
                    undo_last_operation()
                st.rerun()
else:
    st.info("Popolare i quadranti per vedere il riepilogo")