# 1_🏠_Home_&_Data.py
import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd
import numpy as np
import re

# --- Seitenkonfiguration (Muss der erste Streamlit-Befehl sein) ---
st.set_page_config(
    page_title="Egypt Population - Home & Data",
    layout="wide",
    page_icon="🇪🇬"
)

# --- Caching-Funktion (Daten laden und bereinigen) ---
@st.cache_data(ttl=3600) # Daten für 1 Stunde cachen
def load_and_clean_data(url):
    """
    Scrapt Bevölkerungsdaten von der angegebenen URL, bereinigt sie und gibt ein Pandas DataFrame zurück.
    """
    # --- Helper Function Definitions (Moved to the top) ---
    def clean_numeric_column(col):
        # Stellt sicher, dass die Spalte zuerst als Serie vom Typ String behandelt wird
        col_str = col.astype(str)
        cleaned_col = col_str.str.replace(",", "", regex=False).str.strip()
        # Behandelt potenzielle Nicht-String-Werte während des Ersetzens vor der Konvertierung
        cleaned_col = cleaned_col.replace("...", np.nan, regex=False)
        return pd.to_numeric(cleaned_col, errors="coerce")

    def clean_text_column(text):
        if pd.isna(text): return None
        text = str(text)
        # Behält grundlegende alphanumerische Zeichen, arabischen Unicode-Bereich, Bindestriche und Leerzeichen
        text = re.sub(r"[^\\w\\s\\u0600-\\u06FF\\-]", "", text)
        text = re.sub(r"\\s+", " ", text).strip()
        return text if text else None # Gibt None zurück, wenn nach der Bereinigung leer

    def clean_column_name(col_name):
        # Entfernt Daten, Sonderzeichen, zusätzliche Leerzeichen, behält das Schlüsselwort 'Population'
        col_name_str = str(col_name) # Sicherstellen, dass es ein String ist
        cleaned = re.sub(r'\d{4}-\d{2}-\d{2}', '', col_name_str) # Entfernt YYYY-MM-DD
        cleaned = re.sub(r'[()\[\]]+', '', cleaned) # Entfernt Klammern/Eckklammern
        cleaned = re.sub(r'\s+', '', cleaned).strip() # Entfernt Leerzeichen
        return cleaned

    def extract_year(column_name):
        match = re.search(r'\d{4}', str(column_name)) # Stellt sicher, dass column_name ein String ist
        return int(match.group(0)) if match else None
    # --- End Helper Function Definitions ---


    st.info(f"Fetching data from {url}...") # Info für den Benutzer
    try:
        output = requests.get(url, timeout=15) # Timeout leicht erhöht
        output.raise_for_status() # Fehler bei schlechten Antworten auslösen
    except requests.exceptions.RequestException as e:
        # Zeigt den Fehler in der App an, gibt aber None zurück, um den Ablauf nicht zu blockieren
        st.error(f"Error fetching URL: {e}")
        return None

    st.info("Parsing HTML content...")
    bs_output = BeautifulSoup(markup=output.text, features="lxml") # lxml-Parser verwenden

    table_output = bs_output.find(name='table', attrs={'id': 'tl'})
    if table_output is None:
        st.error("Die Datentabelle mit id='tl' konnte auf der Seite nicht gefunden werden.")
        return None

    # --- Tabellenüberschriften extrahieren ---
    try:
        # Leerraum entfernen und nur relevante Spalten behalten
        table_columns_raw = [x.get_text(strip=True) for x in table_output.find_all('th')]
        # Filtert leere Header heraus, die manchmal vorkommen
        table_columns = [col for col in table_columns_raw if col]
    except Exception as e:
        st.error(f"Fehler beim Extrahieren der Tabellenüberschriften: {e}")
        return None

    # --- Tabellenkörperdaten extrahieren ---
    table_body = table_output.find('tbody') # Spezifischer
    if table_body is None:
         st.error("Der Tabellenkörper (tbody) konnte nicht gefunden werden.")
         return None

    Egypt_AD = []
    try:
        rows = table_body.find_all('tr')
        for row in rows:
            td = row.find_all('td')
            # Text extrahieren, Leerraum entfernen, letzte Spalte (Pfeil) ausschließen, falls vorhanden
            td_values = [val.get_text(strip=True) for val in td]
            if td_values and td_values[-1] == '→': # Prüfen, ob das letzte Element der Pfeil ist
                 Egypt_AD.append(td_values[:-1])
            elif td_values : # Anhängen, wenn nicht leer, auch wenn kein Pfeil vorhanden
                 Egypt_AD.append(td_values)
    except Exception as e:
        st.error(f"Fehler beim Extrahieren der Tabellenzeilen: {e}")
        return None

    if not Egypt_AD:
        st.warning("Keine Datenzeilen aus der Tabelle extrahiert.")
        return None

    st.info(f"Extracted {len(Egypt_AD)} rows of data.")

    # Spalten an Datenlänge anpassen (wichtig!)
    num_data_cols = len(Egypt_AD[0]) if Egypt_AD else 0
    if num_data_cols > 0:
        # Nimmt die ersten 'num_data_cols' nicht-leeren Header
        valid_headers = [col for col in table_columns_raw if col] # Filtert leere Strings
        if len(valid_headers) >= num_data_cols:
            table_columns = valid_headers[:num_data_cols]
        else:
            # Fallback: Wenn nicht genügend Header vorhanden sind, fülle mit Generika auf
            st.warning(f"Nicht genügend gültige Header gefunden ({len(valid_headers)}). Erwarte {num_data_cols}. Verwende generische Namen.")
            table_columns = [f'Column_{i+1}' for i in range(num_data_cols)]

    else:
        st.error("Die Anzahl der Datenspalten konnte nicht ermittelt werden.")
        return None

    # Erneute Überprüfung nach der Anpassung
    if len(table_columns) != num_data_cols:
         st.error(f"Angepasste Header-Spalten ({len(table_columns)}) stimmen nicht mit Datenspalten ({num_data_cols}) überein. Bitte Scraping-Logik prüfen.")
         st.write("Angepasste Header:", table_columns)
         st.write("Erste Datenzeile:", Egypt_AD[0] if Egypt_AD else "None")
         return None

    # --- DataFrame erstellen ---
    st.info("Creating DataFrame...")
    try:
        # Behandelt potenziell unterschiedliche Zeilenlängen robuster
        egypt_data = pd.DataFrame(Egypt_AD)
        # Benenne Spalten nur, wenn die Anzahl übereinstimmt
        if egypt_data.shape[1] == len(table_columns):
             egypt_data.columns = table_columns
        else:
             # Benenne mit generischen Namen, wenn die Anzahl nicht übereinstimmt
             egypt_data.columns = [f'Column_{i+1}' for i in range(egypt_data.shape[1])]
             st.warning(f"Spaltenanzahl ({egypt_data.shape[1]}) stimmt nicht mit Headern ({len(table_columns)}) überein. Verwende generische Spaltennamen.")

    except Exception as e:
        st.error(f"Fehler beim Erstellen des DataFrame: {e}")
        return None

    # --- Datenbereinigung (Angepasst aus Notebook) ---
    st.info("Cleaning data...")

    # Identifiziere potenzielle Bevölkerungsspalten anhand des Namensmusters (vor dem Bereinigen der Spaltennamen)
    pop_col_candidates = [col for col in egypt_data.columns if 'Population' in str(col)]
    for col in pop_col_candidates:
        if col in egypt_data.columns: # Stelle sicher, dass die Spalte existiert
            # Verwende .copy(), um SettingWithCopyWarning zu vermeiden, falls egypt_data ein Slice ist
            egypt_data[col] = clean_numeric_column(egypt_data[col].copy())

    # Bereinige die Namensspalte (Klammern entfernen) - Prüfe, ob 'Name' existiert
    if 'Name' in egypt_data.columns:
        egypt_data['Name'] = egypt_data['Name'].apply(
            lambda x: re.sub(r'\s*\[.*?\]', '', str(x)).strip() if pd.notna(x) else x
        )

    # Duplikate entfernen
    initial_rows = len(egypt_data)
    egypt_data = egypt_data.drop_duplicates()
    rows_dropped = initial_rows - len(egypt_data)
    if rows_dropped > 0:
        st.write(f"Dropped {rows_dropped} duplicate rows.")

    # Textspalten bereinigen (Status, Native) - Prüfe, ob sie existieren
    for col in ['Status', 'Native']:
        if col in egypt_data.columns:
            egypt_data[col] = egypt_data[col].apply(clean_text_column)

    # --- Fehlende Werte behandeln ---
    st.info("Handling missing values...")
    # Speichert Mittelwerte vor dem Füllen von NaNs zur späteren Verwendung
    means = {}
    # Finde numerische Spalten basierend auf dtype nach der Bereinigung
    numeric_cols_to_fill = egypt_data.select_dtypes(include=np.number).columns
    original_means = {} # Zum Speichern der Originalnamen und Mittelwerte
    for col in numeric_cols_to_fill:
        col_mean = egypt_data[col].mean()
        if pd.notna(col_mean): # Speichert nur, wenn der Mittelwert gültig ist
            means[col] = col_mean
            original_col_name = col # Standardmäßig der aktuelle Name
            for original in pop_col_candidates:
                if clean_column_name(original) == col:
                    original_col_name = original
                    break
            original_means[original_col_name] = col_mean
            egypt_data[col] = egypt_data[col].fillna(col_mean)


    # Speichert Modi vor dem Füllen von NaNs - KORRIGIERTER BLOCK
    modes = {} # Stellt sicher, dass das modes-Dict vor der Schleife definiert ist
    for col in ['Status', 'Native']:
         if col in egypt_data.columns and egypt_data[col].isna().sum() > 0:
            # Berechnet den Modus sicher
            calculated_mode = egypt_data[col].mode()
            if not calculated_mode.empty:
                mode_val = calculated_mode[0] # Nimmt den ersten Modus, falls vorhanden
            else:
                # Behandelt den Fall, dass die Spalte keinen Modus hat (z.B. nur NaNs oder leer nach Bereinigung)
                mode_val = 'Unknown' # Verwendet einen Standardwert
            modes[col] = mode_val # Speichert den verwendeten Modus (oder Standardwert)
            # Wendet fillna an und zeigt die Warnung direkt an, wenn die Modusberechnung fehlgeschlagen ist
            if calculated_mode.empty:
                 st.warning(f"Modus für Spalte '{col}' konnte nicht berechnet werden (könnte nur NaN oder leer sein). Fülle NaNs mit 'Unknown'.")
            egypt_data[col] = egypt_data[col].fillna(mode_val)

    # --- Spalten bereinigen und umbenennen (Definitionen sind jetzt oben) ---
    st.info("Renaming columns...")

    column_mapping = {}
    new_columns = []
    original_pop_cols_map = {} # Ordnet neuen Namen den ursprünglichen zu
    for col in egypt_data.columns:
        year = extract_year(col)
        cleaned_name_base = clean_column_name(col)
        final_cleaned_name = cleaned_name_base

        # Prüfe, ob die ursprüngliche Spalte (vor der Umbenennung) eine Bevölkerungsspalte war
        is_population_col = False
        if col in pop_col_candidates: # Vergleiche mit der Liste der ursprünglichen Kandidaten
             is_population_col = True

        if year and is_population_col: # Prüfe beides: Jahr extrahiert UND war ursprünglich eine Pop-Spalte
            new_name = f'population_{year}'
            column_mapping[col] = new_name
            new_columns.append(new_name)
            original_pop_cols_map[new_name] = str(col) # Zuordnung speichern
        else:
            # Prüft, ob der Spaltenname nach der Bereinigung anderer Spalten bereits existiert
            counter = 1
            while final_cleaned_name in new_columns:
                 final_cleaned_name = f"{cleaned_name_base}_{counter}"
                 counter += 1
            column_mapping[col] = final_cleaned_name
            new_columns.append(final_cleaned_name)

    egypt_data = egypt_data.rename(columns=column_mapping)

    # Fügt Metadaten zum DataFrame-Attribut für potenzielle Anzeige hinzu
    egypt_data.attrs['nan_fill_means'] = original_means # Verwendet das Dict mit ursprünglichen Namen
    egypt_data.attrs['nan_fill_modes'] = modes
    egypt_data.attrs['original_pop_cols_map'] = original_pop_cols_map


    egypt_data.reset_index(drop=True, inplace=True)
    st.info("Data cleaning complete.")
    return egypt_data

