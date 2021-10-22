# Import required libraries
import pickle
import copy
import pathlib
import urllib.request
import dash
import dash_table
import math
import datetime as dt
import pandas as pd
import numpy as np
import base64
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from dash.dependencies import Input, Output, State, ClientsideFunction
import dash_core_components as dcc
import dash_html_components as html

# get relative data folder
PATH = pathlib.Path(__file__).parent
DATA_PATH = PATH.joinpath("data").resolve()
LogList = []
PrintStart = 20

app = dash.Dash(
    __name__, meta_tags=[{"name": "viewport", "content": "width=device-width"}],
)
app.title = "CLIP3D Log Analysis"
server = app.server

# Create global chart template
mapbox_access_token = "pk.eyJ1IjoicGxvdGx5bWFwYm94IiwiYSI6ImNrOWJqb2F4djBnMjEzbG50amg0dnJieG4ifQ.Zme1-Uzoi75IaFbieBDl3A"

layout = dict(
    autosize=True,
    automargin=True,
    margin=dict(l=30, r=30, b=20, t=40),
    hovermode="closest",
    plot_bgcolor="#F9F9F9",
    paper_bgcolor="#F9F9F9",
    legend=dict(font=dict(size=10), orientation="h"),
    title="Satellite Overview",
    xaxis={"title": "", "gridcolor": "#DE6DB51"},
    yaxis={"title": "", "gridcolor": "#DE6DB51"},
    mapbox=dict(
        accesstoken=mapbox_access_token,
        style="light",
        center=dict(lon=-78.05, lat=42.54),
        zoom=7,
    ),
)

layoutGO = dict(
    autosize=True,
    margin=dict(l=30, r=30, b=20, t=40),
    hovermode="closest",
    plot_bgcolor="#F9F9F9",
    paper_bgcolor="#F9F9F9",
    legend=dict(font=dict(size=10), orientation="h"),
    title="",
    xaxis={"title": ""},
    yaxis={"title": ""},
    mapbox=dict(
        accesstoken=mapbox_access_token,
        style="light",
        center=dict(lon=-78.05, lat=42.54),
        zoom=7,
    ),
)

