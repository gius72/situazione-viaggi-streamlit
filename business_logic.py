import pandas as pd
from datetime import datetime, timedelta

# --- Funzioni di utilità ---
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

# --- Costanti ---
STATO_OPTIONS = [
    "Manca", "Manca (occupa spazio)", "Respinto", "Respinto (occupa spazio)",
    "Stralcio", "Stralcio (occupa spazio)", "In carico"
]

RITARDI_COLS = [
    "Nr. Viaggio", "Descrizione Trasportatore", "Data di carico", "Orario di presentazione da",
    "Descr.Info Standing Trailer Pianificato", "Nazione Dest", "Porta", "Stato"
]

# --- Funzioni di business logic identiche al desktop ---

def filtra_ritardi(df, nazione, data_anticipi):
    if data_anticipi is None:
        return pd.DataFrame()
    data_col = get_col(df, ["Data di carico", "Data Carico"])
    evento_col = get_col(df, ["Evento Magazzino"])
    chiusura_col = get_col(df, ["Data Chiusura Scivola"])
    naz_col = "Nazione Dest"
    df = df.copy()
    if data_col is not None:
        df["__data"] = df[data_col].apply(robust_parse_date)
    else:
        df["__data"] = pd.NaT
    mask = pd.Series([True] * len(df))
    if evento_col and evento_col in df.columns:
        mask = mask & (df[evento_col].fillna("").str.strip().str.upper() == "CPF")
    if chiusura_col and chiusura_col in df.columns:
        mask = mask & (df[chiusura_col].isnull() | (df[chiusura_col] == ""))
    if naz_col in df.columns:
        if nazione == "IT":
            mask = mask & (df[naz_col].str.strip().str.upper() == "IT")
        else:
            mask = mask & (df[naz_col].str.strip().str.upper() != "IT")
    if not df.empty and data_col is not None and data_anticipi is not None:
        data_anticipi = pd.to_datetime(data_anticipi)
        mask = mask & (df["__data"] < data_anticipi)
    df = df[mask]
    if "__data" in df.columns:
        df = df.drop(columns="__data")
    return df.reset_index(drop=True)

def filtra_anticipi(shipment_df, zloadplan_df, nazione, data_anticipi):
    if data_anticipi is None:
        return pd.DataFrame()
    v_shi = get_col(shipment_df, ["Nr. Viaggio"])
    v_zlp = get_col(zloadplan_df, ["Viaggio"])
    naz_dest_zlp = get_col(zloadplan_df, ["Nazione Dest"])
    data_col = get_col(shipment_df, ["Data di carico", "Data Carico"])
    evento_col = get_col(shipment_df, ["Evento Magazzino"])
    chiusura_col = get_col(shipment_df, ["Data Chiusura Scivola"])
    if None in [v_shi, v_zlp, naz_dest_zlp, data_col, evento_col, chiusura_col]:
        raise ValueError(f"Colonne richieste mancanti")
    merged = pd.merge(shipment_df, zloadplan_df[[v_zlp, naz_dest_zlp]].drop_duplicates(), left_on=v_shi, right_on=v_zlp, how="left")
    data_anticipi = pd.to_datetime(data_anticipi)
    mask = (
        (merged[evento_col] == "CPF") &
        (merged[chiusura_col].notnull()) & (merged[chiusura_col] != "") &
        (merged[data_col].apply(robust_parse_date) == data_anticipi)
    )
    if nazione == "IT":
        mask = mask & (merged[naz_dest_zlp].str.strip().str.upper() == "IT")
    else:
        mask = mask & (merged[naz_dest_zlp].str.strip().str.upper() != "IT")
    result = merged[mask].reset_index(drop=True)
    return result

