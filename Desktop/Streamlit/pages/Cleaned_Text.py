# pages/4_📄_Cleaned_Text.py
import streamlit as st
import requests
from bs4 import BeautifulSoup
import re
import pandas as pd # Benötigt für pd.isna

# --- Seitenkonfiguration ---
st.set_page_config(page_title="Egypt Population - Cleaned Text", layout="wide", page_icon="📄")

st.title("📄 Cleaned Text Artifacts from Page")
st.caption("Extracted and cleaned text from paragraph tags on the source page.")

# --- Funktion zum Bereinigen von HTML (hier zur Unabhängigkeit kopiert) ---
@st.cache_data(ttl=3600) # Cacht das Ergebnis der Textbereinigung
def get_and_clean_paragraphs(url):
    """Ruft die URL ab, extrahiert Absätze und bereinigt deren Text."""
    try:
        response_text = requests.get(url, timeout=10)
        response_text.raise_for_status()
        soup_text = BeautifulSoup(response_text.content, 'lxml')
        all_paragraphs = soup_text.find_all('p') # Findet alle <p>-Tags
        cleaned_texts = []

        def clean_html_artifacts(text):
            if pd.isna(text) or str(text).strip() == '':
                return None
            soup = BeautifulSoup(str(text), 'lxml') # Verwendet lxml
            for tag in soup(['script', 'style']): # Entfernt Skript- und Stil-Tags
                tag.decompose()
            cleaned_text = soup.get_text(separator=' ', strip=True) # Holt Text, entfernt überschüssige Leerzeichen
            cleaned_text = re.sub(r'&[a-zA-Z0-9#]+;', ' ', cleaned_text) # Entfernt HTML-Entitäten
            cleaned_text = re.sub(r'<[^>]+>', '', cleaned_text) # Entfernt verbleibende Tags
            return cleaned_text if cleaned_text.strip() else None # Gibt None zurück, wenn nach Bereinigung leer

        for p_tag in all_paragraphs:
            raw_text = p_tag.get_text(separator=' ', strip=True)
            cleaned = clean_html_artifacts(raw_text)
            if cleaned:
                cleaned_texts.append(cleaned)
        return cleaned_texts

    except requests.exceptions.RequestException as e:
        st.error(f"Fehler beim Abrufen der URL für Text: {e}")
        return None
    except Exception as e:
         st.error(f"Fehler beim Extrahieren/Bereinigen von Textartefakten: {e}")
         return None

# --- Text extrahieren und anzeigen ---
url = "https://www.citypopulation.de/en/egypt/admin/" # Definiert URL erneut
cleaned_paragraphs = get_and_clean_paragraphs(url)

if cleaned_paragraphs:
    st.info(f"Found and cleaned {len(cleaned_paragraphs)} paragraphs.")
    for i, text in enumerate(cleaned_paragraphs): # Zeigt alle bereinigten Absätze an
        st.markdown(f"**Paragraph {i+1}:**")
        st.text_area(f"P{i+1}", text, height=100, disabled=True, label_visibility="collapsed") # Zeigt Text in einer deaktivierten Textarea an
        st.markdown("---")
elif cleaned_paragraphs is None:
    # Fehler wurde bereits in der Funktion angezeigt
    pass
else:
    st.info("No relevant text paragraphs found or extracted after cleaning.")