# Create app layout
app.layout = html.Div(
    [
        dcc.Store(id='input_data'),
        # empty Div to trigger javascript file for graph resizing
        html.Div(id="output-clientside"),
        html.Div(
            [
                html.Div(
                    [
                        html.Img(
                            src=app.get_asset_url("DeSimoneLogo2.png"),
                            id="plotly-image",
                            style={
                                "height": "40px",
                                "width": "auto",
                                "margin-bottom": "0px",
                            },
                        )
                    ],
                    className="one-fourth column",
                ),
                html.Div(
                    [
                        html.Div(
                            [
                                html.H2(
                                    "CLIP3D Print Log Analysis",
                                    style={"margin-bottom": "10px"},
                                ),
                            ]
                        )
                    ],
                    className="one-fourth column",
                    id="title",
                ),
                html.Div(
                    [
                        html.A(
                            html.Button("Download Report", id="learn-more-button"),
                            href="https://plot.ly/dash/pricing/",
                            style={"margin-bottom": "20px"}
                        )
                    ],
                    className="one-fourth column",
                    id="button",
                ),
            ],
            id="header",
            className="row flex-display",
            style={"margin-bottom": "25px", "justify-content": "center"},
        ),
        html.Div(
            [
                html.Div(
                    [
                        html.Div(
                            className="padding-top-bot",
                            children=[
                                html.H5("Upload Print Log"),
                                dcc.Upload(
                                    id="upload-data",
                                    className="upload",
                                    children=html.Div(
                                        children=[
                                            html.P("Drag and Drop or "),
                                            html.A("Select Files"),
                                        ]
                                    ),
                                    accept=".txt",
                                ),
                            ],
                        ),
                        html.H6(
                            "Selected File:",
                            className="filename_label",
                        ),
                        html.P(
                            id="log-name"
                        ),
                        html.H6(
                            "Slice Image Location:",
                            className="file_location_label",
                        ),
                        html.P(
                            id="image-location"
                        ),
                        html.Div(
                            [   
                                html.A(
                                    html.Button("Use Example Log", id="Example_Data", n_clicks=0),
                                    style={"margin-bottom": "20px"}
                                )
                            ],
                            id="button2",
                            style={"justify-content": "center"},
                        ),   
                    ],
                    className="pretty_container four columns",
                    id="cross-filter-options",
                ),
                html.Div(
                    [
                        html.Div(
                            [
                                html.Div(
                                    [html.H6(id="resinText"), html.P("Resin")],
                                    id="wells",
                                    className="mini_container",
                                ),
                                html.Div(
                                    [html.H6(id="layerText"), html.P("Layers")],
                                    id="gas",
                                    className="mini_container",
                                ),
                                html.Div(
                                    [html.H6(id="heightText"), html.P("Build Height")],
                                    id="oil",
                                    className="mini_container",
                                ),
                                html.Div(
                                    [html.H6(id="timeText"), html.P("Print Time")],
                                    id="water",
                                    className="mini_container",
                                ),
                            ],
                            id="info-container",
                            className="row container-display",
                        ),
                        html.Div(
                            [
                                html.Div(
                                    [
                                        dcc.Textarea(
                                            id='user_text',
                                            value='Add any additional notes here',
                                            style={'width': '100%', 'height': 180},
                                        ),
                                    ],
                                    style={'whiteSpace': 'pre-line'}, 
                                    className="mini_container four columns",
                                ),  
                                html.Div(id="mode_table", className="mini_container four columns"),
                                html.Div(id="general_table", className="mini_container four columns"),
                            ],
                            className="row container-display",
                        ),
                        html.Div(
                            [
                                html.Div(id="stage_table", className="mini_container  four columns"),
                                html.Div(id="light_table", className="mini_container  four columns"),
                                html.Div(id="injection_table", className="mini_container  four columns"),
                            ],
                            className="row container-display",
                        ),
                    ],
                    id="right-column",
                    className="eight columns",
                ),
            ],
            className="row flex-display",
            style={"justify-content": "center"},
        ),
        html.Div(
            [
                html.Div(
                    [dcc.Graph(id="ps_graph")],
                    className="pretty_container seven columns",
                ),
                html.Div(
                    [dcc.Graph(id="stage_graph")],
                    className="pretty_container five columns",
                ),
            ],
            className="row flex-display",
            style={"justify-content": "center"}
        ),
        html.Div(
            [
                html.Div(
                    [dcc.Graph(id="ps_graph2")],
                    className="pretty_container seven columns",
                ),
                html.Div(
                    [dcc.Graph(id="stage_graph2")],
                    className="pretty_container five columns",
                ),
            ],
            className="row flex-display",
            style={"justify-content": "center"}
        ),
        dcc.Textarea(
            id='textarea-example',
            value='Textarea content initialized\nwith multiple lines of text',
            style={'width': '100%', 'height': 300},
        ),
        html.Div(id='textarea-example-output', 
                 style={'whiteSpace': 'pre-line', }),
    ],
    id="mainContainer",
    style={"display": "flex", "flex-direction": "column", "justify-content": "center"},
)

# Helper functions
def parseContents(contents, type):
    stringlist = []
    if contents:
        if(type == 0):
            content_type, content_string = contents.split(",")
            decoded = base64.b64decode(content_string)
            decodedlist = decoded.split(b'\r\n')
            for i in range(1, len(decodedlist)):
                stringlist.append(str(decodedlist[i], 'cp1252'))
        elif(type == 1):
            decoded = contents
            decodedlist = decoded.split('\r\n')
            stringlist = decodedlist
        
        testkey = "Entering Printing Procedure"
        for i in range(0,len(decodedlist)):
            testobj = decodedlist[i]
            if(testobj[0:len(testkey)] == testkey):
                PrintStart = i
    return stringlist[0:]

