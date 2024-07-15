import streamlit as st
import pandas as pd
from PIL import Image
import plotly
import plotly.express as px
import plotly.graph_objects as go
import sys
import subprocess
import ssl
import urllib.request

# Disable SSL certificate verification (use with caution)
ssl._create_default_https_context = ssl._create_unverified_context
subprocess.check_call([sys.executable, "-m", "pip", "install", "plotly"])
subprocess.check_call([sys.executable, "-m", "pip", "install", "plotly-express"])

# Set page configuration (must be the first Streamlit command)
st.set_page_config(layout="wide", page_title="Summer Olympics Dashboard")

# Load the data
def load_data():
    df_final_results = pd.read_csv("https://raw.githubusercontent.com/probablyvivek/Data-Analytics-Portfolio/main/Python-Projects/Olympics/Olympic_Athlete_Event_Results.csv")
    df_games = pd.read_csv('Olympics_Games.csv')
    df_bio = pd.read_csv('Olympic_Athlete_Bio.csv')
    df_medal = pd.read_csv('Olympic_Games_Medal_Tally.csv')
    
    # Merge dataframes
    df = pd.merge(df_final_results, df_bio, on='athlete_id', how='left')
    df = pd.merge(df, df_games, on='edition_id', how='left')
    
    # Handle duplicate columns
    columns = df.columns
    columns_to_drop = [col for col in columns if col.endswith('_y')]
    columns_to_rename = {col: col[:-2] for col in columns if col.endswith('_x')}

    # Drop columns with '_y' suffix
    df = df.drop(columns=columns_to_drop)

    # Rename columns with '_x' suffix to remove the suffix
    df = df.rename(columns=columns_to_rename)
    
    # Filter for Summer Olympics
    summer_editions = df_games[df_games['edition'].str.contains("Summer", na=False)]['edition_id'].tolist()
    df = df[df['edition_id'].isin(summer_editions)]
    df_medal = df_medal[df_medal['edition'].str.contains("Summer", na=False)]
    
    # Filter out team sports
    df = df[df['isTeamSport'] == False]
    
    return df, df_medal

df, df_Medal = load_data()

# Sidebar for navigation
st.sidebar.title("Navigation")
page = st.sidebar.radio("Go to", ["Home", "Host Cities", "Participation Trends", "Medal Analysis", "Champions Showcase"])

if page == "Home":
    # Image Header
    image = Image.open('Olympic Rings.png')
    st.image(image, width=500)

    # Center the header
    st.markdown("<h1 style='text-align: center;'>Summer Olympics Dashboard</h1>", unsafe_allow_html=True)

    #Created by
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

    # Read the CSV file into a DataFrame
    df_Games = pd.read_csv("Olympics_Games.csv")

    # Filter for rows where the edition is "Summer"
    df_Summer_Games = df_Games[df_Games['edition'].str.contains("Summer")].sort_values(by='year', ascending=False)

    # Replace missing values in 'competition_date' for specific 'edition_id' values
    df_Summer_Games.loc[df_Summer_Games['edition_id'].isin([50, 51, 52]), 'competition_date'] = "Not Held Due to War"

    # Select relevant columns
    df_Summer_Games = df_Summer_Games[['edition', 'city', 'year', 'competition_date', 'country_noc']]

    # Rename the columns
    df_Summer_Games = df_Summer_Games.rename(columns={'edition': 'Edition', 'city': 'City', 'year': 'Year', 'competition_date': 'Competition Date', 'country_noc': 'Country'})

    # Create a map of host cities
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

    #set index to year
    df_Summer_Games = df_Summer_Games.set_index('Year')

    # Display the DataFrame
    st.dataframe(df_Summer_Games, width=1000, height=500, use_container_width=True)

