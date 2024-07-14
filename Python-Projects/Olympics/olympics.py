import streamlit as st
import pandas as pd
import plotly.express as px



# Load the data
@st.cache_data
def load_data():
    df_results = pd.read_csv('Olympic_Athlete_Event_Results.csv')
    df_games = pd.read_csv('Olympics_Games.csv')
    df_bio = pd.read_csv('Olympic_Athlete_Bio.csv')
    df_medal = pd.read_csv('Olympic_Games_Medal_Tally.csv')
    
    # Filter for Summer Olympics
    summer_editions = df_games[df_games['edition'].str.contains("Summer", na=False)]['edition_id'].tolist()
    
    # Merge dataframes
    df = pd.merge(df_results, df_games[['edition_id', 'year', 'city']], on='edition_id', how='left')
    df = pd.merge(df, df_bio[['athlete_id', 'name', 'sex', 'country']], on='athlete_id', how='left')
    
    # Filter for Summer Olympics
    df = df[df['edition_id'].isin(summer_editions)]
    df_medal = df_medal[df_medal['edition'].str.contains("Summer", na=False)]
    
    return df, df_medal

df, df_Medal = load_data()

#Image Header

from PIL import Image
image = Image.open('Olympic Rings.png')
st.image(image, width=500)


# Center the header
st.markdown("<h1 style='text-align: left;'>Summer Olympics Dashboard</h1>", unsafe_allow_html=True)

# 1. Where the Olympics has happened
st.subheader('1. Where the Summer Olympics has happened')

# Read the CSV file into a DataFrame
df_Games = pd.read_csv("Olympics_Games.csv")

# Filter for rows where the edition is "Summer"
df_Summer_Games = df_Games[df_Games['edition'].str.contains("Summer")].sort_values(by='year', ascending=False)

# Replace missing values in 'competition_date' for specific 'edition_id' values
df_Summer_Games.loc[df_Summer_Games['edition_id'].isin([50, 51, 52]), 'competition_date'] = "Not Held Due to War"

# Select relevant columns
df_Summer_Games = df_Summer_Games[['edition', 'city', 'year', 'competition_date']]

# Display the DataFrame
st.dataframe(df_Summer_Games, width=1000, height=500, use_container_width=True)

# 2. Male and Female Participation Over Time (Percentage)
st.subheader('2. Male and Female Participation Over Time')

# Group by year and sex, then calculate the percentage
participation_data = df.groupby(['year', 'sex']).size().unstack(fill_value=0)
participation_data_percent = participation_data.div(participation_data.sum(axis=1), axis=0) * 100
participation_data_percent = participation_data_percent.reset_index()

fig = px.area(participation_data_percent, x='year', y=['Female', 'Male'],
              title='Male and Female Participation Over Time (Percentage)',
              labels={'value': 'Percentage of Participants', 'variable': 'Gender'},
              color_discrete_map={'Female': 'rgb(255, 127, 14)', 'Male': 'rgb(31, 119, 180)'},
              )

fig.update_layout(yaxis_range=[0, 100])

st.plotly_chart(fig)

# 3. Country Medal Data
st.subheader('3. Country Medal Data')

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

# Display the DataFrame
st.dataframe(df_Medal_country, width=1000, use_container_width=True)

# 4. Olympic Medal Winners
st.header('4. Olympic Medal Winners')

# Filter for medal winners only
df_medal_winners = df[df['medal'].notna()]

# # Known team sports to filter out
# team_sports = ['Basketball', 'Football', 'Hockey', 'Volleyball', 'Handball', 'Water Polo']

# # Filter out team sports
# df_medal_winners = df_medal_winners[~df_medal_winners['sport'].isin(team_sports)]

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

    df_medal = filtered_df[['year', 'city', 'sport', 'event', 'name', 'sex', 'medal']]

    # Create a custom order for medals
    medal_order = {'Gold': 1, 'Silver': 2, 'Bronze': 3}
    df_medal['medal_order'] = df_medal['medal'].map(medal_order)

    # Sort by year in descending order and then by medal
    df_medal = df_medal.sort_values(by=['year', 'medal_order'], ascending=[False, True])

    # Drop the temporary medal_order column
    df_medal = df_medal.drop(columns=['medal_order'])

    # Remove the row index
    df_medal = df_medal.reset_index(drop=True)

    st.dataframe(df_medal, width=2000)