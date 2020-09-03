import dash
import dash_auth
import dash_core_components as dcc
import dash_table as dt
import dash_html_components as html
import pandas as pd
pd.options.mode.chained_assignment = None
from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate
import plotly.graph_objs as go
import time
import datetime
import flask
import base64
import requests
import json
from pandas.io.json import json_normalize
from datetime import datetime, timedelta
import io
import csv
from ratelimit import limits, sleep_and_retry
import math
import re
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# -*- coding: utf-8 -*-
server = flask.Flask(__name__)

app = dash.Dash(__name__, server=server)
app.title = "mp2_jgrotton3"

request = 'https://api.covidtracking.com/v1/states/current.json'
r = requests.get(request, verify=False)
if r.status_code == 200:
    df = pd.read_json(r.text)
    df = df[['state', 'positive', 'death', 'hospitalizedCumulative', 'inIcuCumulative']]
    df = df.fillna(0)
else:
    df = pd.DataFrame(columns=['state', 'positive', 'death', 'hospitalizedCumulative', 'inIcuCumulative'])

df_race = pd.read_csv('Race Data Entry - CRDT.csv')
df_race = df_race.head(56)
df_race = df_race[['State', 'Cases_White', 'Cases_Black', 'Cases_LatinX', 'Cases_Asian', 'Cases_AIAN', 'Cases_NHPI', 'Cases_Multiracial', 'Cases_Other', 'Deaths_White', 'Deaths_Black', 'Deaths_LatinX', 'Deaths_Asian', 'Deaths_AIAN', 'Deaths_NHPI', 'Deaths_Multiracial', 'Deaths_Other']]
df_race = df_race.fillna(0)

def calculate_cfr(row):
    if row['death'] > 0 and row['positive'] > 0:
        return round(((row['death'] / row['positive']) * 100), 2)
    else:
        return 0

def calculate_hr(row):
    if row['hospitalizedCumulative'] > 0 and row['positive'] > 0:
        return round(((row['hospitalizedCumulative'] / row['positive']) * 100), 2)
    else:
        return 0

def calculate_icu(row):
    if row['inIcuCumulative'] > 0 and row['positive'] > 0:
        return round(((row['inIcuCumulative'] / row['positive']) * 100), 2)
    else:
        return 0

def total_cfr(df):
    total_death = df['death'].astype(float).sum()
    total_positive = df['positive'].astype(float).sum()
    if total_death > 0 and total_positive > 0:
        return str(round(((total_death / total_positive) * 100), 2))
    else:
        return '0'

df['cfr'] = df.apply(calculate_cfr, axis=1)
df['hr'] = df.apply(calculate_hr, axis=1)
df['icu'] = df.apply(calculate_icu, axis=1)

#print(df_race)

df = df.astype(str)

df['text'] = 'Case Fatality Rate ' + df['cfr'] + '%' + '<br>' + 'Hospitalization Rate ' + df['hr'] + '%' + '<br>' + 'ICU Rate ' + df['icu'] + '%'

fig = go.Figure(data=go.Choropleth(
    locations=df['state'],
    z=df['cfr'].astype(float),
    locationmode='USA-states',
    colorscale='blues',
    autocolorscale=False,
    text=df['text'], 
    marker_line_color='white', 
    colorbar_title="CFR"
))

fig.update_layout(
    title_text='COVID-19 Case Fatality Rate by State',
    geo = dict(
        scope='usa',
        projection=go.layout.geo.Projection(type = 'albers usa'),
        showlakes=True,
        bgcolor='#CCCCCC',
        lakecolor='rgb(255, 255, 255)'),
    margin=dict(t=50, b=0, l=0, r=0), 
    paper_bgcolor='#CCCCCC',
    font={
        'color': 'blue'
    }
)

race_traces = []
race_layout = go.Layout(title = {
                'text': '<b>CFR by Race</b>'
                },
                hovermode = 'closest', plot_bgcolor='#CCCCCC', paper_bgcolor='#CCCCCC', barmode = 'overlay',
                height = 500,
                #width = 1100,
                font = {
                    'color': 'blue'
                },
                titlefont = {
                    'color': 'blue'
                },
                showlegend = False, 
                xaxis = {
                    'zeroline': False,
                    'showgrid': False,
                    'gridcolor':'black',
                    'showline': False,
                    'linewidth': 3,
                    'linecolor': 'black',
                    'mirror': True
                },
                yaxis = {
                    'zeroline': False,
                    'showline': False,
                    'linewidth': 1,
                    'linecolor': 'black',
                    'mirror': False
                })