# --- App Layout ---
st.title("🇪🇬 Egypt Population Data Analysis")
st.caption("Data Source: [City Population](https://www.citypopulation.de/en/egypt/admin/)")

st.divider()

st.header("Load and Clean Data")


import os

github_url = "https://raw.githubusercontent.com/Mahmoud-Ezat/Fstreamlit/master/Desktop/Streamlit/cleaned_egypt_population_wide.csv"

with st.spinner('Loading cleaned data from GitHub...'):
    try:
        df_cleaned = pd.read_csv(github_url)
        df_cleaned.columns = [re.sub(r"[^\w\s]", "", col).strip().replace(" ", "_").lower() for col in df_cleaned.columns]
        st.session_state['cleaned_df'] = df_cleaned
        st.success("Data loaded from GitHub successfully!")
    except Exception as e:
        st.error(f"Error loading file from GitHub: {e}")
        st.session_state['cleaned_df'] = None

if 'cleaned_df' in st.session_state and st.session_state['cleaned_df'] is not None:
    df_display = st.session_state['cleaned_df']  # يستخدم الـ df من الـ session_state
    df_display = df_display.fillna('Not Available')

    st.subheader("Preview of Cleaned Data")
    st.dataframe(df_display)
    st.write(f"Shape of the cleaned data: {df_display.shape}")
