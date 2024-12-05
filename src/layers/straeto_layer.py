import pandas as pd
import plotly.graph_objects as go

def add_straeto_layer(fig):
    """Add stræto layer to the map showing bus stops with emphasis on the 20 most used stops"""
    if fig is None:
        print("Error: Invalid figure object")
        return fig

    try:
        # Load bus stops data
        stops_df = pd.read_csv('data/raw/bus/stops.txt')
        stops_df = stops_df[['stop_id', 'stop_name', 'stop_lat', 'stop_lon']]
        stops_df = stops_df.dropna(subset=['stop_lat', 'stop_lon'])
        
        # Load top 20 stops data
        popular_stops_df = pd.read_csv('data/processed/20.csv')
        popular_stop_names = set(popular_stops_df['stop_name'])
        flow_dict = dict(zip(popular_stops_df['stop_name'], 
                           popular_stops_df['Passenger flow in 2023']))
        rank_dict = dict(zip(popular_stops_df['stop_name'], 
                           popular_stops_df['Popularity rating']))
        
        # Add regular stops
        regular_stops = []
        popular_stops = []
        
        for _, stop in stops_df.iterrows():
            stop_name = stop['stop_name']
            is_popular = any(stop_name.startswith(pop_name) or pop_name.startswith(stop_name) 
                           for pop_name in popular_stop_names)
            
            if is_popular:
                matching_name = next(pop_name for pop_name in popular_stop_names 
                                   if stop_name.startswith(pop_name) or pop_name.startswith(stop_name))
                rank = rank_dict[matching_name]
                size = 20 - ((rank - 1) * 0.25)  # Size decreases with rank
                
                popular_stops.append({
                    'lat': stop['stop_lat'],
                    'lon': stop['stop_lon'],
                    'name': stop_name,
                    'rank': rank,
                    'flow': flow_dict[matching_name],
                    'size': size
                })
            else:
                regular_stops.append({
                    'lat': stop['stop_lat'],
                    'lon': stop['stop_lon'],
                    'name': stop_name
                })
        
        # Add regular stops trace
        if regular_stops:
            fig.add_trace(go.Scattermapbox(
                mode='markers',
                lon=[stop['lon'] for stop in regular_stops],
                lat=[stop['lat'] for stop in regular_stops],
                marker=dict(
                    size=6,
                    color='white',
                    opacity=0.6,
                    symbol='circle'
                ),
                text=[stop['name'] for stop in regular_stops],
                name='Regular Stops',
                hovertemplate="<b>%{text}</b><br><extra></extra>",
                showlegend=True
            ))
        
        # Add popular stops trace
        if popular_stops:
            fig.add_trace(go.Scattermapbox(
                mode='markers',
                lon=[stop['lon'] for stop in popular_stops],
                lat=[stop['lat'] for stop in popular_stops],
                marker=dict(
                    size=[stop['size'] for stop in popular_stops],
                    color='#2d6a3e',  # Medium green
                    opacity=0.8,
                    symbol='circle'
                ),
                text=[f"{stop['name']}<br>Daily Passengers: {stop['flow']:,}<br>Rank: #{stop['rank']}" 
                      for stop in popular_stops],
                name='Top 20 Stops',
                hovertemplate="<b>%{text}</b><br><extra></extra>",
                showlegend=True
            ))
        
        return fig
    except Exception as e:
        print(f"Error adding stræto layer: {e}")
        return fig
