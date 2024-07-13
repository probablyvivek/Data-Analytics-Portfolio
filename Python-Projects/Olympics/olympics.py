import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import numpy as np

# Load data
@st.cache_data
def load_data():
    df = pd.read_csv('Olympic_Athlete_Event_Results.csv')
    df_bio = pd.read_csv('Olympic_Athlete_Bio.csv')
    df_games = pd.read_csv('Olympics_Games.csv')
    
    # Merge dataframes
    df = pd.merge(df, df_bio, on='athlete_id', how='left')
    df = pd.merge(df, df_games, on='edition_id', how='left')
    
    # Clean data
    if 'year' not in df.columns:
        if 'edition' in df.columns:
            df['year'] = df['edition'].str.extract(r'(\d{4})')
        elif 'edition.1' in df.columns:
            df['year'] = df['edition.1'].str.extract(r'(\d{4})')
    
    df['country'] = df['country'].str.strip()
    
    # Filter for Summer Olympics
    df = df[df['year'].notna()]
    df['year'] = df['year'].astype(int)
    df = df[df['year'] % 4 == 0]  # Summer Olympics years
    df = df.fillna('-')
    
    return df

def display_medal_winners(df, title):
    st.subheader(title)
    if not df.empty:
        st.write(df[['year', 'city', 'sport', 'event', 'name', 'sex', 'medal', 'country']])
    else:
        st.write("No medals in this category.")

def plot_gender_participation(df, country_selection, medal_type, year_range=None):
    st.subheader("Gender Participation Over the Years")
    
    # Filter data based on selection and medal type
    if country_selection == "India":
        df_filtered = df[df['country'] == 'India']
    else:
        df_filtered = df
    
    if medal_type == "Individual":
        df_filtered = df_filtered[df_filtered['isTeamSport'] == False]
    else:  # Team
        df_filtered = df_filtered[df_filtered['isTeamSport'] == True]
    
    # Apply year filter if specified
    if year_range:
        start_year, end_year = year_range
        df_filtered = df_filtered[(df_filtered['year'] >= start_year) & (df_filtered['year'] <= end_year)]
    
    # Calculate gender participation
    participation = df_filtered.groupby('year').agg(
        total_count=('athlete_id', 'nunique'),
        male_count=('sex', lambda x: (x == 'Male').sum()),
        female_count=('sex', lambda x: (x == 'Female').sum())
    ).reset_index()
    
    # Calculate percentages
    participation['male_percentage'] = np.where(participation['total_count'] > 0, 
                                                (participation['male_count'] / participation['total_count']) * 100, 
                                                0)
    participation['female_percentage'] = np.where(participation['total_count'] > 0, 
                                                  (participation['female_count'] / participation['total_count']) * 100, 
                                                  0)
    
    # Cap percentages at 100% to avoid any issues
    participation['male_percentage'] = participation['male_percentage'].clip(upper=100)
    participation['female_percentage'] = participation['female_percentage'].clip(upper=100)
    
    # Create the plot
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=participation['year'], y=participation['male_percentage'],
                             mode='lines+markers', name='Male'))
    fig.add_trace(go.Scatter(x=participation['year'], y=participation['female_percentage'],
                             mode='lines+markers', name='Female'))
    
    fig.update_layout(
        title=f'Percentage of Male and Female {medal_type} Athletes Over the Years ({country_selection})',
        xaxis_title='Year',
        yaxis_title='Percentage of Athletes',
        legend_title='Gender',
        hovermode="x unified"
    )
    
    st.plotly_chart(fig)


def display_best_performances(df, country_selection, medal_type, sport_filter=None):
    st.subheader(f"Best Performances - {country_selection}")
    
    if country_selection == "India":
        df_filtered = df[df['country'] == 'India']
    else:
        df_filtered = df
    
    if medal_type == "Individual":
        df_filtered = df_filtered[df_filtered['isTeamSport'] == False]
    else:
        df_filtered = df_filtered[df_filtered['isTeamSport'] == True]
    
    if sport_filter:
        df_filtered = df_filtered[df_filtered['sport'] == sport_filter]
    
    df_filtered = df_filtered[df_filtered['medal'] != '-']
    
    performances = df_filtered.groupby(['sport', 'name', 'country']).agg(
        gold=('medal', lambda x: (x == 'Gold').sum()),
        silver=('medal', lambda x: (x == 'Silver').sum()),
        bronze=('medal', lambda x: (x == 'Bronze').sum())
    ).reset_index()
    
    performances['total'] = performances['gold'] + performances['silver'] + performances['bronze']
    performances = performances.sort_values(['gold', 'silver', 'bronze', 'total'], ascending=[False, False, False, False])
    
    st.write(performances.head(5))

# Main app
def main():
    st.title("Olympics Dashboard")
    
    df = load_data()
    
    # Sidebar
    st.sidebar.header("Filters")
    country_selection = st.sidebar.radio("Select Region", ["World", "India"])
    medal_type = st.sidebar.radio("Medal Type", ["Individual", "Team"], index=0)
    year_range = st.sidebar.slider("Select Year Range", df['year'].min(), df['year'].max(), (df['year'].min(), df['year'].max()))
    
    # Sport selection dropdown
    sports = df['sport'].unique()
    sports = np.insert(sports, 0, 'All Sports')
    sport_filter = st.sidebar.selectbox("Select Sport", sports)
    
    # Filter data based on selection
    if country_selection == "India":
        df_filtered = df[df['country'] == 'India']
    else:
        df_filtered = df
    
    # Filter based on medal type
    if medal_type == "Individual":
        df_medals = df_filtered[(df_filtered['medal'] != '-') & (df_filtered['isTeamSport'] == False)]
    else:  # Team
        df_medals = df_filtered[(df_filtered['medal'] != '-') & (df_filtered['isTeamSport'] == True)]
    
    # Main content
    st.header(f"{country_selection}'s Olympic {medal_type} Medals")
    
    # Display medal winners
    display_medal_winners(df_medals, f"{medal_type} Medal Winners")
    
    # Gender participation over the years
    plot_gender_participation(df_filtered, country_selection, medal_type, year_range)
    
    # Top medal-winning sports
    st.subheader(f"Top Medal-Winning Sports")
    top_sports = df_medals['sport'].value_counts().head(5)
    if not top_sports.empty:
        fig = px.pie(values=top_sports.values, names=top_sports.index, title=f'Top {medal_type} Medal-Winning Sports')
        st.plotly_chart(fig)
    else:
        st.write("No medals won in this category.")
    
    # Best Performances
    display_best_performances(df_filtered, country_selection, medal_type, sport_filter)

if __name__ == "__main__":
    main()