cfr_race = go.Figure(data=race_traces, layout=race_layout)

def serve_layout():
    return html.Div(id='display-value', style={'backgroundColor': '#E3E3E3', 'margin-bottom': 0}, children=[
        html.H1(children='Mini Project #2',
                    style={
                        'padding-top': 10,
                        'textAlign': 'center',
                        'color': '#0B2062',
                        'backgroundColor': '#E3E3E3',
                        'text-decoration': 'underline',
                        'font-size': '300%',
                        'font-family': 'Helvetica',
                        'text-shadow': '2px 2px #FFFFFF',
                        'font-style': 'italic',
                        'margin-bottom': 0
                    }),
        html.H4(children='Justin Grotton',
                    style={
                        'textAlign': 'center',
                        'color': '#0B2062',
                        'backgroundColor': '#E3E3E3',
                        'font-family': 'Helvetica',
                        'margin-bottom': 0
                    }),
        html.Hr(),
        html.Div(
            children=[
                html.Label(children='Overall CFR: ' + total_cfr(df) + '%',
                style={
                    'textAlign': 'center',
                    'font-size': '200%',
                    'color': '#FFFFFF',
                    'fontWeight': 'bold',
                    'font-family': 'Gravitas One',
                })
            ],
            style={
                'textAlign': 'center',
                'margin-right': 150,
                'margin-left': 150,
                'backgroundColor': '#0B2062'
            }
        ),
        html.Div(
            children=[dcc.Graph(id='fig', figure=fig)],
            style={
                'textAlign': 'center',
                'margin-right': 150,
                'margin-left': 150,
                'backgroundColor': '#CCCCCC',
                "border":"2px #0B2062 solid"
            }
        ),
        html.Hr(),
        html.Div(
            children=[dcc.Graph(id='cfr_race', figure=cfr_race)],
            style={
                'textAlign': 'center',
                'margin-right': 150,
                'margin-left': 150,
                'backgroundColor': '#CCCCCC',
                "border":"2px #0B2062 solid"
            }
        )
    ])

app.layout = serve_layout

# Suppress conditional callbacks
app.config['suppress_callback_exceptions']=True

@app.callback(Output("cfr_race", "figure"), [Input("fig", "hoverData")])
def event_cb(data):
    race_traces = []
    if data  is None:
        state_bar = df_race['State'].iloc[0]
    else:
        state_bar = data['points']
        state_bar = state_bar[0]['location']

    state = df_race.loc[df_race['State'] == state_bar]
    state = state.drop('State', 1)
    state = state.astype(float)
    cases = state[['Cases_Black', 'Cases_AIAN', 'Cases_LatinX', 'Cases_White', 'Cases_Asian', 'Cases_NHPI', 'Cases_Other', 'Cases_Multiracial']]
    cases = cases.values.tolist()[0]
    deaths = state[['Deaths_Black', 'Deaths_AIAN', 'Deaths_LatinX', 'Deaths_White', 'Deaths_Asian', 'Deaths_NHPI', 'Deaths_Other', 'Deaths_Multiracial']]
    deaths = deaths.values.tolist()[0]
    y = ['Black', 'AIAN', 'Hispanic or Latino', 'White', 'Asian', 'NHPI', 'Other', 'Multiracial']
    cfr = []

    for i, case in enumerate(cases):
        if case > 0 and deaths[i] > 0:
            cfr.append(str(round(((deaths[i] / case) * 100), 2)) + '%')
        else:
            cfr.append('0' + '%')

    case_trace = go.Bar(x=cases,
        y=y,
        text=cfr,
        textposition='auto',
        textfont=dict(
            family="sans serif",
            size=18,
            color="blue"
        ),
        name='Cases',
        orientation='h',
        marker=dict(
            color='#f0f8ff', 
            line=dict(color='black', width=2))
    )

    death_trace = go.Bar(x=deaths,
        y=y,
        name='Deaths',
        orientation='h',
        marker=dict(
            color='rgba(58, 71, 80, 0.6)', 
            line=dict(color='black', width=2))
    )

    race_traces.append(case_trace)
    race_traces.append(death_trace)

    cfr_race = go.Figure(data=race_traces, layout=race_layout)
    cfr_race.layout.update(title_text='CFR by Race: ' + state_bar)
    return cfr_race

server = app.server

if __name__ == '__main__':
    app.run_server(debug=True)