def getTestKeyLoc(input_list, testKey):
    Loc = 0
    for i in range(0,len(input_list)):
        testobj = input_list[i]
        if(testobj[0:len(testKey)] == testKey):
            Loc = i
            break
    return Loc
    
def GenerateTable(InputList, Keys, Remove):
    TableData = InputList[1:len(InputList)]
    TableIndex = Keys
    TableTitle = InputList[0]
    
    if (Remove):
        loopCount = 0
        for i in (range(0,len(TableData))):
            if (TableData[loopCount] == []):
                TableData.pop(loopCount)
                TableIndex.pop(loopCount)
            else:
                loopCount += 1
    df = pd.DataFrame(TableData, 
                        index = TableIndex, 
                        columns = [TableTitle])
    return df

def ExtractStringData(InputList, TestKey, EndTrim, OutputType):
  DataList = [0]                                 # Initialize DataList variable
  for i in range(0, len(InputList)):             # Iterate over each entry
    testobj = InputList[i]                       #
    if (testobj[0:len(TestKey)] == TestKey):     #
      testobj = testobj[len(TestKey):]           #
      testobj = testobj[:len(testobj)-EndTrim]   #
      if (testobj != "NA"):                      #
        if (OutputType == "float"):              #
          DataList.append(float(testobj))        #
        else:                                    #
          DataList.append(testobj)               #
  return DataList[1:]                  

def CalcTotalTime(InputList):
    DataList = []
    if (InputList):
        for i in range(0,len(InputList)):
            Time = 0
            Time += float(InputList[i][0:2])*3600       # hours
            Time += float(InputList[i][3:5])*60         # minutes
            Time += float(InputList[i][6:8])            # seconds
            Time += float(InputList[i][9:])/1000        # milliseconds
            DataList.append(Time)
            if (i != 0):
                DataList[i] -= DataList[0]
        DataList[0] = 0
    return DataList

def dfToDataTable(df):
    df = df.rename(columns={'index': ''})
    data = df.to_dict('rows')
    columns = [{"name": i, "id": i,} for i in (df.columns)]
    style = [{"if": {"column_id": ''}, 
                "fontWeight": "bold",}]
    table = dash_table.DataTable(
                                    data=data, 
                                    columns=columns, 
                                    style_data_conditional=style, 
                                    style_header={'fontWeight': 'bold'}
                                )
    return table

def PrintModeTable(inputList):
    PrintModeList = ["Print Modes"]
    PrintModeKeys = []
    PrintModeKeys.append("Printer Type: ")          # Printer Type  
    PrintModeKeys.append("Projection Mode: ")       # Projection Mode
    PrintModeKeys.append("Motion Mode: ")           # Motion Mode 
    PrintModeKeys.append("Pumping: ")               # Pumping Mode

    for i in range(0,len(PrintModeKeys)):
        PrintModeList.append(ExtractStringData(inputList,PrintModeKeys[i],0,"str")) 
    
    ModeTable = GenerateTable(PrintModeList, PrintModeKeys, False)
    return ModeTable

def GeneralTable(inputList):
    GeneralSettingsList = ["General Settings"]
    GeneralKeys = []
    GeneralKeys.append("Max Image Upload: ")      # POTF Max Image Upload
    GeneralKeys.append("Resync Rate: ")           # VP Resync Rate
    GeneralKeys.append("Bit Depth: ")             # Bit Depth
    GeneralKeys.append("Starting Position: ")     # Starting Position
    GeneralKeys.append("Layer Thickness: ")       # Layer Thickness

    for i in range(0,len(GeneralKeys)):
        GeneralSettingsList.append(ExtractStringData(inputList, GeneralKeys[i],0,"str"))

    GeneralTable = GenerateTable(GeneralSettingsList, GeneralKeys, False)
    return GeneralTable

