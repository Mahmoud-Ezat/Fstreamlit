# 1_🏠_Home_&_Data.py
import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd
import numpy as np
import re
import os # Hinzugefügt für os.path.exists, obwohl wir es hier nicht direkt verwenden

# --- Seitenkonfiguration (Muss der erste Streamlit-Befehl sein) ---
st.set_page_config(
    page_title="Egypt Population - Home & Data",
    layout="wide",
    page_icon="🇪🇬"
)

# --- Caching-Funktion (Daten laden und bereinigen - von der Webseite) ---
# Diese Funktion wird jetzt *nur* aufgerufen, wenn die GitHub-Datei nicht geladen wird.
@st.cache_data(ttl=3600)
def load_and_clean_data_from_web(url):
    """
    Scrapt Bevölkerungsdaten von der angegebenen URL, bereinigt sie und gibt ein Pandas DataFrame zurück.
    (Inhalt der Funktion ist identisch mit der vorherigen `load_and_clean_data`-Funktion)
    """
    # --- Hilfsfunktionen ---
    def clean_numeric_column(col):
        col_str = col.astype(str)
        cleaned_col = col_str.str.replace(",", "", regex=False).str.strip()
        cleaned_col = cleaned_col.replace("...", np.nan, regex=False)
        return pd.to_numeric(cleaned_col, errors="coerce")

    def clean_text_column(text):
        if pd.isna(text): return None
        text = str(text)
        text = re.sub(r"[^\\w\\s\\u0600-\\u06FF\\-]", "", text)
        text = re.sub(r"\\s+", " ", text).strip()
        return text if text else None

    def clean_column_name(col_name):
        col_name_str = str(col_name)
        cleaned = re.sub(r'\d{4}-\d{2}-\d{2}', '', col_name_str)
        cleaned = re.sub(r'[()\[\]]+', '', cleaned)
        cleaned = re.sub(r'\s+', '', cleaned).strip()
        return cleaned

    def extract_year(column_name):
        match = re.search(r'\d{4}', str(column_name))
        return int(match.group(0)) if match else None
    # --- Ende Hilfsfunktionen ---

    st.info(f"Fetching data from {url}...") # Info für Web-Scraping bleibt
    try:
        output = requests.get(url, timeout=15)
        output.raise_for_status()
    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching URL: {e}")
        return None

    st.info("Parsing HTML content...")
    bs_output = BeautifulSoup(markup=output.text, features="lxml")

    table_output = bs_output.find(name='table', attrs={'id': 'tl'})
    if table_output is None:
        st.error("Data table with id='tl' not found.")
        return None

    try:
        table_columns_raw = [x.get_text(strip=True) for x in table_output.find_all('th')]
        table_columns = [col for col in table_columns_raw if col]
    except Exception as e:
        st.error(f"Error extracting table headers: {e}")
        return None

    table_body = table_output.find('tbody')
    if table_body is None:
         st.error("Table body (tbody) not found.")
         return None

    Egypt_AD = []
    try:
        rows = table_body.find_all('tr')
        for row in rows:
            td = row.find_all('td')
            td_values = [val.get_text(strip=True) for val in td]
            if td_values and td_values[-1] == '→':
                 Egypt_AD.append(td_values[:-1])
            elif td_values :
                 Egypt_AD.append(td_values)
    except Exception as e:
        st.error(f"Error extracting table rows: {e}")
        return None

    if not Egypt_AD:
        st.warning("No data rows extracted.")
        return None

    st.info(f"Extracted {len(Egypt_AD)} rows.")

    num_data_cols = len(Egypt_AD[0]) if Egypt_AD else 0
    if num_data_cols > 0:
        valid_headers = [col for col in table_columns_raw if col]
        if len(valid_headers) >= num_data_cols:
            table_columns = valid_headers[:num_data_cols]
        else:
            st.warning(f"Not enough valid headers ({len(valid_headers)}). Expected {num_data_cols}. Using generic names.")
            table_columns = [f'Column_{i+1}' for i in range(num_data_cols)]
    else:
        st.error("Could not determine number of data columns.")
        return None

    if len(table_columns) != num_data_cols:
         st.error(f"Adjusted header columns ({len(table_columns)}) mismatch data columns ({num_data_cols}). Check scraping.")
         return None

    st.info("Creating DataFrame...")
    try:
        egypt_data = pd.DataFrame(Egypt_AD)
        if egypt_data.shape[1] == len(table_columns):
             egypt_data.columns = table_columns
        else:
             egypt_data.columns = [f'Column_{i+1}' for i in range(egypt_data.shape[1])]
             st.warning(f"Column count ({egypt_data.shape[1]}) mismatch headers ({len(table_columns)}). Using generic column names.")
    except Exception as e:
        st.error(f"Error creating DataFrame: {e}")
        return None

    st.info("Cleaning data...")
    pop_col_candidates = [col for col in egypt_data.columns if 'Population' in str(col)]
    for col in pop_col_candidates:
        if col in egypt_data.columns:
            egypt_data[col] = clean_numeric_column(egypt_data[col].copy())

    if 'Name' in egypt_data.columns:
        egypt_data['Name'] = egypt_data['Name'].apply(
            lambda x: re.sub(r'\s*\[.*?\]', '', str(x)).strip() if pd.notna(x) else x
        )

    initial_rows = len(egypt_data)
    egypt_data = egypt_data.drop_duplicates()
    rows_dropped = initial_rows - len(egypt_data)
    if rows_dropped > 0:
        st.write(f"Dropped {rows_dropped} duplicate rows.")

    for col in ['Status', 'Native']:
        if col in egypt_data.columns:
            egypt_data[col] = egypt_data[col].apply(clean_text_column)

    st.info("Handling missing values...")
    means = {}
    numeric_cols_to_fill = egypt_data.select_dtypes(include=np.number).columns
    original_means = {}
    for col in numeric_cols_to_fill:
        col_mean = egypt_data[col].mean()
        if pd.notna(col_mean):
            means[col] = col_mean
            original_col_name = col
            for original in pop_col_candidates:
                if clean_column_name(original) == col:
                    original_col_name = original
                    break
            original_means[original_col_name] = col_mean
            egypt_data[col] = egypt_data[col].fillna(col_mean)

    modes = {}
    for col in ['Status', 'Native']:
         if col in egypt_data.columns and egypt_data[col].isna().sum() > 0:
            calculated_mode = egypt_data[col].mode()
            mode_val = 'Unknown' # Default
            if not calculated_mode.empty:
                mode_val = calculated_mode[0]
            else:
                 st.warning(f"Could not calculate mode for '{col}'. Filling NaNs with 'Unknown'.")
            modes[col] = mode_val
            egypt_data[col] = egypt_data[col].fillna(mode_val)

    st.info("Renaming columns...")
    column_mapping = {}
    new_columns = []
    original_pop_cols_map = {}
    for col in egypt_data.columns:
        year = extract_year(col)
        cleaned_name_base = clean_column_name(col)
        final_cleaned_name = cleaned_name_base
        is_population_col = col in pop_col_candidates

        if year and is_population_col:
            new_name = f'population_{year}'
            column_mapping[col] = new_name
            new_columns.append(new_name)
            original_pop_cols_map[new_name] = str(col)
        else:
            counter = 1
            while final_cleaned_name in new_columns:
                 final_cleaned_name = f"{cleaned_name_base}_{counter}"
                 counter += 1
            column_mapping[col] = final_cleaned_name
            new_columns.append(final_cleaned_name)

    egypt_data = egypt_data.rename(columns=column_mapping)

    egypt_data.attrs['nan_fill_means'] = original_means
    egypt_data.attrs['nan_fill_modes'] = modes
    egypt_data.attrs['original_pop_cols_map'] = original_pop_cols_map

    egypt_data.reset_index(drop=True, inplace=True)
    st.info("Data cleaning complete.")
    return egypt_data

