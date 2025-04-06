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
app.title = "Spotify “Unwrapped”"

app.layout = html.Div(
    style={
        'backgroundColor': '#191414',
        'color': '#FFFFFF',
        'fontFamily': 'system-ui, "Helvetica Neue", Arial, sans-serif',
        'padding': '30px'
    },
    children=[
        html.Div([
            html.H1("SPOTIFY “Unwrapped”", style={
                'textAlign': 'center',
                'fontWeight': 'bold',
                'color': '#1DB954',
                'marginBottom': '0px',
                'fontSize': '48px'
            }),
            html.H4("Analyzing Trends in Music Popularity and Characteristics", style={
                'textAlign': 'center',
                'fontStyle': 'italic',
                'color': '#FFFFFF',
                'marginTop': '5px'
            }),
        ], style={'marginBottom': '40px'}),

        html.Div([
            html.Label("🔘 View by:", style={'color': '#1DB954', 'fontWeight': 'bold'}),
            dcc.RadioItems(
                id='view-radio',
                options=[
                    {'label': 'Song', 'value': 'song'},
                    {'label': 'Artist', 'value': 'artist'}
                ],
                value='song',
                labelStyle={'display': 'inline-block', 'margin-right': '15px', 'color': '#FFFFFF'}
            ),

            html.Label("📅 Select Year Range:", style={'color': '#1DB954', 'fontWeight': 'bold'}),
            dcc.RangeSlider(
                id='year-range',
                min=df['year'].min(),
                max=df['year'].max(),
                step=1,
                marks={str(y): str(y) for y in sorted(df['year'].dropna().unique())},
                value=[df['year'].min(), df['year'].max()],
                tooltip={"placement": "bottom", "always_visible": True}
            ),

            html.Label("🎤 Select Song or Artist:", style={'color': '#1DB954', 'fontWeight': 'bold'}),
            dcc.Dropdown(id='entity-dropdown', style={'color': '#191414'})
        ], style={'margin-bottom': '40px'}),

        html.Div([
            dcc.Graph(id='choropleth-map', style={'width': '48%', 'display': 'inline-block'}),
            dcc.Graph(id='line-chart', style={'width': '48%', 'display': 'inline-block'})
        ]),

        html.Div([
            html.Label("📊 Select Attribute for Bar Chart:", style={'color': '#1DB954', 'fontWeight': 'bold'}),
            dcc.Dropdown(
                id='bar-attribute',
                options=[{'label': a, 'value': a} for a in audio_features],
                value='energy',
                style={'color': '#191414'}
            ),
            dcc.Graph(id='bar-chart')
        ], style={'margin-top': '40px'}),

        html.Div([
            html.Label("🔍 Correlation Explorer (Scatter Plot):", style={'color': '#1DB954', 'fontWeight': 'bold'}),
            html.Div([
                dcc.Dropdown(
                    id='x-attribute',
                    options=[{'label': a, 'value': a} for a in audio_features],
                    value='danceability',
                    style={'color': '#191414'}
                ),
                dcc.Dropdown(
                    id='y-attribute',
                    options=[{'label': a, 'value': a} for a in audio_features],
                    value='energy',
                    style={'color': '#191414'}
                )
            ], style={'display': 'flex', 'gap': '10px'}),
            dcc.Graph(id='scatter-plot')
        ], style={'margin-top': '40px'})
    ]
)

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