def filtra_ritardo_scarico(shipment_df, data_anticipi):
    if data_anticipi is None:
        return pd.DataFrame()
    nr_viaggio = get_col(shipment_df, ["Nr. Viaggio"])
    desc_trasp = get_col(shipment_df, ["Descrizione Trasportatore"])
    evento_magazzino = get_col(shipment_df, ["Evento Magazzino"])
    data_consegna = get_col(shipment_df, ["Data di consegna", "Data di carico", "Data Carico"])
    data_checkin = get_col(shipment_df, ["Data Check-in Effettiva"])
    data_chiusura = get_col(shipment_df, ["Data Chiusura Scivola"])
    if None in [nr_viaggio, desc_trasp, evento_magazzino, data_consegna, data_checkin, data_chiusura]:
        return pd.DataFrame()
    df = shipment_df.copy()
    df["__data"] = df[data_consegna].apply(robust_parse_date)
    max_data = pd.to_datetime(data_anticipi)
    mask1 = (
        (df[evento_magazzino].fillna("").str.strip().str.upper() == "SPF") &
        (df[data_checkin].isnull() | (df[data_checkin] == "")) &
        (df[data_chiusura].isnull() | (df[data_chiusura] == "")) &
        (df["__data"] < max_data)
    )
    df1 = df.loc[mask1, [nr_viaggio, desc_trasp, evento_magazzino, data_consegna]].copy()
    df1["Responsabilità"] = "TRASPORTO"
    mask2 = (
        (df[evento_magazzino].fillna("").str.strip().str.upper() == "SPF") &
        (df[data_checkin].notnull() & (df[data_checkin] != "")) &
        (df[data_chiusura].isnull() | (df[data_chiusura] == "")) &
        (df["__data"] < max_data)
    )
    df2 = df.loc[mask2, [nr_viaggio, desc_trasp, evento_magazzino, data_consegna]].copy()
    df2["Responsabilità"] = "MAGAZZINO"
    out = pd.concat([df1, df2], ignore_index=True).drop_duplicates()
    if "__data" in out.columns:
        out = out.drop(columns="__data")
    out.columns = ["Nr. Viaggio", "Descrizione Trasportatore", "Evento Magazzino", "Data di consegna", "Responsabilità"]
    return out

def filtra_anticipi_scarico(shipment_df, data_anticipi):
    if data_anticipi is None:
        return pd.DataFrame()
    nr_viaggio_col = get_col(shipment_df, ["Nr. Viaggio"])
    ora_chiusura_col = get_col(shipment_df, ["Ora Chiusura Scivola"])
    data_consegna_col = get_col(shipment_df, ["Data di consegna"])
    data_chiusura_col = get_col(shipment_df, ["Data Chiusura Scivola"])
    evento_col = get_col(shipment_df, ["Evento Magazzino"])
    if None in [nr_viaggio_col, ora_chiusura_col, data_consegna_col, data_chiusura_col, evento_col]:
        return pd.DataFrame()
    df = shipment_df.copy()
    df["__data_consegna"] = df[data_consegna_col].apply(robust_parse_date)
    data_anticipi_dt = pd.to_datetime(data_anticipi)
    mask = (
        (df[data_chiusura_col].notnull()) & (df[data_chiusura_col] != "") &
        (df["__data_consegna"].dt.date == data_anticipi_dt.date()) &
        (df[evento_col].fillna("").str.strip().str.upper() == "SPF")
    )
    out = df.loc[mask, [nr_viaggio_col, ora_chiusura_col, data_consegna_col, data_chiusura_col]].copy()
    if "__data_consegna" in out.columns:
        out = out.drop(columns="__data_consegna")
    out.columns = ["Nr. Viaggio", "Ora Chiusura Scivola", "Data di consegna", "Data Chiusura Scivola"]
    return out