def LightEngineTable(inputList):
    LightEngineSettingsList = ["Light Engine"]
    LightEngineKeys = []
    LightEngineKeys.append("Initial Exposure Time: ")     # Initial Exposure Time
    LightEngineKeys.append("Initial Exposure Delay: ")    # Initial Exposure Delay
    LightEngineKeys.append("Initial Exposure Intensity: ")# Initial Exposure Intensity
    LightEngineKeys.append("Exposure Time: ")             # Exposure Time
    LightEngineKeys.append("UV Intensity: ")              # UV Intensity
    LightEngineKeys.append("Dark Time: ")                 # Dark Time

    for i in range(0,len(LightEngineKeys)):
        LightEngineSettingsList.append(ExtractStringData(inputList, LightEngineKeys[i],0,"str"))
    
    LightTable = GenerateTable(LightEngineSettingsList, LightEngineKeys, False)
    return LightTable

def StageTable(inputList):
    StageSettingsList = ["Stage"]
    StageKeys = []
    StageKeys.append("Pump Height: ")             # Pump Height
    StageKeys.append("Stage Velocity: ")          # Stage Velocity
    StageKeys.append("Stage Acceleration: ")      # Stage Acceleration
    StageKeys.append("Max End of Run: ")          # Max End of Run
    StageKeys.append("Min End of Run: ")          # Min End of Run

    for i in range(0,len(StageKeys)):
        StageSettingsList.append(ExtractStringData(inputList,StageKeys[i],0,"str"))

    StageTable = GenerateTable(StageSettingsList, StageKeys, False)
    return StageTable

def InjectionTable(inputList):
    InjectionSettingsList = ["Injection"]
    InjectionKeys = []
    InjectionKeys.append("Injection Volume: ")         # Injection Volume
    InjectionKeys.append("Injection Rate: ")           # Injection Rate
    InjectionKeys.append("Initial Injection Volume: ") # Initial Injection Volume
    InjectionKeys.append("Pre-Injection Delay: ")      # Pre-Injection Delay
    InjectionKeys.append("Post-Injection Delay: ")     # Post-Injection Delay
    InjectionKeys.append("Continuous Injection: ")     # Continuous Injection
    InjectionKeys.append("Base Injection Rate: ")      # Base Injection Rate

    nullCount = 0
    for i in range(0,len(InjectionKeys)):
        String = ExtractStringData(inputList,InjectionKeys[i],0,"str")
        InjectionSettingsList.append(String)
        if(String == []):
            nullCount += 1

    if(nullCount >= len(InjectionKeys)):
        InjectionTable = GenerateTable(InjectionSettingsList, InjectionKeys, True)
    else:
        InjectionTable = GenerateTable(InjectionSettingsList, InjectionKeys, False)
    return InjectionTable



@app.callback(
    [
        Output("resinText", "children"),
        Output("layerText", "children"),
        Output("heightText", "children"),
        Output("timeText", "children"),
    ],
    [
        Input("input_data", "data"),
        Input('upload-data', 'filename'),
    ],
)
def update_text(input_data, filename):
    if (input_data):
        # image name
        resin = ExtractStringData(input_data[:200], "Resin: ", 0, "str")
        #resin = "No Resin Selected"

        # layer count
        count = ExtractStringData(input_data[len(input_data)-50:], "Layer ", 0, "float")
        layers = "%d" %(max(count))

        # build height
        layerHeights = ExtractStringData(input_data[PrintStart:], "Moving Stage: ", 3, "float")
        height = "%d um" %(sum(layerHeights))

        # total time
        ExpEndList = ExtractStringData(input_data[PrintStart:],  "Exp. end: ", 0, "str")
        timeList = list(CalcTotalTime(ExpEndList))
        time = timeList[len(timeList)-1] - timeList[0]
        min, sec = divmod(time, 60)
        hour, min = divmod(min, 60)
        totalTime = "%d:%02d:%02d" % (hour, min, sec)
        #"ExpEndList[len(ExpEndList)] - ExpEndList[0]

        return [resin, layers, height, totalTime]
    else:
        return "","","",""
        #return data[0] + " mcf", data[1] + " bbl", data[2] + " bbl", data[0]

