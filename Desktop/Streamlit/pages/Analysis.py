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
    st.stop() # Stop execution if no data

df = st.session_state['cleaned_df']

# --- Perform Analysis ---
st.header("Analysis Results")

# Basic Statistics
with st.expander("Basic Statistics (Numeric Columns)"):
    try:
        # Select only numeric columns for describe
        numeric_cols = df.select_dtypes(include=np.number).columns
        if not numeric_cols.empty:
            st.dataframe(df[numeric_cols].describe().applymap('{:.0f}'.format)) # Format to integer
        else:
            st.info("No numeric columns found for statistics.")
    except Exception as e:
        st.error(f"Error calculating basic statistics: {e}")


# Total Population and Density Calculation (Repeated here for independence)
total_population_misr = None
population_density = None
pop_cols = [col for col in df.columns if col.startswith('population_')] # Get pop columns again

try:
    # Ensure DataFrame is not empty and 'Name' exists
    if not df.empty and 'Name' in df.columns and pop_cols:
        # Check the last row more carefully
        if len(df) > 0 and df.iloc[-1]['Name'].lower() == 'miṣr':
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

            # Store for potential use in viz page
            st.session_state['population_density'] = population_density
            st.session_state['pop_cols_for_density'] = pop_cols

        else:
            # *** ÜBERSETZUNG ***
            st.warning("Could not identify the 'Miṣr' (Egypt total) row for density calculation.")
            if 'population_density' in st.session_state: del st.session_state['population_density']
            if 'pop_cols_for_density' in st.session_state: del st.session_state['pop_cols_for_density']

    else:
        # Case when DataFrame is empty or 'Name'/'pop_cols' are missing
         # *** ÜBERSETZUNG ***
         st.warning("DataFrame is empty or required columns ('Name', 'population_*') are missing for density calculation.")
         if 'population_density' in st.session_state: del st.session_state['population_density']
         if 'pop_cols_for_density' in st.session_state: del st.session_state['pop_cols_for_density']


except IndexError:
     # *** ÜBERSETZUNG ***
     st.warning("IndexError while looking for the 'Miṣr' row (DataFrame might be empty).")
     if 'population_density' in st.session_state: del st.session_state['population_density']
     if 'pop_cols_for_density' in st.session_state: del st.session_state['pop_cols_for_density']
except Exception as e:
    st.error(f"Error calculating total population/density: {e}")
    if 'population_density' in st.session_state: del st.session_state['population_density']
    if 'pop_cols_for_density' in st.session_state: del st.session_state['pop_cols_for_density']


# Prepare data for city/area analysis (exclude total row if found)
df_analysis = df.copy()
# Check if total_population_misr was calculated (meaning 'Miṣr' row was found)
if total_population_misr is not None and len(df) > 1: # Ensure there's more than just the total row
     df_analysis = df.iloc[:-1].copy()
elif len(df)>0 and 'Name' in df.columns and df.iloc[-1]['Name'].lower() != 'miṣr':
     # If last row is not 'Miṣr', assume no total row present
     df_analysis = df.copy()
elif len(df) <= 1 and total_population_misr is not None:
     st.warning("DataFrame only contains the total row, no area analysis possible.")
     df_analysis = pd.DataFrame() # Empty DataFrame for the rest

# Top 10 Cities by Population 2023
if 'population_2023' in df_analysis.columns and not df_analysis.empty:
     st.subheader("Top 10 Cities/Areas by Population (2023)")
     try:
        # Ensure 'Name' and 'Status' exist before accessing
        cols_to_display = ['Name', 'population_2023']
        if 'Status' in df_analysis.columns:
            cols_to_display.insert(1, 'Status')

        top_10_cities = df_analysis.nlargest(10, 'population_2023')[cols_to_display]
        st.table(top_10_cities.style.format({'population_2023': '{:,.0f}'}).hide(axis="index"))
        st.session_state['top_10_cities'] = top_10_cities # Store for viz
     except KeyError as e:
        st.error(f"Error accessing columns for Top 10 Cities: {e}. Required: 'Name', 'population_2023'. 'Status' optional.")
        if 'top_10_cities' in st.session_state: del st.session_state['top_10_cities']
     except Exception as e:
         st.error(f"Error finding top 10 cities: {e}")
         if 'top_10_cities' in st.session_state: del st.session_state['top_10_cities']
elif not df_analysis.empty:
     # *** ÜBERSETZUNG ***
     st.warning("Column 'population_2023' not found for Top 10 Cities analysis.")
     if 'top_10_cities' in st.session_state: del st.session_state['top_10_cities']

# Growth Rate Calculation and Analysis
if 'population_1996' in df_analysis.columns and 'population_2023' in df_analysis.columns and not df_analysis.empty:
    st.subheader("Population Growth Rate (1996 - 2023)")
    try:
        pop_1996 = df_analysis['population_1996']
        pop_2023 = df_analysis['population_2023']

        # Calculate growth rate safely
        growth_rate = np.where(
            (pop_1996.notna()) & (pop_1996 != 0),
            ((pop_2023 - pop_1996) / pop_1996) * 100,
            np.nan # Set to NaN if 1996 is 0 or NaN
        )
        df_analysis['growth_rate'] = growth_rate
        df_analysis['growth_rate'] = df_analysis['growth_rate'].replace([np.inf, -np.inf], np.nan) # Replace inf with NaN

        cols_growth_display = ['Name', 'population_1996', 'population_2023', 'growth_rate']
        if 'Status' in df_analysis.columns:
            cols_growth_display.insert(1, 'Status')

        col1_growth, col2_growth = st.columns(2)
        with col1_growth:
             st.write("**Top 10 Areas by Growth Rate:**")
             top_growth_areas = df_analysis.sort_values('growth_rate', ascending=False, na_position='last').head(10)
             st.table(top_growth_areas[cols_growth_display].style.format({
                 'population_1996': '{:,.0f}',
                 'population_2023': '{:,.0f}',
                 'growth_rate': '{:.1f}%'
             }, na_rep='N/A').hide(axis="index"))
             st.session_state['top_growth_areas'] = top_growth_areas # Store for viz

        with col2_growth:
             st.write("**Bottom 10 Areas by Growth Rate:**")
             low_growth_areas = df_analysis.sort_values('growth_rate', ascending=True, na_position='last').head(10)
             st.table(low_growth_areas[cols_growth_display].style.format({
                  'population_1996': '{:,.0f}',
                  'population_2023': '{:,.0f}',
                  'growth_rate': '{:.1f}%'
             }, na_rep='N/A').hide(axis="index"))
             st.session_state['low_growth_areas'] = low_growth_areas # Store for viz

        st.session_state['df_analysis_with_growth'] = df_analysis

    except Exception as e:
        st.error(f"Error calculating growth rates: {e}")
        if 'top_growth_areas' in st.session_state: del st.session_state['top_growth_areas']
        if 'low_growth_areas' in st.session_state: del st.session_state['low_growth_areas']
        if 'df_analysis_with_growth' in st.session_state: del st.session_state['df_analysis_with_growth']

elif not df_analysis.empty:
    # *** ÜBERSETZUNG ***
    st.warning("Columns 'population_1996' or 'population_2023' not found for growth rate analysis.")
    if 'top_growth_areas' in st.session_state: del st.session_state['top_growth_areas']
    if 'low_growth_areas' in st.session_state: del st.session_state['low_growth_areas']
    if 'df_analysis_with_growth' in st.session_state: del st.session_state['df_analysis_with_growth']
