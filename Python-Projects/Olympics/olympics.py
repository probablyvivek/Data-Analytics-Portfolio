import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from PIL import Image
import ssl
ssl._create_default_https_context = ssl._create_unverified_context


# Set page configuration (must be the first Streamlit command)
st.set_page_config(layout="wide", page_title="Summer Olympics Dashboard")

# URL prefix for GitHub raw content
GITHUB_REPO_URL = "https://raw.githubusercontent.com/probablyvivek/Data-Analytics-Portfolio/main/Python-Projects/Olympics/data/"

# Caching functions for data loading
@st.cache_data(ttl=3600)
def load_csv(file_name):
    try:
        file_url = GITHUB_REPO_URL + file_name
        return pd.read_csv(file_url)
    except Exception as e:
        st.error(f"Error loading data file: {file_name}. Details: {e}")
        return pd.DataFrame()  # Return an empty DataFrame

@st.cache_data(ttl=3600)
def load_and_process_data():
    df_final_results = load_csv('Olympic_Athlete_Event_Results.csv')
    df_games = load_csv('Olympics_Games.csv')
    df_bio = load_csv('Olympic_Athlete_Bio.csv')
    df_medal = load_csv('Olympic_Games_Medal_Tally.csv')
    
    if df_final_results.empty or df_games.empty or df_bio.empty or df_medal.empty:
        st.error("One or more required data files could not be loaded. Please check the file paths and try again.")
        return pd.DataFrame(), pd.DataFrame()
    
    df = pd.merge(df_final_results, df_bio, on='athlete_id', how='left')
    df = pd.merge(df, df_games, on='edition_id', how='left')
    
    columns_to_drop = [col for col in df.columns if col.endswith('_y')]
    columns_to_rename = {col: col[:-2] for col in df.columns if col.endswith('_x')}
    df = df.drop(columns=columns_to_drop).rename(columns=columns_to_rename)
    
    summer_editions = df_games[df_games['edition'].str.contains("Summer", na=False)]['edition_id'].tolist()
    df = df[(df['edition_id'].isin(summer_editions)) & (df['isTeamSport'] == False)]
    df_medal = df_medal[df_medal['edition'].str.contains("Summer", na=False)]
    
    return df, df_medal

@st.cache_data(ttl=3600)
def load_host_cities_data():
    df_Games = load_csv("Olympics_Games.csv")
    if df_Games.empty:
        st.error("Unable to load Olympics_Games.csv. Please check if the file exists and is in the correct location.")
        return pd.DataFrame()
    
    df_Summer_Games = df_Games[df_Games['edition'].str.contains("Summer", na=False)].sort_values(by='year', ascending=False)
    df_Summer_Games.loc[df_Summer_Games['edition_id'].isin([50, 51, 52]), 'competition_date'] = "Not Held Due to War"
    df_Summer_Games = df_Summer_Games[['edition', 'city', 'year', 'competition_date', 'country_noc']]
    df_Summer_Games = df_Summer_Games.rename(columns={'edition': 'Edition', 'city': 'City', 'year': 'Year', 'competition_date': 'Competition Date', 'country_noc': 'Country'})
    return df_Summer_Games

@st.cache_data(ttl=3600)
def calculate_participation_data(df):
    if df.empty:
        st.error("No data available for participation analysis.")
        return pd.DataFrame()
    participation_data = df.groupby(['year', 'sex']).size().unstack(fill_value=0)
    participation_data_percent = participation_data.div(participation_data.sum(axis=1), axis=0) * 100
    return participation_data_percent.reset_index()

@st.cache_data(ttl=3600)
def prepare_medal_data(df_Medal, selected_year):
    if df_Medal.empty:
        st.error("No medal data available for analysis.")
        return pd.DataFrame()
    if selected_year == 'Overall':
        df_Medal_country = df_Medal.groupby('country').agg({
            'gold': 'sum', 'silver': 'sum', 'bronze': 'sum', 'total': 'sum'
        }).sort_values(by='total', ascending=False).reset_index()
    else:
        df_Medal_country = df_Medal[df_Medal['year'] == selected_year].groupby('country').agg({
            'gold': 'sum', 'silver': 'sum', 'bronze': 'sum', 'total': 'sum'
        }).sort_values(by='total', ascending=False).reset_index()
    
    df_Medal_country['Rank'] = df_Medal_country['total'].rank(ascending=False, method='first').astype(int)
    df_Medal_country = df_Medal_country[['Rank', 'country', 'gold', 'silver', 'bronze', 'total']]
    df_Medal_country = df_Medal_country.rename(columns={'country': 'Country', 'gold': 'Gold', 'silver': 'Silver', 'bronze': 'Bronze', 'total': 'Total'})
    return df_Medal_country.set_index('Rank')

