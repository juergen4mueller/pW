from dash import dash, dcc, html, callback_context, dash_table
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

from sqlite3 import Error

root = sys.path[0]

def traceFileList():
    files = os.listdir(os.path.join(root,"tracefile"))
    tracefiles = []
    for file in files:
        if file.endswith(".sqlite"):
            tracefiles.append(file)
            #print(file)
    return tracefiles

#daten = get_table(r"/home/pi/pW/tracefile/20221205_124300_log.sqlite")  

 

def get_table(dateiname = "Vorlage.sqlite"): #später leeres übergeben
    
    sqfile_path = os.path.join(root,'tracefile',dateiname)

    conn = None
    try: 
        conn = sqlite3.connect(sqfile_path)
        print(conn)
    except Error as e:
        print(e)
    
    daten = pd.read_sql_query("select * from loggings",conn)
    conn.close()
    return daten
 
def get_graph(dateiname = "Vorlage.sqlite"): #später leeres übergeben
    
    sqfile_path = os.path.join(root,'tracefile',dateiname)
    
    conn = None
    try: 
        conn = sqlite3.connect(sqfile_path)
        print(conn)
    except Error as e:
        print(e)
    
    daten_map = pd.read_sql_query("select * from loggings",conn)
    del daten_map['posx']
    del daten_map['posy']
    del daten_map['direction']
    daten_map.insert (loc = len(daten_map.columns), column='size', value=2)
    conn.close()
    
    fig = px.scatter_mapbox(daten_map,
                         lat='lat',
                         lon='lon',
                         #text ='code',
                         color='id',
                         zoom=15,
                         size = 'size',
                         mapbox_style="open-street-map",
                         #mapbox_style="street",
                         #size=10
                         )  
    
    return fig
 

tracefiles = traceFileList()  
daten = get_table()
fig = get_graph()        




    
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
                         children="Personalisierte Werbung V1.0",
                         style={
                             "textAlign": "center",
                             "marginTop": 40,
                             "marginBottom": 40,
                             "text-decoration": "underline",
                         },
                     ),
                ),
                dcc.Dropdown(
                    options= tracefiles, 
                    value = tracefiles[0], 
                    id="dropdown_tracefiles"
                    ),
                
            ],
            #justify="center",
        ),

           dbc.Row(
              [
                  dcc.Graph(
                      id="graph",
                      figure=fig,
                  ),
                  #dcc.Interval(id="interval_100s", interval=100000),
                  #dcc.RangeSlider(0, 100, 5, value=[0, 100], id="range_slider"),
              ]       
             ),
            dbc.Row(
                 dash_table.DataTable(
                 
                    #daten.to_dict('records'),[{"name":i, "id":i} for i in daten.columns],

                     id = 'table',
                     data = [],
                     editable=True,
                     style_data={
                                    'color': 'black',
                                    'backgroundColor': 'white'
                                },
                                
                    style_data_conditional=[
                                {
                                    'if': {'row_index': 'odd'},
                                    'backgroundColor': 'rgb(220, 220, 220)',
                                }
                    ],
    
                    style_header={
                                    'backgroundColor': 'rgb(210, 210, 210)',
                                    'color': 'black',
                                    'fontWeight': 'bold'
                                }
                    
                 
                 ),
                )  
    ]
)

@app.callback(
    Output('table','data'),
    Output('table','columns'),
    Input('dropdown_tracefiles', 'value'),
)

def update_table(dateiname):        #Dateiname zurückgeben
    print("dateinameapp",dateiname)
    daten = get_table(dateiname)
    data = daten.to_dict('records'),[{"name":i, "id":i} for i in daten.columns],
    return data

@app.callback(
    Output('graph','figure'),
    Input('dropdown_tracefiles','value'),
    )

def update_graph(dateiname):
    print("graph",dateiname)
    return get_graph(dateiname)
    

if __name__ == "__main__":
    app.run_server(debug=True, host="0.0.0.0", port=8055)



# app.layout = dbc.Container(
#     [
#         dbc.Row(
#             [  # Row 1
#                 dbc.Col(
#                     html.H1(
#                         id="title_main",
#                         children="Waypoints",
#                         style={
#                             "textAlign": "center",
#                             "marginTop": 40,
#                             "marginBottom": 40,
#                             "text-decoration": "underline",
#                         },
#                     ),
#                 ),
#                 dcc.Dropdown(traceFiles, traceFiles[0], id="dropdown_tracefiles"),
#             ],
#             justify="center",
#         ),
#         dbc.Row(
#             [
#                 dcc.Graph(
#                     id="graph_temp",
#                     figure=fig,
#                 ),
#                 dcc.Interval(id="interval_100s", interval=100000),
#                 dcc.RangeSlider(0, 100, 5, value=[0, 100], id="range_slider"),
#             ]
#         ),
#     ]
# )



# 
# def get_graph(val_range, tracefile="trace.sqlite"):
#     db_path = os.path.join(root, tracefile)
#     sql_con = sqlite3.connect(db_path)
#     #try:
#     print(sql_con)
#     df = pd.read_sql_query("select * from loggings", sql_con)
#     dfLength = df.count()[0]
#     minval = val_range[0] * dfLength // 100
#     maxval = val_range[1] * dfLength // 100
#     df = df.iloc[minval:maxval]
#     sql_con.close()
#     fig = px.scatter_mapbox(
#             df,
#             lat="lat",
#             lon="lon",
#             hover_name="direction",
#             color="speed",
#             zoom=10,
#             mapbox_style="open-street-map",
#     )
#     #except:
#      #   print("file error")
#     fig = None
#     return fig
# 
# 

# #fig =  get_graph([0, 100])
# traceFiles = traceFileList()
# 
# 


# 
# @app.callback(
#     Output("graph_temp", "figure"),
#     Input("interval_100s", "n_intervals"),
#     Input("range_slider", "value"),
#     Input("dropdown_tracefiles", "value"),
# )
# def update_graph(n_intervals, range_slider_values, tracefile):
#     return get_graph(range_slider_values, tracefile)
# 
# 

################Eichi BackUp#################################

# Ausgelagerte Funktion Connect für sq-Lite aufbauen
# ~ def create_connection(trace_file):
    # ~ """ Create a database Connection to SQLite Database"""
    # ~ conn = None
    # ~ try:
        # ~ conn = sqlite3.connect(trace_file)
    # ~ except Error as e:
        # ~ print(e)
    
    # ~ return conn

#Ausgelagerte Funktion pd-Frame bilden
# ~ def select_all_loggings(conn):
    # ~ """ Logfile auslesen"""
    
    # ~ df = pd.read_sql_query("select * from loggings",conn)
    # ~ #print(df)
    # ~ #print(type(df))
    # ~ #print(df.size)
    # ~ return df
   
