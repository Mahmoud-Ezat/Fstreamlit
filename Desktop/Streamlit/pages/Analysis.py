# pages/2_📊_Analysis.py
import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(page_title="Egypt Population - Analysis", layout="wide", page_icon="📊")

st.title("📊 Data Analysis")

# Check if DataFrame exists in session state
if 'cleaned_df' not in st.session_state or st.session_state['cleaned_df'] is None:
    st.warning("Please load data on the '🏠 Home & Data' page first.")
    st.page_link("1_🏠_Home_&_Data.py", label="Go to Home Page", icon="🏠")
    st.stop()

df = st.session_state['cleaned_df']
# *** FÜGE DIES HINZU: Debug-Ausgabe der Spalten ***
# st.write("Columns available for analysis:", df.columns.tolist())

# --- Define expected column names (lowercase) ---
# Diese Namen sollten nach der `rename_columns` Funktion vorhanden sein
NAME_COL = 'name'
STATUS_COL = 'status'
NATIVE_COL = 'native'
POP_1996_COL = 'population_1996'
POP_2006_COL = 'population_2006'
POP_2017_COL = 'population_2017'
POP_2023_COL = 'population_2023'
GROWTH_RATE_COL = 'growth_rate' # Wird später hinzugefügt


# --- Perform Analysis ---
st.header("Analysis Results")

# Basic Statistics
with st.expander("Basic Statistics (Numeric Columns)"):
    try:
        numeric_cols = df.select_dtypes(include=np.number).columns
        if not numeric_cols.empty:
            st.dataframe(df[numeric_cols].describe().applymap('{:.0f}'.format))
        else:
            st.info("No numeric columns found for statistics.")
    except Exception as e:
        st.error(f"Error calculating basic statistics: {e}")


# Total Population and Density Calculation
total_population_misr = None
population_density = None
# *** VERWENDE KLEINSCHREIBUNG für pop_cols ***
pop_cols = [col for col in df.columns if col.startswith('population_')]

try:
    # *** VERWENDE KLEINSCHREIBUNG für 'name' ***
    if not df.empty and NAME_COL in df.columns and pop_cols:
        if len(df) > 0 and df.iloc[-1][NAME_COL].lower() == 'miṣr': # Prüfe Name in Kleinbuchstaben
            total_population_misr = df.iloc[-1][pop_cols]
            egypt_area_km2 = 1002450
            population_density = total_population_misr / egypt_area_km2

            st.subheader("Egypt Total Population and Density")
            col1, col2 = st.columns(2)
            with col1:
                st.write("**Total Population:**")
                st.dataframe(total_population_misr.apply('{:.0f}'.format))
            with col2:
                st.write("**Population Density (persons/km²):**")
                st.dataframe(population_density.apply('{:.0f}'.format))

            st.session_state['population_density'] = population_density
            st.session_state['pop_cols_for_density'] = pop_cols

        else:
            st.warning("Could not identify the 'Miṣr' (Egypt total) row for density calculation.")
            if 'population_density' in st.session_state: del st.session_state['population_density']
            if 'pop_cols_for_density' in st.session_state: del st.session_state['pop_cols_for_density']

    else:
         st.warning(f"DataFrame is empty or required columns ('{NAME_COL}', 'population_*') are missing for density calculation.")
         if 'population_density' in st.session_state: del st.session_state['population_density']
         if 'pop_cols_for_density' in st.session_state: del st.session_state['pop_cols_for_density']

except IndexError:
     st.warning("IndexError while looking for the 'Miṣr' row (DataFrame might be empty).")
     if 'population_density' in st.session_state: del st.session_state['population_density']
     if 'pop_cols_for_density' in st.session_state: del st.session_state['pop_cols_for_density']
except Exception as e:
    st.error(f"Error calculating total population/density: {e}")
    if 'population_density' in st.session_state: del st.session_state['population_density']
    if 'pop_cols_for_density' in st.session_state: del st.session_state['pop_cols_for_density']

# Prepare data for city/area analysis
df_analysis = df.copy()
if total_population_misr is not None and len(df) > 1:
     df_analysis = df.iloc[:-1].copy()
# *** VERWENDE KLEINSCHREIBUNG für 'name' ***
elif len(df)>0 and NAME_COL in df.columns and df.iloc[-1][NAME_COL].lower() != 'miṣr':
     df_analysis = df.copy()
elif len(df) <= 1 and total_population_misr is not None:
     st.warning("DataFrame only contains the total row, no area analysis possible.")
     df_analysis = pd.DataFrame()