@st.cache_data(ttl=3600)
def preprocess_medal_winners(df):
    if df.empty:
        st.error("No data available for medal winners analysis.")
        return pd.DataFrame()
    df_medal_winners = df[df['medal'].notna()].copy()
    df_medal_winners['country'] = df_medal_winners['country'].astype('category')
    df_medal_winners['name'] = df_medal_winners['name'].astype('category')
    return df_medal_winners

# Sidebar for navigation
st.sidebar.title("Navigation")
page = st.sidebar.radio("Go to", ["Home", "Host Cities", "Participation Trends", "Medal Analysis", "Champions Showcase"])

if page == "Home":
    st.markdown("<h1 style='text-align: center;'>🏅 Summer Olympics Dashboard</h1>", unsafe_allow_html=True)
    
    st.markdown("Created by [Vivek Tiwari](https://github.com/probablyvivek)")
    st.write("""
    Welcome to the Summer Olympics Dashboard! This interactive tool allows you to explore various aspects of the Olympic Games, including:
    
    - Host Cities
    - Athlete Participation Trends
    - Medal Analysis
    - Olympic Champions
    
    Use the sidebar to navigate between different sections of the dashboard.
    """)

elif page == "Host Cities":
    st.header('Summer Olympics Host Cities')
    df_Summer_Games = load_host_cities_data()
    
    if not df_Summer_Games.empty:
        fig_map = px.scatter_geo(df_Summer_Games, 
                                 locations="Country", 
                                 locationmode="ISO-3",
                                 hover_name="City", 
                                 size=[15]*len(df_Summer_Games),
                                 projection="natural earth",
                                 color="Year",
                                 color_continuous_scale=px.colors.sequential.Viridis,
                                 hover_data=["Year", "Competition Date"])
        fig_map.update_layout(title='Summer Olympics Host Cities')
        st.plotly_chart(fig_map, use_container_width=True)
        
        st.dataframe(df_Summer_Games.set_index('Year'), width=1000, height=500, use_container_width=True)
    else:
        st.warning("No data available for Host Cities. Please check the data source.")

elif page == "Participation Trends":
    st.header('Athlete Participation Trends')
    df, _ = load_and_process_data()
    participation_data_percent = calculate_participation_data(df)
    
    if not participation_data_percent.empty:
        fig = px.area(participation_data_percent, x='year', y=['Female', 'Male'],
                      title='Male and Female Participation Over Time (Percentage)',
                      labels={'value': 'Percentage of Participants', 'variable': 'Gender'},
                      color_discrete_map={'Female': 'rgb(255, 99, 71)', 'Male': 'rgb(100, 49, 237)'})
        fig.update_layout(yaxis_range=[0, 100])
        st.plotly_chart(fig)
        
    else:
        st.warning("No data available for Participation Trends. Please check the data source.")