# Callback for file name
@app.callback(
    Output("log-name", "children"),
    [Input('upload-data', 'filename')]
)
def GetLogName(filename):
    if (filename):
        outputName = filename
    else:
        outputName = ""
    return outputName

# Callback for slice image location
@app.callback(
    Output("image-location", "children"),
    [Input("input_data", "data")],
)
def getImageLoc(input_data):
    if(input_data):
        EndPoint = getTestKeyLoc(input_data, "Entering Printing Procedure")
        imageloc = ExtractStringData(input_data[:EndPoint], "C:/", 0, "str")
        splitimage = imageloc[0].split('/')
        location = "/".join(splitimage[len(splitimage)-4:])
    else:
        location = ""
    return location


# Callback for input data
@app.callback(
    Output("input_data", "data"),
    [Input('upload-data', 'contents'),
     Input('Example_Data', "n_clicks")],
)
def txtToList(contents, nClicks):
    outputList = []
    if contents:
        outputList = parseContents(contents ,0)
    elif (nClicks > 0):
        data = urllib.request.urlopen("https://raw.githubusercontent.com/TimSamuelsen/LogAnalysis/master/ExampleLog.txt").read().decode('cp1252')
        outputList = parseContents(data, 1)

    return outputList

#Test callback for text box
@app.callback(
    Output('textarea-example', 'value'),
    [Input('input_data', 'data')]
)
def RawTextBox(data):
    if data:
        output = "List length: %d" %(len(data))
        #stagePos = ExtractStringData(data[PrintStart:], "Stage is currently at: ", 3, "string")
        #output = ",".join(stagePos)
        #output = "Print start: %d" %(PrintStart) 
        return output
    else:
        return 'No log file selected'

# Print modes table
@app.callback(
    Output('mode_table', 'children'),
    [Input("input_data", "data")],
)
def modeTable(input_data):
    if(input_data):
        EndPoint = getTestKeyLoc(input_data, "Entering Printing Procedure")
        df = PrintModeTable(input_data[:EndPoint]).reset_index()
        return dfToDataTable(df)

# General settings table
@app.callback(
    Output('general_table', 'children'),
    [Input("input_data", "data")],
)
def modeTable(input_data):
    if(input_data):
        EndPoint = getTestKeyLoc(input_data, "Entering Printing Procedure")
        df = GeneralTable(input_data[:EndPoint]).reset_index()
        return dfToDataTable(df)

# Stage table
@app.callback(
    Output('stage_table', 'children'),
    [Input("input_data", "data")],
)
def modeTable(input_data):
    if(input_data):
        EndPoint = getTestKeyLoc(input_data, "Entering Printing Procedure")
        df = StageTable(input_data[:EndPoint]).reset_index()
        return dfToDataTable(df)

# Light Engine table
@app.callback(
    Output('light_table', 'children'),
    [Input("input_data", "data")],
)
def modeTable(input_data):
    if(input_data):
        EndPoint = getTestKeyLoc(input_data, "Entering Printing Procedure")
        df = LightEngineTable(input_data[:EndPoint]).reset_index()
        return dfToDataTable(df)

# Injection table
@app.callback(
    Output('injection_table', 'children'),
    [Input("input_data", "data")],
)
def modeTable(input_data):
    if(input_data):
        EndPoint = getTestKeyLoc(input_data, "Entering Printing Procedure")
        df = InjectionTable(input_data[:EndPoint]).reset_index()
        return dfToDataTable(df)