# Top 10 Cities by Population 2023
# *** VERWENDE KLEINSCHREIBUNG für Spaltennamen ***
if POP_2023_COL in df_analysis.columns and not df_analysis.empty:
     st.subheader("Top 10 Cities/Areas by Population (2023)")
     try:
        cols_to_display = [NAME_COL, POP_2023_COL]
        if STATUS_COL in df_analysis.columns:
            cols_to_display.insert(1, STATUS_COL)

        top_10_cities = df_analysis.nlargest(10, POP_2023_COL)[cols_to_display]
        st.table(top_10_cities.style.format({POP_2023_COL: '{:,.0f}'}).hide(axis="index"))
        st.session_state['top_10_cities'] = top_10_cities
     except KeyError as e:
        st.error(f"Error accessing columns for Top 10 Cities: {e}. Required: '{NAME_COL}', '{POP_2023_COL}'. '{STATUS_COL}' optional.")
        if 'top_10_cities' in st.session_state: del st.session_state['top_10_cities']
     except Exception as e:
         st.error(f"Error finding top 10 cities: {e}")
         if 'top_10_cities' in st.session_state: del st.session_state['top_10_cities']
elif not df_analysis.empty:
     st.warning(f"Column '{POP_2023_COL}' not found for Top 10 Cities analysis.")
     if 'top_10_cities' in st.session_state: del st.session_state['top_10_cities']

# Growth Rate Calculation and Analysis
# *** VERWENDE KLEINSCHREIBUNG für Spaltennamen ***
if POP_1996_COL in df_analysis.columns and POP_2023_COL in df_analysis.columns and not df_analysis.empty:
    st.subheader("Population Growth Rate (1996 - 2023)")
    try:
        pop_1996 = df_analysis[POP_1996_COL]
        pop_2023 = df_analysis[POP_2023_COL]

        growth_rate = np.where(
            (pop_1996.notna()) & (pop_1996 != 0),
            ((pop_2023 - pop_1996) / pop_1996) * 100,
            np.nan
        )
        df_analysis[GROWTH_RATE_COL] = growth_rate # Verwende definierte Konstante
        df_analysis[GROWTH_RATE_COL] = df_analysis[GROWTH_RATE_COL].replace([np.inf, -np.inf], np.nan)

        cols_growth_display = [NAME_COL, POP_1996_COL, POP_2023_COL, GROWTH_RATE_COL]
        if STATUS_COL in df_analysis.columns:
            cols_growth_display.insert(1, STATUS_COL)

        col1_growth, col2_growth = st.columns(2)
        with col1_growth:
             st.write("**Top 10 Areas by Growth Rate:**")
             top_growth_areas = df_analysis.sort_values(GROWTH_RATE_COL, ascending=False, na_position='last').head(10)
             st.table(top_growth_areas[cols_growth_display].style.format({
                 POP_1996_COL: '{:,.0f}',
                 POP_2023_COL: '{:,.0f}',
                 GROWTH_RATE_COL: '{:.1f}%'
             }, na_rep='N/A').hide(axis="index"))
             st.session_state['top_growth_areas'] = top_growth_areas

        with col2_growth:
             st.write("**Bottom 10 Areas by Growth Rate:**")
             low_growth_areas = df_analysis.sort_values(GROWTH_RATE_COL, ascending=True, na_position='last').head(10)
             st.table(low_growth_areas[cols_growth_display].style.format({
                  POP_1996_COL: '{:,.0f}',
                  POP_2023_COL: '{:,.0f}',
                  GROWTH_RATE_COL: '{:.1f}%'
             }, na_rep='N/A').hide(axis="index"))
             st.session_state['low_growth_areas'] = low_growth_areas

        st.session_state['df_analysis_with_growth'] = df_analysis

    except KeyError as e:
        st.error(f"Error calculating growth rates: {e}. Check if '{POP_1996_COL}' and '{POP_2023_COL}' exist.")
        if 'top_growth_areas' in st.session_state: del st.session_state['top_growth_areas']
        if 'low_growth_areas' in st.session_state: del st.session_state['low_growth_areas']
        if 'df_analysis_with_growth' in st.session_state: del st.session_state['df_analysis_with_growth']
    except Exception as e:
        st.error(f"An unexpected error occurred during growth rate calculation: {e}")
        # Clear potentially corrupted session state variables
        if 'top_growth_areas' in st.session_state: del st.session_state['top_growth_areas']
        if 'low_growth_areas' in st.session_state: del st.session_state['low_growth_areas']
        if 'df_analysis_with_growth' in st.session_state: del st.session_state['df_analysis_with_growth']


elif not df_analysis.empty:
    st.warning(f"Columns '{POP_1996_COL}' or '{POP_2023_COL}' not found for growth rate analysis.")
    if 'top_growth_areas' in st.session_state: del st.session_state['top_growth_areas']
    if 'low_growth_areas' in st.session_state: del st.session_state['low_growth_areas']
    if 'df_analysis_with_growth' in st.session_state: del st.session_state['df_analysis_with_growth']