elif page == "Participation Trends":
    st.header('Athlete Participation Trends')

    # Group by year and sex, then calculate the percentage
    participation_data = df.groupby(['year', 'sex']).size().unstack(fill_value=0)
    participation_data_percent = participation_data.div(participation_data.sum(axis=1), axis=0) * 100
    participation_data_percent = participation_data_percent.reset_index()

    fig = px.area(participation_data_percent, x='year', y=['Female', 'Male'],
                  title='Male and Female Participation Over Time (Percentage)',
                  labels={'value': 'Percentage of Participants', 'variable': 'Gender'},
                  color_discrete_map={'Female': 'rgb(255, 99, 71)', 'Male': 'rgb(100, 49, 237)'},
                  )

    fig.update_layout(yaxis_range=[0, 100])

    st.plotly_chart(fig)

    # New chart: Total participants over time
    total_participants = df.groupby('year').size().reset_index(name='Total Participants')
    fig_total = px.line(total_participants, x='year', y='Total Participants',
                        title='Total Olympic Participants Over Time',
                        labels={'year': 'Year', 'Total Participants': 'Number of Athletes'})
    st.plotly_chart(fig_total)

elif page == "Medal Analysis":
    st.header('Olympic Medal Analysis')

    # Year selection for medal data
    year_options = ['Overall'] + sorted(df_Medal['year'].unique(), reverse=True)
    selected_year_medals = st.selectbox('Select Year for Medal Data', year_options)

    if selected_year_medals == 'Overall':
        # Group by 'country' and sum the medals
        df_Medal_country = df_Medal.groupby('country').agg({
            'gold': 'sum',
            'silver': 'sum',
            'bronze': 'sum',
            'total': 'sum'
        }).sort_values(by='total', ascending=False).reset_index()
    else:
        # Filter for the selected year and group by country
        df_Medal_country = df_Medal[df_Medal['year'] == selected_year_medals].groupby('country').agg({
            'gold': 'sum',
            'silver': 'sum',
            'bronze': 'sum',
            'total': 'sum'
        }).sort_values(by='total', ascending=False).reset_index()

    # Add rank column based on the total medals
    df_Medal_country['Rank'] = df_Medal_country['total'].rank(ascending=False, method='first').astype(int)

    # Reorder columns to include Rank and reset the index
    df_Medal_country = df_Medal_country[['Rank', 'country', 'gold', 'silver', 'bronze', 'total']]

    #Rename columns
    df_Medal_country = df_Medal_country.rename(columns={'country': 'Country', 'gold': 'Gold', 'silver': 'Silver', 'bronze': 'Bronze', 'total': 'Total'})

    df_Medal_country = df_Medal_country.set_index('Rank')

    # Display the DataFrame
    st.dataframe(df_Medal_country, width=1000, use_container_width=True)

    # New visualization: Top 10 countries medal distribution
    top_10 = df_Medal_country.head(10).reset_index()

    fig_medals = go.Figure()

    # Add bars for each medal type
    for medal, color in zip(['Gold', 'Silver', 'Bronze'], ['#FFD700', '#C0C0C0', '#CD7F32']):
        fig_medals.add_trace(go.Bar(
            y=top_10['Country'],
            x=top_10[medal],
            name=medal,
            orientation='h',
            marker_color=color
        ))

    # Update the layout
    fig_medals.update_layout(
        title=f'Top 10 Countries Medal Distribution {"Overall" if selected_year_medals == "Overall" else f"in {selected_year_medals}"}',
        xaxis_title='Number of Medals',
        yaxis_title='Country',
        barmode='stack',
        height=400,
        width=600,
        margin=dict(l=50, r=50, t=50, b=50),
        legend_title_text='Medal Type',
        yaxis={'categoryorder':'total ascending'}
    )

    # Display the chart
    st.plotly_chart(fig_medals, use_container_width=True)