elif page == "Champions Showcase":
    st.header('Olympic Champions Showcase')
    df, _ = load_and_process_data()
    df_medal_winners = preprocess_medal_winners(df)
    
    if not df_medal_winners.empty:
        if 'filters' not in st.session_state:
            st.session_state.filters = {key: None for key in ['year', 'country', 'sport', 'name']}
        
        def get_filtered_options(df, column, filters):
            filtered_df = df
            for key, value in filters.items():
                if value and key != column and value != 'All':
                    filtered_df = filtered_df[filtered_df[key].astype(str) == str(value)]
            return sorted(filtered_df[column].unique())
    
        
        col1, col2, col3, col4 = st.columns(4)
        for col, key in zip([col1, col2, col3, col4], ['year', 'country', 'sport', 'name']):
            with col:
                options = get_filtered_options(df_medal_winners, key, st.session_state.filters)
                options = ['All'] + [str(option) for option in options]  # Convert all options to strings
                if key == 'year':
                    options = sorted(options, reverse=True)
                else:
                    options = sorted(options)
                
                # Use the current filter value as the default, or 'All' if not set
                current_value = st.session_state.filters.get(key, 'All')
                default_index = options.index(current_value) if current_value in options else options.index('All')
                
                selected = st.selectbox(f'Select {key.capitalize()}', options=options,
                                        index=default_index, key=f'{key}_selectbox')
                st.session_state.filters[key] = None if selected == 'All' else selected
        
         # Add a reset button
        if st.button('Reset Filters'):
            for key in st.session_state.filters:
                st.session_state.filters[key] = None
            st.experimental_rerun()
        
        filtered_df = df_medal_winners
        filters_applied = False
        for column, selected_value in st.session_state.filters.items():
            if selected_value and selected_value != 'All':
                filtered_df = filtered_df[filtered_df[column].astype(str) == str(selected_value)]
                filters_applied = True
        
        if filtered_df.empty:
            st.write('No data available for the selected filters.')
        else:
            st.subheader('Medal Winners')
            df_medal = filtered_df[['year', 'city', 'sport', 'event', 'name', 'sex', 'medal', 'country']]
            medal_order = {'Gold': 1, 'Silver': 2, 'Bronze': 3}
            df_medal['medal_order'] = df_medal['medal'].map(medal_order)
            df_medal = df_medal.sort_values(by=['year', 'medal_order'], ascending=[False, True])
            df_medal = df_medal.drop(columns=['medal_order']).reset_index(drop=True)
            df_medal.columns = df_medal.columns.str.capitalize()
            st.dataframe(df_medal.set_index('Year'), width=2000)

            # Calculate top athletes by medal count using the filtered DataFrame
            top_athletes = filtered_df.groupby('name')['medal'].value_counts().unstack(fill_value=0)

            # Ensure all columns exist in the DataFrame
            for medal_type in ['Gold', 'Silver', 'Bronze']:
                if medal_type not in top_athletes:
                    top_athletes[medal_type] = 0

            top_athletes['Total'] = top_athletes.sum(axis=1)

            # Remove athletes with no medals
            top_athletes = top_athletes[top_athletes['Total'] > 0]

            # Sort athletes by Total medals first, then by Gold, Silver, Bronze for tiebreakers
            top_athletes = top_athletes.sort_values(
                by=['Total', 'Gold', 'Silver', 'Bronze'], 
                ascending=[False, False, False, False]
            )

            # Always show top 10 if there are at least 10 athletes
            top_athletes = top_athletes.head(10)

            # Get the number of athletes to display
            num_athletes = len(top_athletes)

            # Create the bar chart
            fig_top_athletes = go.Figure()
            for medal, color in zip(['Gold', 'Silver', 'Bronze'], ['#FFD700', '#C0C0C0', '#CD7F32']):
                fig_top_athletes.add_trace(go.Bar(y=top_athletes.index[::-1], x=top_athletes[medal][::-1], name=medal, orientation='h', marker_color=color))

            # Update y-axis to show the correct order of athletes
            fig_top_athletes.update_layout(
                yaxis=dict(
                    tickmode='array',
                    tickvals=list(range(num_athletes)),
                    ticktext=top_athletes.index[::-1].tolist()
                )
            )

            # Determine the title based on filters
            if filters_applied:
                if st.session_state.filters['country'] and st.session_state.filters['country'] != 'All':
                    country_name = st.session_state.filters['country']
                    title = f'Top {num_athletes} Medal Winners from {country_name}'
                elif st.session_state.filters['year'] and st.session_state.filters['year'] != 'All':
                    year = st.session_state.filters['year']
                    title = f'Top {num_athletes} Medal Winners in {year}'
                elif st.session_state.filters['sport'] and st.session_state.filters['sport'] != 'All':
                    sport = st.session_state.filters['sport']
                    title = f'Top {num_athletes} Medal Winners in {sport}'
                elif st.session_state.filters['name'] and st.session_state.filters['name'] != 'All':
                    name = st.session_state.filters['name']
                    title = f'Medal Wins for {name}'
                else:
                    title = f'Top {num_athletes} Medal Winners for Selected Filters'
            else:
                title = f'Top {num_athletes} Olympic Medal Winners of All Time'

            # Update layout
            fig_top_athletes.update_layout(
                title=title, 
                xaxis_title='Number of Medals', 
                yaxis_title='Athlete',
                barmode='stack', 
                height=max(300, 50 * num_athletes),  # Adjust height based on number of athletes
                width=600, 
                margin=dict(l=50, r=50, t=50, b=50),
                legend_title_text='Medal Type'
            )

            # Display the chart in Streamlit
            st.plotly_chart(fig_top_athletes, use_container_width=True)
    else:
        st.warning("No data available for Champions Showcase. Please check the data source.")