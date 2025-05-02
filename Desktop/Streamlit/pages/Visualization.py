# pages/3_📈_Visualizations.py
import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import matplotlib.ticker as mticker # Für Formatierung

st.set_page_config(page_title="Egypt Population - Visualizations", layout="wide", page_icon="📈")

st.title("📈 Visualizations")

# Prüft, ob essentielle Dataframes/Serien im Session-Status vorhanden sind
if 'cleaned_df' not in st.session_state or st.session_state['cleaned_df'] is None:
    st.warning("Please load data on the '🏠 Home & Data' page first.")
    st.page_link("1_🏠_Home_&_Data.py", label="Go to Home Page", icon="🏠")
    st.stop()

# --- Daten aus dem Session-Status abrufen ---
df = st.session_state['cleaned_df'] # Ursprüngliches bereinigtes df
# Holt Analyseergebnisse, falls gespeichert, andernfalls Nachricht anzeigen oder bei Bedarf neu berechnen
population_density = st.session_state.get('population_density', None)
pop_cols_for_density = st.session_state.get('pop_cols_for_density', None) # Verwendet den eindeutigen Schlüssel
top_10_cities = st.session_state.get('top_10_cities', None)
top_growth_areas = st.session_state.get('top_growth_areas', None)
low_growth_areas = st.session_state.get('low_growth_areas', None)
df_analysis = st.session_state.get('df_analysis_with_growth', None) # Holt df, das für die Wachstumsanalyse verwendet wurde


# --- Visualisierungen erstellen ---
st.header("Population Trends and Comparisons")

# Verwendet Tabs für verschiedene Diagramme
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "Density Trend",
    "Top Growth Areas",
    "Bottom Growth Areas",
    "Top Populated Cities",
    "Population 1996 vs 2023"
])

with tab1:
    st.subheader("Population Density Trend")
    if population_density is not None and pop_cols_for_density:
        try:
            years_str = [col.split('_')[-1] for col in pop_cols_for_density] # Holt Jahresstrings
            # Stellt sicher, dass Jahre numerisch für die Darstellung sind
            years = [int(y) for y in years_str if y.isdigit()]
            if len(years) == len(population_density.values): # Prüft, ob Längen übereinstimmen
                population_density_values = population_density.values

                fig1, ax1 = plt.subplots(figsize=(7, 5))
                ax1.plot(years, population_density_values, marker='o', color='b', linestyle='-', linewidth=2, markersize=8)
                ax1.set_xlabel('Year')
                ax1.set_ylabel("Population Density (persons/km²)")
                ax1.set_title("Population Density in Egypt Over the Years")
                ax1.grid(True)
                ax1.set_xticks(years) # Stellt sicher, dass alle Jahre als Ticks angezeigt werden
                ax1.yaxis.set_major_formatter(mticker.FormatStrFormatter('%d')) # Format als ganze Zahl
                st.pyplot(fig1)
            else:
                 st.error("Mismatch between number of population columns and extracted years for density plot.")
        except Exception as e:
            st.error(f"Error creating density plot: {e}")
    else:
        st.info("Population density data not available from Analysis page.")


with tab2:
    st.subheader("Top 10 Areas by Growth Rate (%)")
    if top_growth_areas is not None and not top_growth_areas.empty:
         try:
            # Stellt sicher, dass korrekt für das Balkendiagramm sortiert ist
            # Entferne Zeilen mit NaN-Wachstumsrate vor der Darstellung
            top_growth_plot = top_growth_areas.dropna(subset=['growth_rate']).sort_values('growth_rate', ascending=True) # Aufsteigend für horizontalen Balken

            if not top_growth_plot.empty:
                fig2, ax2 = plt.subplots(figsize=(10, 6)) # Größe leicht angepasst
                sns.barplot(y='Name', x='growth_rate', data=top_growth_plot, palette='viridis', ax=ax2, dodge=False)
                ax2.set_xlabel('Growth Rate (%)')
                ax2.set_ylabel('Area')
                ax2.set_title('Top 10 Areas by Population Growth Rate (1996 - 2023)')
                ax2.grid(axis='x', linestyle='--', alpha=0.5)
                ax2.xaxis.set_major_formatter(mticker.FormatStrFormatter('%.1f%%')) # Formatiert Achse
                plt.tight_layout() # Layout anpassen
                st.pyplot(fig2)
            else:
                st.info("No areas with valid growth rate found in the top 10.")
         except Exception as e:
             st.error(f"Error creating top growth plot: {e}")
    else:
         st.info("Top growth area data not available from Analysis page or is empty.")