def viaggi_piazzale_mancanti(shipment_tracking_df, data_anticipi):
    if data_anticipi is None:
        return pd.DataFrame(), "Nessuna data selezionata"
    df = shipment_tracking_df.copy()
    colonne_richieste = [
        "Descr.Info Standing Trailer Pianificato",
        "Evento Magazzino",
        "Data Reg.C.I.Pos.",
        "Nr. Viaggio",
        "Descrizione Trasportatore",
        "Data di carico",
        "Orario di presentazione da",
        "Nr. Targa Pianificata"
    ]
    df.columns = [c.strip() for c in df.columns]
    missing = [c for c in colonne_richieste if not any(c.replace(" ", "").lower() == cc.replace(" ", "").lower() for cc in df.columns)]
    if missing:
        return None, f"Colonne mancanti in Shipment Tracking: {missing}"
    col_map = {}
    for r in colonne_richieste:
        found = [c for c in df.columns if c.replace(" ", "").lower() == r.replace(" ", "").lower()]
        if found:
            col_map[r] = found[0]
    f1 = df[col_map["Descr.Info Standing Trailer Pianificato"]].fillna("").str.strip().str.upper() == "A PIAZZALE"
    f2 = df[col_map["Evento Magazzino"]].fillna("").str.strip().str.upper() == "CPF"
    f3 = df[col_map["Data Reg.C.I.Pos."]].isnull() | (df[col_map["Data Reg.C.I.Pos."]] == "")
    trasportatore = df[col_map["Descrizione Trasportatore"]].fillna("").str.strip().str.upper()
    f4 = trasportatore != "NUMBER 1 LOGISTICS GROUP S.P.A."
    orario = pd.to_datetime(df[col_map["Orario di presentazione da"]].fillna(""), format="%H:%M:%S", errors="coerce").dt.time
    from datetime import time
    f5 = (orario >= time(7, 0, 0)) & (orario <= time(17, 0, 0))
    filtro = f1 & f2 & f3 & f4 & f5
    colonne_gui = [
        "Nr. Viaggio",
        "Descrizione Trasportatore",
        "Data di carico",
        "Orario di presentazione da",
        "Descr.Info Standing Trailer Pianificato",
        "Nr. Targa Pianificata"
    ]
    colonne_gui_real = [col_map[c] for c in colonne_gui]
    out = df.loc[filtro, colonne_gui_real]
    if not out.empty:
        data_col = get_col(out, ["Data di carico", "Data Carico"])
        out["__data"] = out[data_col].apply(robust_parse_date)
        data_anticipi_dt = pd.to_datetime(data_anticipi)
        out = out[out["__data"].dt.date == data_anticipi_dt.date()]
        out = out.drop(columns="__data")
    if out.empty:
        return out, "Nessun viaggio a piazzale mancante trovato con i criteri specificati."
    return out, f"Trovati {len(out)} viaggi a piazzale mancanti con i criteri specificati."

def viaggi_bloccati(zloadplan_df, data_anticipi):
    if data_anticipi is None:
        return pd.DataFrame(), "Nessuna data selezionata"
    col_viaggio = get_col(zloadplan_df, ["Viaggio"])
    col_sped = get_col(zloadplan_df, ["DescrSpedizioniere"])
    col_naz = get_col(zloadplan_df, ["Nazione Dest"])
    col_stato = get_col(zloadplan_df, ["Stato"])
    col_data = get_col(zloadplan_df, ["Data Carico", "Data di carico"])
    if None in [col_viaggio, col_sped, col_naz, col_stato, col_data]:
        return pd.DataFrame(), f"Colonne richieste mancanti nel file ZLOADPLAN"
    df = zloadplan_df.copy()
    df["__data"] = df[col_data].apply(robust_parse_date)
    max_data = pd.to_datetime(data_anticipi) if data_anticipi else df["__data"].max()
    max_data_only = max_data.date() if pd.notnull(max_data) else max_data
    df["__stato"] = (
        df[col_stato]
        .astype(str)
        .str.replace("\u00A0", "", regex=False)
        .str.strip()
        .str.upper()
        .str.replace(".", "", regex=False)
        .str.replace("\t", "", regex=False)
        .str.replace("\r", "", regex=False)
        .str.replace("\n", "", regex=False)
    )
    mask = (df["__data"] == max_data) & (df["__stato"].str.startswith("PROGR"))
    df = df[mask].drop_duplicates(subset=[col_viaggio])
    df = df[[col_viaggio, col_sped, col_naz, col_stato, "__data"]].reset_index(drop=True)
    df.columns = ["Viaggio", "DescrSpedizioniere", "Nazione Dest", "Stato", "Data Carico"]
    df["Data Carico"] = df["Data Carico"].apply(lambda x: x.strftime("%d/%m/%Y") if pd.notnull(x) else "")
    return df, f"Trovati {len(df)} viaggi bloccati con Stato=PROGR e Data Carico selezionata ({max_data_only}) (senza duplicati)."