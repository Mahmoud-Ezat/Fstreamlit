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
# Holt Analyseergebnisse, falls gespeichert
population_density = st.session_state.get('population_density', None)
pop_cols_for_density = st.session_state.get('pop_cols_for_density', None)
top_10_cities = st.session_state.get('top_10_cities', None)
top_growth_areas = st.session_state.get('top_growth_areas', None)
low_growth_areas = st.session_state.get('low_growth_areas', None)
df_analysis = st.session_state.get('df_analysis_with_growth', None)

# --- Definiere erwartete Spaltennamen (Kleinbuchstaben) ---
NAME_COL = 'name'
STATUS_COL = 'status'
POP_1996_COL = 'population_1996'
POP_2023_COL = 'population_2023'
GROWTH_RATE_COL = 'growth_rate'

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
            years_str = [col.split('_')[-1] for col in pop_cols_for_density]
            years = [int(y) for y in years_str if y.isdigit()]
            if len(years) == len(population_density.values):
                population_density_values = population_density.values

                fig1, ax1 = plt.subplots(figsize=(7, 5))
                ax1.plot(years, population_density_values, marker='o', color='b', linestyle='-', linewidth=2, markersize=8)
                ax1.set_xlabel('Year')
                ax1.set_ylabel("Population Density (persons/km²)")
                ax1.set_title("Population Density in Egypt Over the Years")
                ax1.grid(True)
                ax1.set_xticks(years)
                ax1.yaxis.set_major_formatter(mticker.FormatStrFormatter('%d'))
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
            top_growth_sorted = top_growth_areas.dropna(subset=[GROWTH_RATE_COL]).sort_values(GROWTH_RATE_COL, ascending=True)

            # *** KORREKTUR: Tippfehler und Spaltenname ***
            if not top_growth_sorted.empty: # Korrigierter Variablenname
                fig2, ax2 = plt.subplots(figsize=(10, 6))
                sns.barplot(y=NAME_COL, x=GROWTH_RATE_COL, data=top_growth_sorted, palette='viridis', ax=ax2, dodge=False) # Verwende NAME_COL
                ax2.set_xlabel('Growth Rate (%)')
                ax2.set_ylabel('Area')
                ax2.set_title('Top 10 Areas by Population Growth Rate (1996 - 2023)')
                ax2.grid(axis='x', linestyle='--', alpha=0.5)
                ax2.xaxis.set_major_formatter(mticker.FormatStrFormatter('%.1f%%'))
                plt.tight_layout()
                st.pyplot(fig2)
            else:
                st.info("No areas with valid growth rate found in the top 10.")
         except KeyError:
             st.error(f"Error creating top growth plot: Could not find required columns ('{NAME_COL}', '{GROWTH_RATE_COL}') in the top growth data.")
         except Exception as e:
             st.error(f"Error creating top growth plot: {e}")
    else:
         st.info("Top growth area data not available from Analysis page or is empty.")


with tab3:
     st.subheader("Bottom 10 Areas by Growth Rate (%)")
     if low_growth_areas is not None and not low_growth_areas.empty:
          try:
            low_growth_plot = low_growth_areas.dropna(subset=[GROWTH_RATE_COL]).sort_values(GROWTH_RATE_COL, ascending=True)

            if not low_growth_plot.empty:
                fig3, ax3 = plt.subplots(figsize=(12, 6))
                # *** KORREKTUR: Spaltenname ***
                bars = ax3.barh(
                    low_growth_plot[NAME_COL], # Verwende NAME_COL
                    low_growth_plot[GROWTH_RATE_COL], # Verwende GROWTH_RATE_COL
                    color='salmon'
                )
                ax3.bar_label(bars, fmt='%.1f%%', padding=3)

                ax3.set_xlabel('Growth Rate (%)', fontsize=12)
                ax3.set_ylabel('Area', fontsize=12)
                ax3.set_title('Bottom 10 Areas by Population Growth Rate (1996 - 2023)', fontsize=14)
                ax3.grid(axis='x', linestyle='--', alpha=0.5)
                ax3.xaxis.set_major_formatter(mticker.FormatStrFormatter('%.1f%%'))
                plt.tight_layout()
                st.pyplot(fig3)
            else:
                 st.info("No areas with valid growth rate found in the bottom 10.")
          except KeyError:
              st.error(f"Error creating bottom growth plot: Could not find required columns ('{NAME_COL}', '{GROWTH_RATE_COL}') in the bottom growth data.")
          except Exception as e:
              st.error(f"Error creating bottom growth plot: {e}")
     else:
          st.info("Bottom growth area data not available from Analysis page or is empty.")