with tab3:
     st.subheader("Bottom 10 Areas by Growth Rate (%)")
     if low_growth_areas is not None and not low_growth_areas.empty:
          try:
            # Sortiere und entferne NaNs
            low_growth_plot = low_growth_areas.dropna(subset=['growth_rate']).sort_values('growth_rate', ascending=True)

            if not low_growth_plot.empty:
                fig3, ax3 = plt.subplots(figsize=(12, 6))
                bars = ax3.barh(
                    low_growth_plot['Name'],
                    low_growth_plot['growth_rate'],
                    color='salmon' # Andere Farbe für unten
                )
                # Fügt Textbeschriftungen zu Balken hinzu
                ax3.bar_label(bars, fmt='%.1f%%', padding=3)

                ax3.set_xlabel('Growth Rate (%)', fontsize=12)
                ax3.set_ylabel('Area', fontsize=12)
                ax3.set_title('Bottom 10 Areas by Population Growth Rate (1996 - 2023)', fontsize=14)
                ax3.grid(axis='x', linestyle='--', alpha=0.5)
                ax3.xaxis.set_major_formatter(mticker.FormatStrFormatter('%.1f%%')) # Formatiert Achse
                plt.tight_layout()
                st.pyplot(fig3)
            else:
                 st.info("No areas with valid growth rate found in the bottom 10.")
          except Exception as e:
              st.error(f"Error creating bottom growth plot: {e}")
     else:
          st.info("Bottom growth area data not available from Analysis page or is empty.")


with tab4:
    st.subheader("Top 10 Cities/Areas by Population (2023)")
    if top_10_cities is not None and not top_10_cities.empty:
         try:
            top_10_cities_sorted = top_10_cities.sort_values('population_2023', ascending=False)

            fig4, ax4 = plt.subplots(figsize=(12, 6))
            colors = plt.cm.viridis(np.linspace(0, 1, len(top_10_cities_sorted)))
            ax4.bar(top_10_cities_sorted['Name'], top_10_cities_sorted['population_2023'], color=colors)
            ax4.set_xlabel('City/Area')
            ax4.set_ylabel('Population in 2023')
            ax4.set_title('Top 10 Cities/Areas by Population in 2023')
            plt.xticks(rotation=45, ha='right')
            ax4.grid(axis='y', linestyle='--', alpha=0.5)
            # Formatiert die Y-Achse für bessere Lesbarkeit
            ax4.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, p: format(int(x), ',')))
            plt.tight_layout()
            st.pyplot(fig4)
         except Exception as e:
              st.error(f"Error creating top cities plot: {e}")
    else:
         st.info("Top 10 cities data not available from Analysis page or is empty.")


with tab5:
    st.subheader("Population Comparison: 1996 vs 2023")
    # Verwendet df_analysis, falls es mit Wachstumsrate gespeichert wurde, andernfalls das Haupt-df ohne letzte Zeile
    df_for_scatter = df_analysis if df_analysis is not None else None
    # Wenn df_analysis nicht vorhanden ist, erstelle es aus dem Haupt-df
    if df_for_scatter is None:
        if not df.empty and 'Name' in df.columns and len(df)>0 and df.iloc[-1]['Name'].lower() == 'miṣr':
             df_for_scatter = df.iloc[:-1].copy()
        else:
             df_for_scatter = df.copy() # Gehe davon aus, dass keine Gesamtzeile vorhanden ist, wenn die letzte nicht 'Miṣr' ist


    if 'population_1996' in df_for_scatter.columns and 'population_2023' in df_for_scatter.columns and not df_for_scatter.empty:
         try:
            fig5, ax5 = plt.subplots(figsize=(8, 6))
            sns.scatterplot(
                data=df_for_scatter, # Verwendet das Analyse-df (ohne Gesamt)
                x='population_1996',
                y='population_2023',
                color='dodgerblue',
                edgecolor='black',
                alpha=0.7, # Transparenz hinzufügen
                ax=ax5
            )
            ax5.set_title('Population in 1996 vs 2023 (Excluding Egypt Total if identified)')
            ax5.set_xlabel('Population 1996')
            ax5.set_ylabel('Population 2023')
            ax5.grid(True, linestyle='--', alpha=0.5)
            # Bestimme Grenzen nach dem Plotten
            xlims = ax5.get_xlim()
            ylims = ax5.get_ylim()
            lims = [min(xlims[0], ylims[0]), max(xlims[1], ylims[1])]
            # Plottet y=x Linie
            ax5.plot(lims, lims, 'r--', alpha=0.75, zorder=0, label='y=x (No Change)')
            ax5.set_xlim(lims)
            ax5.set_ylim(lims)
            ax5.legend()
            # Formatiert Achsen für Lesbarkeit
            ax5.xaxis.set_major_formatter(mticker.FuncFormatter(lambda x, p: format(int(x), ',')))
            ax5.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, p: format(int(x), ',')))
            plt.tight_layout()
            st.pyplot(fig5)
         except Exception as e:
             st.error(f"Error creating scatter plot: {e}")
    elif not df_for_scatter.empty:
        st.info("Population 1996 or 2023 data not available for scatter plot.")
    else:
        st.info("No data available for scatter plot.")