# --- Funktion zum Laden von GitHub (mit Caching) ---
@st.cache_data(ttl=3600) # Cacht auch das Laden von GitHub
def load_data_from_github(github_url):
    """Lädt eine CSV-Datei von GitHub und gibt ein Pandas DataFrame zurück."""
    # *** st.info-Zeile hier entfernt ***
    # st.info(f"Attempting to load cleaned data from GitHub: {github_url}...")
    try:
        df = pd.read_csv(github_url)
        # Bereinigt Spaltennamen direkt nach dem Laden
        df.columns = [re.sub(r"[^\w\s]", "", str(col)).strip().replace(" ", "_").lower() for col in df.columns]
        st.success("Data loaded from GitHub successfully!")
        return df
    except Exception as e:
        st.warning(f"Could not load file from GitHub: {e}. Will attempt web scraping.")
        return None

# --- App Layout ---
st.title("🇪🇬 Egypt Population Data Analysis")
st.caption("Data Source: [City Population](https://www.citypopulation.de/en/egypt/admin/) / Pre-cleaned GitHub CSV")

st.divider()

st.header("Load and Clean Data")

# Definiere URLs
web_url = "https://www.citypopulation.de/en/egypt/admin/"
github_url = "https://raw.githubusercontent.com/Mahmoud-Ezat/Fstreamlit/master/Desktop/Streamlit/cleaned_egypt_population_wide.csv"