else:
    st.warning("Data not loaded. Cannot display preview or analysis.")
    st.button("Try Reloading Data", on_click=lambda: st.query_params.__setitem__("reload", "true"))



# Zeigt Daten und Informationen nur an, wenn erfolgreich geladen
if 'cleaned_df' in st.session_state and st.session_state['cleaned_df'] is not None:
    df_display = st.session_state['cleaned_df'] # Verwendet das df aus dem Session-Status

    st.subheader("Preview of Cleaned Data")
    st.dataframe(df_display)
    st.write(f"Shape of the cleaned data: {df_display.shape}")

    # Zeigt Informationen zum NaN-Füllen an
    if 'nan_fill_means' in df_display.attrs and df_display.attrs['nan_fill_means']:
         with st.expander("NaN Filling Information (Numeric Columns - Mean)"):
              st.write("Original columns and mean used for filling:")
              st.json(df_display.attrs['nan_fill_means'])

    if 'nan_fill_modes' in df_display.attrs and df_display.attrs['nan_fill_modes']:
         with st.expander("NaN Filling Information (Categorical Columns - Mode)"):
             st.json(df_display.attrs['nan_fill_modes'])

    st.info("Navigate to the 'Analysis' and 'Visualizations' pages using the sidebar.")
    # *** KORREKTUR HIER ***
    st.button("Reload Data", on_click=lambda: st.query_params.__setitem__("reload", "true"), help="Click to force a refresh of the data from the source.") # Korrekte Syntax

else:
    st.warning("Data not loaded. Cannot display preview or analysis.")
    # Biete einen Button zum Neuladen an, wenn der erste Versuch fehlschlug
    if st.session_state.get('cleaned_df', 'not_loaded') is None:
         # *** KORREKTUR HIER ***
         st.button("Try Reloading Data", on_click=lambda: st.query_params.__setitem__("reload", "true")) # Korrekte Syntax