elif page == "Champions Showcase":
    st.header('Olympic Champions Showcase')

    # Filter for medal winners only
    df_medal_winners = df[df['medal'].notna()]

    # Ensure 'country' and 'name' columns are of type str
    df_medal_winners['country'] = df_medal_winners['country'].astype(str)
    df_medal_winners['name'] = df_medal_winners['name'].astype(str).replace('nan', '')

    # Function to get filtered options
    def get_filtered_options(df, column, filters):
        filtered_df = df.copy()
        for key, value in filters.items():
            if value and key != column:
                filtered_df = filtered_df[filtered_df[key].isin(value)]
        return sorted(filtered_df[column].unique())

    # Initialize session state for filters if not already present
    if 'filters' not in st.session_state:
        st.session_state.filters = {
            'year': [],
            'country': [],
            'sport': [],
            'name': []
        }

    # Create 4 columns for filters
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        year_options = get_filtered_options(df_medal_winners, 'year', st.session_state.filters)
        selected_years = st.multiselect('Select Year(s)', 
                                        options=sorted(year_options, reverse=True),
                                        default=st.session_state.filters['year'],
                                        key='year_multiselect')
        st.session_state.filters['year'] = selected_years

    with col2:
        country_options = get_filtered_options(df_medal_winners, 'country', st.session_state.filters)
        selected_countries = st.multiselect('Select Country(s)', 
                                            options=sorted(country_options),
                                            default=st.session_state.filters['country'],
                                            key='country_multiselect')
        st.session_state.filters['country'] = selected_countries

    with col3:
        sport_options = get_filtered_options(df_medal_winners, 'sport', st.session_state.filters)
        selected_sports = st.multiselect('Select Sport(s)', 
                                         options=sorted(sport_options),
                                         default=st.session_state.filters['sport'],
                                         key='sport_multiselect')
        st.session_state.filters['sport'] = selected_sports

    with col4:
        athlete_options = get_filtered_options(df_medal_winners, 'name', st.session_state.filters)
        selected_athletes = st.multiselect('Select Athlete(s)', 
                                           options=sorted(athlete_options),
                                           default=st.session_state.filters['name'],
                                           key='athlete_multiselect')
        st.session_state.filters['name'] = selected_athletes

    # Filter data based on selections
    filtered_df = df_medal_winners.copy()

    for column, selected_values in st.session_state.filters.items():
        if selected_values:
            filtered_df = filtered_df[filtered_df[column].isin(selected_values)]

    # Display medal winners if filtered_df is not empty
    if filtered_df.empty:
        st.write('No data available for the selected filters.')
    else:
        st.subheader('Medal Winners')

        df_medal = filtered_df[['year', 'city', 'sport', 'event', 'name', 'sex', 'medal', 'country']]

        # Create a custom order for medals
        medal_order = {'Gold': 1, 'Silver': 2, 'Bronze': 3}
        df_medal['medal_order'] = df_medal['medal'].map(medal_order)

        # Sort by year in descending order and then by medal
        df_medal = df_medal.sort_values(by=['year', 'medal_order'], ascending=[False, True])

        # Drop the temporary medal_order column
        df_medal = df_medal.drop(columns=['medal_order'])

        # Remove the row index
        df_medal = df_medal.reset_index(drop=True)

        df_medal = df_medal.rename(columns={'year': 'Year', 'city': 'City', 'sport': 'Sport', 'event': 'Event', 'name': 'Name', 'sex': 'Sex', 'medal': 'Medal', 'country': 'Country'})

        #set index to year
        df_medal = df_medal.set_index('Year')

        st.dataframe(df_medal, width=2000)

        # New visualization: Top athletes by medal count
        top_athletes = df_medal_winners.groupby('name')['medal'].value_counts().unstack(fill_value=0)
        top_athletes['Total'] = top_athletes.sum(axis=1)
        top_athletes = top_athletes.sort_values('Total', ascending=False).head(10)

        # Create the stacked bar chart
        fig_top_athletes = go.Figure()

        # Add bars for each medal type
        for medal, color in zip(['Gold', 'Silver', 'Bronze'], ['#FFD700', '#C0C0C0', '#CD7F32']):
            fig_top_athletes.add_trace(go.Bar(
                y=top_athletes.index,
                x=top_athletes[medal],
                name=medal,
                orientation='h',
                marker_color=color
            ))

        # Update the layout
        fig_top_athletes.update_layout(
            title='Top 10 Athletes by Medal Count',
            xaxis_title='Number of Medals',
            yaxis_title='Athlete',
            barmode='stack',
            height=400,
            width=600,
            margin=dict(l=50, r=50, t=50, b=50),
            legend_title_text='Medal Type',
            yaxis={'categoryorder':'total ascending'}
        )

        # Display the chart
        st.plotly_chart(fig_top_athletes, use_container_width=True)

        # Medal distribution by country
        medal_by_country = df_medal.groupby('Country')['Medal'].value_counts().unstack(fill_value=0)
        medal_by_country['Total'] = medal_by_country.sum(axis=1)
        medal_by_country = medal_by_country.sort_values('Total', ascending=False).head(10)