with tab4:
    st.subheader("Top 10 Cities/Areas by Population (2023)")
    if top_10_cities is not None and not top_10_cities.empty:
         try:
            top_10_cities_sorted = top_10_cities.sort_values(POP_2023_COL, ascending=False) # Verwende POP_2023_COL

            fig4, ax4 = plt.subplots(figsize=(12, 6))
            colors = plt.cm.viridis(np.linspace(0, 1, len(top_10_cities_sorted)))
             # *** KORREKTUR: Spaltenname ***
            ax4.bar(top_10_cities_sorted[NAME_COL], top_10_cities_sorted[POP_2023_COL], color=colors) # Verwende NAME_COL und POP_2023_COL
            ax4.set_xlabel('City/Area')
            ax4.set_ylabel('Population in 2023')
            ax4.set_title('Top 10 Cities/Areas by Population in 2023')
            plt.xticks(rotation=45, ha='right')
            ax4.grid(axis='y', linestyle='--', alpha=0.5)
            ax4.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, p: format(int(x), ',')))
            plt.tight_layout()
            st.pyplot(fig4)
         except KeyError:
             st.error(f"Error creating top cities plot: Could not find required columns ('{NAME_COL}', '{POP_2023_COL}') in the top cities data.")
         except Exception as e:
              st.error(f"Error creating top cities plot: {e}")
    else:
         st.info("Top 10 cities data not available from Analysis page or is empty.")


with tab5:
    st.subheader("Population Comparison: 1996 vs 2023")
    df_for_scatter = df_analysis if df_analysis is not None else None
    if df_for_scatter is None:
        # *** VERWENDE KLEINSCHREIBUNG für 'name' ***
        if not df.empty and NAME_COL in df.columns and len(df)>0 and df.iloc[-1][NAME_COL].lower() == 'miṣr':
             df_for_scatter = df.iloc[:-1].copy()
        else:
             df_for_scatter = df.copy()

    # *** VERWENDE KLEINSCHREIBUNG für Spaltennamen ***
    if POP_1996_COL in df_for_scatter.columns and POP_2023_COL in df_for_scatter.columns and not df_for_scatter.empty:
         try:
            fig5, ax5 = plt.subplots(figsize=(8, 6))
            sns.scatterplot(
                data=df_for_scatter,
                x=POP_1996_COL, # Verwende POP_1996_COL
                y=POP_2023_COL, # Verwende POP_2023_COL
                color='dodgerblue',
                edgecolor='black',
                alpha=0.7,
                ax=ax5
            )
            ax5.set_title('Population in 1996 vs 2023 (Excluding Egypt Total if identified)')
            ax5.set_xlabel('Population 1996')
            ax5.set_ylabel('Population 2023')
            ax5.grid(True, linestyle='--', alpha=0.5)
            xlims = ax5.get_xlim()
            ylims = ax5.get_ylim()
            lims = [min(xlims[0], ylims[0]), max(xlims[1], ylims[1])]
            ax5.plot(lims, lims, 'r--', alpha=0.75, zorder=0, label='y=x (No Change)')
            ax5.set_xlim(lims)
            ax5.set_ylim(lims)
            ax5.legend()
            ax5.xaxis.set_major_formatter(mticker.FuncFormatter(lambda x, p: format(int(x), ',')))
            ax5.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, p: format(int(x), ',')))
            plt.tight_layout()
            st.pyplot(fig5)
         except KeyError:
              st.error(f"Error creating scatter plot: Could not find required columns ('{POP_1996_COL}', '{POP_2023_COL}') in the data.")
         except Exception as e:
             st.error(f"Error creating scatter plot: {e}")
    elif not df_for_scatter.empty:
        st.info(f"Columns '{POP_1996_COL}' or '{POP_2023_COL}' not available for scatter plot.")
    else:
        st.info("No data available for scatter plot.")