# Überprüfe Query-Parameter für erzwungenes Neuladen
query_params = st.query_params
force_reload = query_params.get("reload", ["false"])[0].lower() == "true"

# Lade-Logik: Versuche zuerst GitHub, dann Web-Scraping
if 'cleaned_df' not in st.session_state or st.session_state['cleaned_df'] is None or force_reload:
    if force_reload:
        st.warning("Forcing data reload...")
        load_data_from_github.clear() # Lösche GitHub-Cache
        load_and_clean_data_from_web.clear() # Lösche Web-Scraping-Cache

    # 1. Versuch: GitHub
    df_loaded = load_data_from_github(github_url)

    # 2. Versuch: Web-Scraping (nur wenn GitHub fehlschlägt)
    if df_loaded is None:
        st.info("GitHub load failed, attempting web scraping...")
        with st.spinner('Fetching and cleaning data from web... Please wait.'):
            df_loaded = load_and_clean_data_from_web(web_url)

    # Speichere das Ergebnis (DataFrame oder None) im Session State
    if df_loaded is not None:
        st.session_state['cleaned_df'] = df_loaded
        st.success("Data loading and cleaning complete!")
        if force_reload:
            st.query_params.clear() # Parameter nach erfolgreichem Laden entfernen
    else:
        st.error("Failed to load data from both GitHub and Web Scraping.")
        st.session_state['cleaned_df'] = None
else:
    st.success("Cleaned data already in session.")


# --- Anzeige der Datenvorschau und Infos (NUR EINMAL) ---
if 'cleaned_df' in st.session_state and st.session_state['cleaned_df'] is not None:
    df_display = st.session_state['cleaned_df']

    st.subheader("Preview of Cleaned Data")
    # Fülle NaNs nur für die Anzeige, nicht im session_state
    st.dataframe(df_display.head(10).fillna("N/A"))
    st.write(f"Shape of the cleaned data: {df_display.shape}")

    # Zeige NaN-Füllinfos an, falls vorhanden (nur wenn vom Web-Scraping geladen)
    if 'nan_fill_means' in df_display.attrs and df_display.attrs['nan_fill_means']:
         with st.expander("NaN Filling Information (Numeric Columns - Mean, if scraped)"):
              st.write("Original columns and mean used for filling:")
              st.json(df_display.attrs['nan_fill_means'])

    if 'nan_fill_modes' in df_display.attrs and df_display.attrs['nan_fill_modes']:
         with st.expander("NaN Filling Information (Categorical Columns - Mode, if scraped)"):
             st.json(df_display.attrs['nan_fill_modes'])

    st.info("Navigate to the 'Analysis' and 'Visualizations' pages using the sidebar.")
    st.button("Reload Data", on_click=lambda: st.query_params.__setitem__("reload", "true"), help="Click to force a refresh of the data.")

else:
    st.warning("Data not loaded. Cannot display preview or analysis.")
    # Biete Button zum erneuten Versuch, falls vorheriger Ladevorgang fehlgeschlagen ist
    if st.session_state.get('cleaned_df', 'not_loaded') is None:
        st.button("Try Reloading Data", on_click=lambda: st.query_params.__setitem__("reload", "true"))
