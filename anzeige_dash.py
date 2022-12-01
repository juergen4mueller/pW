from dash import dash, dcc, html, callback_context
from dash.dependencies import Input, Output, State
import dash_bootstrap_components as dbc
import os
import json
import time
import sys
import socket
from flask import Flask

import datetime
import pandas as pd
import numpy as np
import plotly.express as px
import sqlite3

root = sys.path[0]


def get_graph(val_range, tracefile="trace.sqlite"):
    db_path = os.path.join(root, tracefile)
    sql_con = sqlite3.connect(db_path)
    try:
        df = pd.read_sql_query("select * from loggings", sql_con)
        dfLength = df.count()[0]
        minval = val_range[0] * dfLength // 100
        maxval = val_range[1] * dfLength // 100
        df = df.iloc[minval:maxval]
        sql_con.close()
        fig = px.scatter_mapbox(
            df,
            lat="lat",
            lon="lon",
            hover_name="direction",
            color="speed",
            zoom=10,
            mapbox_style="open-street-map",
        )
    except:
        print("file error")
        fig = None
    return fig


def traceFileList():
    files = os.listdir(os.path.join(root,"tracefile"))
    tracefiles = []
    for file in files:
        if file.endswith(".sqlite"):
            tracefiles.append(file)
            print(file)
    return tracefiles


fig =  None#get_graph([0, 100])
traceFiles = traceFileList()

app = dash.Dash(
    "PersWerb Display",
    external_stylesheets=[dbc.themes.SUPERHERO],
    meta_tags=[
        {"name": "viewport"},
        {"content": "width = device,width, initial-scale=1.0"},
    ],
)

app.layout = dbc.Container(
    [
        dbc.Row(
            [  # Row 1
                dbc.Col(
                    html.H1(
                        id="title_main",
                        children="Waypoints",
                        style={
                            "textAlign": "center",
                            "marginTop": 40,
                            "marginBottom": 40,
                            "text-decoration": "underline",
                        },
                    ),
                ),
                dcc.Dropdown(traceFiles, traceFiles[0], id="dropdown_tracefiles"),
            ],
            justify="center",
        ),
        dbc.Row(
            [
                dcc.Graph(
                    id="graph_temp",
                    figure=fig,
                ),
                dcc.Interval(id="interval_100s", interval=100000),
                dcc.RangeSlider(0, 100, 5, value=[0, 100], id="range_slider"),
            ]
        ),
    ]
)


@app.callback(
    Output("graph_temp", "figure"),
    Input("interval_100s", "n_intervals"),
    Input("range_slider", "value"),
    Input("dropdown_tracefiles", "value"),
)
def update_graph(n_intervals, range_slider_values, tracefile):
    return get_graph(range_slider_values, tracefile)


if __name__ == "__main__":
    app.run_server(debug=True, host="0.0.0.0", port=8055)
