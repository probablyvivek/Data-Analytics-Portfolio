import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from PIL import Image

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
    st.markdown("<h1 style='text-align: center;'>Summer Olympics Dashboard</h1>", unsafe_allow_html=True)
    
    try:
        image = Image.open('Olympic Rings.png')
        st.image(image, width=500)
    except FileNotFoundError:
        st.warning("Olympic Rings image not found. Displaying text instead.")
        st.markdown("## 🏅 Olympic Games")
    
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
        
        total_participants = df.groupby('year').size().reset_index(name='Total Participants')
        fig_total = px.line(total_participants, x='year', y='Total Participants',
                            title='Total Olympic Participants Over Time',
                            labels={'year': 'Year', 'Total Participants': 'Number of Athletes'})
        st.plotly_chart(fig_total)
    else:
        st.warning("No data available for Participation Trends. Please check the data source.")

elif page == "Medal Analysis":
    st.header('Olympic Medal Analysis')
    _, df_Medal = load_and_process_data()
    
    if not df_Medal.empty:
        year_options = ['Overall'] + sorted(df_Medal['year'].unique(), reverse=True)
        selected_year_medals = st.selectbox('Select Year for Medal Data', year_options)
        
        df_Medal_country = prepare_medal_data(df_Medal, selected_year_medals)
        st.dataframe(df_Medal_country, width=1000, use_container_width=True)
        
        top_10_medal_countries = df_Medal_country.head(10)
        fig_medal_tally = go.Figure(data=[
            go.Bar(name='Gold', x=top_10_medal_countries['Country'], y=top_10_medal_countries['Gold'], marker_color='gold'),
            go.Bar(name='Silver', x=top_10_medal_countries['Country'], y=top_10_medal_countries['Silver'], marker_color='silver'),
            go.Bar(name='Bronze', x=top_10_medal_countries['Country'], y=top_10_medal_countries['Bronze'], marker_color='#cd7f32')
        ])
        fig_medal_tally.update_layout(barmode='stack', title=f'Top 10 Countries by Total Medals in {selected_year_medals}', yaxis_title='Number of Medals')
        st.plotly_chart(fig_medal_tally)
    else:
        st.warning("No data available for Medal Analysis. Please check the data source.")

elif page == "Champions Showcase":
    st.header('Olympic Champions Showcase')
    df, _ = load_and_process_data()
    df_medal_winners = preprocess_medal_winners(df)
    
    if not df_medal_winners.empty:
        col1, col2 = st.columns([2, 3])
        
        with col1:
            selected_sport = st.selectbox('Select Sport', sorted(df_medal_winners['sport'].unique()))
            selected_medal = st.radio('Select Medal', ['Gold', 'Silver', 'Bronze'])
            selected_gender = st.radio('Select Gender', ['M', 'F'])
        
        filtered_champions = df_medal_winners[(df_medal_winners['sport'] == selected_sport) & 
                                              (df_medal_winners['medal'] == selected_medal) &
                                              (df_medal_winners['sex'] == selected_gender)]
        
        if not filtered_champions.empty:
            top_athletes = filtered_champions['name'].value_counts().head(10).reset_index()
            top_athletes.columns = ['Athlete', 'Medals Won']
            
            fig_athletes = px.bar(top_athletes, x='Athlete', y='Medals Won', color='Medals Won',
                                  title=f'Top {selected_medal} Medalists in {selected_sport} ({selected_gender})',
                                  color_continuous_scale=px.colors.sequential.Plasma)
            st.plotly_chart(fig_athletes)
        else:
            st.warning("No champions found for the selected criteria. Please adjust your selection.")
    else:
        st.warning("No data available for Champions Showcase. Please check the data source.")
