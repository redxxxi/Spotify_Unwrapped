import dash
from dash import dcc, html, Input, Output
import pandas as pd
import plotly.express as px
import dash_bootstrap_components as dbc

# Load dataset
df = pd.read_csv("universal_top_spotify_songs.csv")

# Clean & prep columns
df.columns = df.columns.str.strip().str.lower().str.replace(" ", "_")
df['snapshot_date'] = pd.to_datetime(df['snapshot_date'], errors='coerce')
df['year'] = df['snapshot_date'].dt.year
df['month'] = df['snapshot_date'].dt.month

# Audio features to analyze
audio_features = [
    'danceability', 'energy', 'acousticness', 'instrumentalness', 'liveness',
    'valence', 'tempo', 'speechiness', 'loudness', 'duration_ms'
]

# Get top unique artists/songs
df['artists'] = df['artists'].astype(str)
df['track_id'] = df['artists'] + " | " + df['name']
top_artists = df['artists'].dropna().unique()
top_tracks = df['track_id'].dropna().unique()

# Dash app setup
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

# Layout
app.layout = html.Div([
    # DLSU Logo
    html.Div([
        html.Img(src="De_La_Salle_University_Seal.png", className="dlsu-corner-logo")
    ], className="dlsu-logo-overlay"),

    # Sidebar
    html.Div([
        html.Div([
            html.Img(src="https://storage.googleapis.com/pr-newsroom-wp/1/2018/11/Spotify_Logo_RGB_White.png", className="spotify-logo"),
            html.Div([
                html.Div([html.I(className="fas fa-home"), " Home"], className="menu-item active"),
                html.Div([html.I(className="fas fa-search"), " Search"], className="menu-item"),
                html.Div([html.I(className="fas fa-book"), " Your Library"], className="menu-item"),
            ], className="sidebar-menu"),
            html.Img(src="Side bar.png", className="sidebar-image")
        ], className="sidebar-content")
    ], className="sidebar d-none d-md-block"),

    # Main Content
    html.Div([
        # Navigation Bar
        dbc.Navbar([
            html.Div([
                dbc.Button("☰", className="navbar-toggler", id="navbar-toggle"),
            ], className="d-md-none"),
            html.Div([
                dbc.NavLink("All Music", href="#"),
                dbc.NavLink("About The Topic", href="#"),
                dbc.NavLink("Podcast", href="#"),
                dbc.Button("LISTEN NOW", className="listen-btn")
            ], className="nav-buttons ml-auto")
        ], className="navbar navbar-dark"),

        # Content Section
        html.Div([
            html.H1("Analyzing Trends in Music Popularity and Characteristics (2000-2019)"),
            html.H3("Problem Statement"),
            html.P("Music trends reflect cultural and technological changes, influencing and mirroring society."),
        ], className="content-section"),

        # Controls & Visualization
        dbc.Row([
            dbc.Col([
                html.Div([
                    html.H4("Data Controls"),
                    dcc.Dropdown([
                        "Blinding Lights - The Weeknd", "Shape of You - Ed Sheeran", "Dance Monkey - Tones and I", "Believer - Imagine Dragons"
                    ], "Blinding Lights - The Weeknd", className="custom-select"),
                    dcc.DatePickerRange(start_date="2000-01-01", end_date="2019-12-31", className="date-range"),
                    dcc.RadioItems([
                        {"label": "Song", "value": "song"},
                        {"label": "Artist", "value": "artist"}
                    ], "song", className="custom-control"),
                    dcc.Dropdown([
                        "Danceability", "Energy", "Tempo", "Acousticness", "Valence"
                    ], "Danceability", className="custom-select"),
                ], className="content-section")
            ], width=4),
            
            dbc.Col([
                html.Div([
                    html.H4("Global Music Popularity by Region"),
                    dcc.Graph(figure=px.choropleth())
                ], className="content-section"),
                html.Div([
                    html.H4("Audio Feature Trends Over Time"),
                    dcc.Graph(figure=px.line())
                ], className="content-section")
            ], width=8)
        ]),

        # Footer
        html.Footer([
            html.Div(["© 2024 Spotify Unwrapped. All Rights Reserved."]),
            html.Img(src="De_La_Salle_University_Seal.png", className="dlsu-logo-small")
        ], className="footer")
    ], className="main-content")
])

# Callback functions
@app.callback(
    Output('entity-dropdown', 'options'),
    Output('entity-dropdown', 'value'),
    Input('view-radio', 'value')
)
def update_dropdown(view_type):
    if view_type == 'song':
        options = [{'label': name, 'value': name} for name in sorted(top_tracks)]
        return options, options[0]['value']
    else:
        options = [{'label': name, 'value': name} for name in sorted(top_artists)]
        return options, options[0]['value']

@app.callback(
    Output('choropleth-map', 'figure'),
    Output('line-chart', 'figure'),
    Input('view-radio', 'value'),
    Input('entity-dropdown', 'value'),
    Input('year-range', 'value')
)
def update_visuals(view, entity, year_range):
    dff = df[(df['year'] >= year_range[0]) & (df['year'] <= year_range[1])]

    if view == 'song':
        dff = dff[df['track_id'] == entity]
    else:
        dff = dff[df['artists'] == entity]

    map_fig = px.choropleth(
        dff,
        locations='country',
        locationmode='country names',
        color='popularity',
        hover_name='country',
        title='Popularity by Country'
    )
    map_fig.update_layout(paper_bgcolor='#191414', plot_bgcolor='#191414', font_color='#FFFFFF')

    line_data = dff.groupby('year')[audio_features].mean().reset_index()
    line_fig = px.line(line_data, x='year', y=audio_features, title='Audio Features Over Time')
    line_fig.update_layout(paper_bgcolor='#191414', plot_bgcolor='#191414', font_color='#FFFFFF')

    return map_fig, line_fig

@app.callback(
    Output('bar-chart', 'figure'),
    Input('bar-attribute', 'value')
)
def update_bar_chart(attribute):
    bar_data = df.groupby('track_id')[attribute].mean().sort_values(ascending=False).head(10).reset_index()
    fig = px.bar(bar_data, x='track_id', y=attribute, title=f"{attribute.capitalize()} by Song")
    fig.update_layout(paper_bgcolor='#191414', plot_bgcolor='#191414', font_color='#FFFFFF')
    return fig

@app.callback(
    Output('scatter-plot', 'figure'),
    Input('x-attribute', 'value'),
    Input('y-attribute', 'value')
)
def update_scatter(x_attr, y_attr):
    fig = px.scatter(df, x=x_attr, y=y_attr, color='popularity',
                     hover_name='artists', title=f"{x_attr.capitalize()} vs {y_attr.capitalize()}")
    fig.update_layout(paper_bgcolor='#191414', plot_bgcolor='#191414', font_color='#FFFFFF')
    return fig

if __name__ == '__main__':
    app.run_server(debug=True)