# Selectors, main graph -> pie graph
@app.callback(
    Output("ps_graph", "figure"),
    [
        Input('input_data', 'data')
    ],
)
def make_pie_figure(input_data):
    EndPoint = getTestKeyLoc(input_data, "Entering Printing Procedure")
    layout_ps = copy.deepcopy(layoutGO)
    fig = make_subplots(
        rows=1, cols=2,
        column_widths=[0.5, 0.5],
        specs=[[{"type": "scatter"}, {"type": "scatter"}]],
        subplot_titles = ['Exposure & Dark Time', 
                        'Layer Thickness'],
    )

    ExpTime = ExtractStringData(input_data[EndPoint:], "Exposure: ", 3, "float")
    fig.add_trace(
        dict(
            type="scatter",
            mode="lines",
            name="Exposure Time",
            x=list(range(0,len(ExpTime))),
            y=ExpTime,
            line=dict(shape="spline", smoothing=0, color="#F9ADA0"),
        ),
        row=1, col=1
    )

    DarkTime = ExtractStringData(input_data[EndPoint:], "Dark Time: ", 3, "float")
    fig.add_trace(
        dict(
            type="scatter",
            mode="lines",
            name="Dark Time",
            x=list(range(0,len(DarkTime))),
            y=DarkTime,
            line=dict(shape="spline", smoothing=0, color="#849E68"),
        ),
        row=1, col=1
    )

    LayerThickness = ExtractStringData(input_data[EndPoint:], "Moving Stage: ", 3,"float")
    fig.add_trace(
        dict(
            type="scatter",
            mode="lines",
            name="Layer Thickness",
            x=list(range(0,len(LayerThickness))),
            y=LayerThickness,
            line=dict(shape="spline", smoothing=0, color="#59C3C3"),
            
        ),
        row=1, col=2
    )




    fig.update_layout(layout_ps)
    fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='#E9E9E9', color='#A0A0A0')
    fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='#E9E9E9', color='#A0A0A0')
    
    fig.update_xaxes(title_text="Layer #", row=1, col=1)
    fig.update_xaxes(title_text="Layer #", row=1, col=2)
    fig.update_yaxes(title_text="Time (ms)", row=1, col=1)
    fig.update_yaxes(title_text="Layer Thickness (um)", row=1, col=2)

    fig.update_layout(plot_bgcolor="#F9F9F9", paper_bgcolor="#F9F9F9")
    
    return fig

# Stage graph
@app.callback(
    Output("stage_graph", "figure"),
    [Input("input_data", "data")],
)
def make_stage_figure(input_data):

    layout_stagePos = copy.deepcopy(layout)
    stagePos = ExtractStringData(input_data[PrintStart:], "Stage is currently at: ", 3, "float")
    ExpEndList = ExtractStringData(input_data[PrintStart:],  "Exp. end: ", 0, "str")
    time = list(CalcTotalTime(ExpEndList))
    if (len(ExpEndList) > len(stagePos)):
        diff = len(ExpEndList) - len(stagePos)
        ExpEndList = ExpEndList[diff:]
    elif (len(stagePos) > len(ExpEndList)):
        diff = len(stagePos) - len(ExpEndList)
        stagePos = stagePos[diff:]

    data = [
        dict(
            type="scatter",
            mode="lines",
            name="Stage Position",

            x=time,#list(range(0,len(stagePos))),
            y=stagePos,
            line=dict(shape="spline", smoothing="2", color="#F9ADA0"),
        ),
    ]
    layout_stagePos["title"] = "Stage Position vs. Time"
    layout_stagePos["showlegend"] = True
    layout_stagePos["margin"]=dict(l=55, r=30, b=20, t=40)
    layout_stagePos["xaxis"] = {"title": "Time (s)"}
    layout_stagePos["yaxis"] = {"title": "Stage Position (mm)"}

    figure = dict(data=data, layout=layout_stagePos)
    return figure

# Main
if __name__ == "__main__":
    app.run_server(debug=True)