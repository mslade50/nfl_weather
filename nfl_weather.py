import streamlit as st
import pandas as pd
import plotly.express as px
from streamlit_plotly_events import plotly_events

st.set_page_config(layout="wide")

# Load your Excel file
df = pd.read_csv('nfl_weather.csv')
df[['lat', 'lon']] = df['game_loc'].str.split(',', expand=True)
df['lat'] = pd.to_numeric(df['lat'], errors='coerce')
df['lon'] = pd.to_numeric(df['lon'], errors='coerce')

# Process data for map
df['dot_size'] = df['gs_fg'].abs()+0.8  # Create dot size based on 'gs_fg'
# Update 'wind_vol' to 'Low' if 'wind_fg' is less than 11.99
df.loc[df['wind_fg'] < 11.99, 'wind_vol'] = 'Low'

# Assign dot color based on conditions
def assign_dot_color(row):
    if row['temp_fg'] > 80 and row['wind_fg'] < 12:
        return 'red'  # Heat
    elif row['temp_fg'] < 30 and row['wind_fg'] < 12:
        return 'blue'  # Cold
    elif row['wind_fg'] >= 12:
        return 'purple'  # Wind
    elif row['rain_fg'] > 0 and row['wind_fg'] < 12:
        return 'black'  # Rain
    else:
        return 'green'  # Default/N/A

df['dot_color'] = df.apply(assign_dot_color, axis=1)

# Function to assign opacity, but only for purple dots (wind)
def assign_dot_opacity(row):
    if row['dot_color'] == 'purple':  # Only change opacity for 'Wind' dots
        if row['wind_vol'] == 'Very High':
            return 0.2  # Very low opacity for high wind
        elif row['wind_vol'] == 'Low':
            return 1.0  # Full opacity for low wind
        elif row['wind_vol'] == 'Mid':
            return 0.5
        elif row['wind_vol'] == 'High':
            return 0.35 # Medium opacity for mid wind
        else:
            return 1.0  # Default opacity for undefined wind_vol
    else:
        return 1.0  # Full opacity for non-wind dots

df['dot_opacity'] = df.apply(assign_dot_opacity, axis=1)

# Create the map using Plotly
fig = px.scatter_mapbox(
    df,
    lat="lat",  # Use the 'lat' column
    lon="lon",  # Use the 'lon' column
    hover_name="Game",  # Column to show on hover
    hover_data={
        "wind_fg": True,   # Show wind forecast
        "temp_fg": True,   # Show temperature forecast
        "rain_fg": True,   # Show rain forecast
        "gs_fg": True,     # Weather Impact percentage
        "Total_open": True,   # Opening total points
        "Total_now": True,    # Current total points
        "game_loc": True,     # Game location
        "wind_vol": True,     # Wind volatility
        "Spread_open": True,  # Opening spread
        "Spread_now": True    # Current spread
    },
    size="dot_size",  # Use the 'gs_fg' field for dot size
    color="dot_color",  # Color based on conditions
    color_discrete_map={
        'red': 'red',
        'blue': 'blue',
        'purple': 'purple',
        'black': 'black',
        'green': 'green'
    },
    zoom=6,  # Adjusted for better zoom in the US
    height=1000,  # Make the map occupy a larger portion of the page
)

# Update the layout to focus on the US and adjust map display
fig.update_layout(
    mapbox_style="open-street-map",
    mapbox_center={"lat": 37.0902, "lon": -95.7129},  # Center the map in the U.S.
    mapbox_zoom=3.5,  # Zoom to focus on U.S. only
    legend_title_text='Weather Conditions',  # Set custom legend title
)

# Manually update the legend labels for the colors
fig.for_each_trace(
    lambda t: t.update(
        name=t.name.replace('red', 'Heat')
                   .replace('blue', 'Cold')
                   .replace('purple', 'Wind')
                   .replace('black', 'Rain')
                   .replace('green', 'N/A')
    )
)

# Apply opacity only to purple dots (Wind)
fig.update_traces(
    selector=dict(marker_color='purple'),  # Only select purple (wind) dots
    marker_opacity=df['dot_opacity']  # Apply opacity based on wind_vol
)

# Update hover template to match your new column names
fig.update_traces(
    hovertemplate="<b>%{hovertext}</b><br>" + 
    "Wind: %{customdata[0]}<br>" +
    "Temp: %{customdata[1]}<br>" +
    "Rain: %{customdata[2]}<br>" +
    "Weather Impact: %{customdata[3]}%<br>" +
    "Total (Open): %{customdata[4]}<br>" +
    "Total (Now): %{customdata[5]}<br>" +
    "Game Location: %{customdata[6]}<br>" +
    "Wind Volatility: %{customdata[7]}<br>" +
    "Spread (Open): %{customdata[8]}<br>" +
    "Spread (Now): %{customdata[9]}<extra></extra>"
)

# Display in Streamlit with wide layout
st.title("NFL Weather Map")
st.plotly_chart(fig)

if st.sidebar.checkbox("Show game details", False):
    # Select a game
    game = st.sidebar.selectbox("Select a game", df['Game'].unique())
    selected_game = df[df['Game'] == game]

    if not selected_game.empty:
        st.write(f"Details for {game}")
        
        # Add a percentage sign to 'gs_fg' and rename it to 'Weather Impact'
        selected_game['Weather Impact'] = selected_game['gs_fg'].apply(lambda x: f"{x}%")
        
        # Reorder the columns to match your hover data order and table display
        reordered_columns = [
            'wind_fg', 
            'temp_fg', 
            'rain_fg',
            'Weather Impact',  # Renamed column
            'Total_open', 
            'Total_now', 
            'Spread_open', 
            'Spread_now',
            'wind_vol',  # Wind volatility
            'Date',      # Date
            'Time',      # Time
            'game_loc'   # Game location
        ]

        # Round numeric columns to 1 decimal place where needed
        numeric_columns = [
            'wind_fg', 
            'temp_fg', 
            'rain_fg', 
            'Total_open', 
            'Total_now', 
            'Spread_open', 
            'Spread_now',
        ]
        selected_game[numeric_columns] = selected_game[numeric_columns].apply(lambda x: x.round(1))

        # Display the selected game's details
        st.table(selected_game[reordered_columns])
