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

# Multi-dropdown options
from controls import COUNTIES, WELL_STATUSES, WELL_TYPES, WELL_COLORS


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

# Create controls
county_options = [
    {"label": str(COUNTIES[county]), "value": str(county)} for county in COUNTIES
]

well_status_options = [
    {"label": str(WELL_STATUSES[well_status]), "value": str(well_status)}
    for well_status in WELL_STATUSES
]

well_type_options = [
    {"label": str(WELL_TYPES[well_type]), "value": str(well_type)}
    for well_type in WELL_TYPES
]


# Download pickle file
urllib.request.urlretrieve(
    "https://raw.githubusercontent.com/plotly/datasets/master/dash-sample-apps/dash-oil-and-gas/data/points.pkl",
    DATA_PATH.joinpath("points.pkl"),
)
points = pickle.load(open(DATA_PATH.joinpath("points.pkl"), "rb"))


# Load data
df = pd.read_csv(
    "https://github.com/plotly/datasets/raw/master/dash-sample-apps/dash-oil-and-gas/data/wellspublic.csv",
    low_memory=False,
)
df["Date_Well_Completed"] = pd.to_datetime(df["Date_Well_Completed"])
df = df[df["Date_Well_Completed"] > dt.datetime(1960, 1, 1)]

trim = df[["API_WellNo", "Well_Type", "Well_Name"]]
trim.index = trim["API_WellNo"]
dataset = trim.to_dict(orient="index")


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
        dcc.Store(id="aggregate_data"),
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
                                "margin-bottom": "15px",
                            },
                        )
                    ],
                    className="one-third column",
                ),
                html.Div(
                    [
                        html.Div(
                            [
                                html.H3(
                                    "CLIP3D Print Log Analysis",
                                    style={"margin-bottom": "15px"},
                                ),
                            ]
                        )
                    ],
                    className="one-half column",
                    id="title",
                ),
                html.Div(
                    [
                        html.A(
                            html.Button("Learn More", id="learn-more-button"),
                            href="https://plot.ly/dash/pricing/",
                        )
                    ],
                    className="one-third column",
                    id="button",
                ),
            ],
            id="header",
            className="row flex-display",
            style={"margin-bottom": "25px"},
        ),
        html.Div(
            [
                html.Div(
                    [
                        html.Div(
                            className="padding-top-bot",
                            children=[
                                html.H6("Upload Print Log"),
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
                        html.P(
                            "Selected File:",
                            className="filename_label",
                        ),
                        html.P(
                            id="log-name"
                        ),
                        html.P(
                            "Filter by construction date (or select range in histogram):",
                            className="control_label",
                        ),
                        dcc.RangeSlider(
                            id="year_slider",
                            min=1960,
                            max=2017,
                            value=[1990, 2010],
                            className="dcc_control",
                        ),
                        html.P("Filter by well status:", className="control_label"),
                        dcc.RadioItems(
                            id="well_status_selector",
                            options=[
                                {"label": "All ", "value": "all"},
                                {"label": "Active only ", "value": "active"},
                                {"label": "Customize ", "value": "custom"},
                            ],
                            value="active",
                            labelStyle={"display": "inline-block"},
                            className="dcc_control",
                        ),
                        dcc.Dropdown(
                            id="well_statuses",
                            options=well_status_options,
                            multi=True,
                            value=list(WELL_STATUSES.keys()),
                            className="dcc_control",
                        ),
                        dcc.Checklist(
                            id="lock_selector",
                            options=[{"label": "Lock camera", "value": "locked"}],
                            className="dcc_control",
                            value=[],
                        ),
                        html.P("Filter by well type:", className="control_label"),
                        dcc.RadioItems(
                            id="well_type_selector",
                            options=[
                                {"label": "All ", "value": "all"},
                                {"label": "Productive only ", "value": "productive"},
                                {"label": "Customize ", "value": "custom"},
                            ],
                            value="productive",
                            labelStyle={"display": "inline-block"},
                            className="dcc_control",
                        ),
                        dcc.Dropdown(
                            id="well_types",
                            options=well_type_options,
                            multi=True,
                            value=list(WELL_TYPES.keys()),
                            className="dcc_control",
                        ),
                    ],

                    className="pretty_container three columns",
                    id="cross-filter-options",
                ),
                html.Div(
                    [
                        html.Div(
                            [
                                html.Div(
                                    [html.P(id="sliceText"), html.P("Slice Image Location")],
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
        ),
        html.Div(
            [
                html.Div(
                    [dcc.Graph(id="main_graph")],
                    className="pretty_container seven columns",
                ),
                html.Div(
                    [dcc.Graph(id="individual_graph")],
                    className="pretty_container five columns",
                ),
            ],
            className="row flex-display",
        ),
        html.Div(
            [
                html.Div(
                    [dcc.Graph(id="pie_graph")],
                    className="pretty_container seven columns",
                ),
                html.Div(
                    [dcc.Graph(id="aggregate_graph")],
                    className="pretty_container five columns",
                ),
            ],
            className="row flex-display",
        ),
        dcc.Textarea(
            id='textarea-example',
            value='Textarea content initialized\nwith multiple lines of text',
            style={'width': '100%', 'height': 300},
        ),
        html.Div(id='textarea-example-output', style={'whiteSpace': 'pre-line'}),
        html.Div(
                            [dcc.Graph(id="count_graph")],
                            id="countGraphContainer",
                            className="pretty_container",
                        ),
    ],
    id="mainContainer",
    style={"display": "flex", "flex-direction": "column"},
)


# Helper functions
def human_format(num):
    if num == 0:
        return "0"

    magnitude = int(math.log(num, 1000))
    mantissa = str(int(num / (1000 ** magnitude)))
    return mantissa + ["", "K", "M", "G", "T", "P"][magnitude]


def filter_dataframe(df, well_statuses, well_types, year_slider):
    dff = df[
        df["Well_Status"].isin(well_statuses)
        & df["Well_Type"].isin(well_types)
        & (df["Date_Well_Completed"] > dt.datetime(year_slider[0], 1, 1))
        & (df["Date_Well_Completed"] < dt.datetime(year_slider[1], 1, 1))
    ]
    return dff


def produce_individual(api_well_num):
    try:
        points[api_well_num]
    except:
        return None, None, None, None

    index = list(
        range(min(points[api_well_num].keys()), max(points[api_well_num].keys()) + 1)
    )
    gas = []
    oil = []
    water = []

    for year in index:
        try:
            gas.append(points[api_well_num][year]["Gas Produced, MCF"])
        except:
            gas.append(0)
        try:
            oil.append(points[api_well_num][year]["Oil Produced, bbl"])
        except:
            oil.append(0)
        try:
            water.append(points[api_well_num][year]["Water Produced, bbl"])
        except:
            water.append(0)

    return index, gas, oil, water


def produce_aggregate(selected, year_slider):

    index = list(range(max(year_slider[0], 1985), 2016))
    gas = []
    oil = []
    water = []

    for year in index:
        count_gas = 0
        count_oil = 0
        count_water = 0
        for api_well_num in selected:
            try:
                count_gas += points[api_well_num][year]["Gas Produced, MCF"]
            except:
                pass
            try:
                count_oil += points[api_well_num][year]["Oil Produced, bbl"]
            except:
                pass
            try:
                count_water += points[api_well_num][year]["Water Produced, bbl"]
            except:
                pass
        gas.append(count_gas)
        oil.append(count_oil)
        water.append(count_water)

    return index, gas, oil, water

def parseContents(contents):
    stringlist = []
    if contents:
        content_type, content_string = contents.split(",")
        
        decoded = base64.b64decode(content_string)
        string = str(decoded, 'cp1252')

        decodedlist = decoded.split(b'\r\n')
        for i in range(1, len(decodedlist)):
            stringlist.append(str(decodedlist[i], 'cp1252'))
        
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

# Create callbacks
#app.clientside_callback(
#    ClientsideFunction(namespace="clientside", function_name="resize"),
#    Output("output-clientside", "children"),
#    [Input("count_graph", "figure")],
#)


@app.callback(
    Output("aggregate_data", "data"),
    [
        Input("well_statuses", "value"),
        Input("well_types", "value"),
        Input("year_slider", "value"),
    ],
)
def update_production_text(well_statuses, well_types, year_slider):

    dff = filter_dataframe(df, well_statuses, well_types, year_slider)
    selected = dff["API_WellNo"].values
    index, gas, oil, water = produce_aggregate(selected, year_slider)
    return [human_format(sum(gas)), human_format(sum(oil)), human_format(sum(water))]


# Radio -> multi
@app.callback(
    Output("well_statuses", "value"), [Input("well_status_selector", "value")]
)
def display_status(selector):
    if selector == "all":
        return list(WELL_STATUSES.keys())
    elif selector == "active":
        return ["AC"]
    return []


# Radio -> multi
@app.callback(Output("well_types", "value"), [Input("well_type_selector", "value")])
def display_type(selector):
    if selector == "all":
        return list(WELL_TYPES.keys())
    elif selector == "productive":
        return ["GD", "GE", "GW", "IG", "IW", "OD", "OE", "OW"]
    return []


# Slider -> count graph
@app.callback(Output("year_slider", "value"), [Input("count_graph", "selectedData")])
def update_year_slider(count_graph_selected):

    if count_graph_selected is None:
        return [1990, 2010]

    nums = [int(point["pointNumber"]) for point in count_graph_selected["points"]]
    return [min(nums) + 1960, max(nums) + 1961]

@app.callback(
    [
        Output("sliceText", "children"),
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
        EndPoint = getTestKeyLoc(input_data, "Entering Printing Procedure")
        imageloc = ExtractStringData(input_data[:EndPoint], "C:/", 0, "str")
        splitimage = imageloc[0].split('/')
        image = "/".join(splitimage[len(splitimage)-3:])

        # layer count
        count = ExtractStringData(input_data[len(input_data)-50:], "Layer ", 0, "float")
        layers = "%d" %(max(count))

        # build height
        layerHeights = ExtractStringData(input_data[PrintStart:], "Moving Stage: ", 3, "float")
        height = "%d mm" %(sum(layerHeights)/1000)

        # total time
        ExpEndList = ExtractStringData(input_data[PrintStart:],  "Exp. end: ", 0, "str")
        timeList = list(CalcTotalTime(ExpEndList))
        time = timeList[len(timeList)-1] - timeList[0]
        min, sec = divmod(time, 60)
        hour, min = divmod(min, 60)
        totalTime = "%d:%02d:%02d" % (hour, min, sec)
        #"ExpEndList[len(ExpEndList)] - ExpEndList[0]

        return [image, layers, height, totalTime]
    else:
        return "","","",""
        #return data[0] + " mcf", data[1] + " bbl", data[2] + " bbl", data[0]


# Selectors -> main graph
@app.callback(
    Output("main_graph", "figure"),
    [
        Input("well_statuses", "value"),
        Input("well_types", "value"),
        Input("year_slider", "value"),
    ],
    [State("lock_selector", "value"), State("main_graph", "relayoutData")],
)
def make_main_figure(
    well_statuses, well_types, year_slider, selector, main_graph_layout
):

    dff = filter_dataframe(df, well_statuses, well_types, year_slider)

    traces = []
    for well_type, dfff in dff.groupby("Well_Type"):
        trace = dict(
            type="scattermapbox",
            lon=dfff["Surface_Longitude"],
            lat=dfff["Surface_latitude"],
            text=dfff["Well_Name"],
            customdata=dfff["API_WellNo"],
            name=WELL_TYPES[well_type],
            marker=dict(size=4, opacity=0.6),
        )
        traces.append(trace)

    # relayoutData is None by default, and {'autosize': True} without relayout action
    if main_graph_layout is not None and selector is not None and "locked" in selector:
        if "mapbox.center" in main_graph_layout.keys():
            lon = float(main_graph_layout["mapbox.center"]["lon"])
            lat = float(main_graph_layout["mapbox.center"]["lat"])
            zoom = float(main_graph_layout["mapbox.zoom"])
            layout["mapbox"]["center"]["lon"] = lon
            layout["mapbox"]["center"]["lat"] = lat
            layout["mapbox"]["zoom"] = zoom

    figure = dict(data=traces, layout=layout)
    return figure


# Main graph -> individual graph
@app.callback(Output("individual_graph", "figure"), [Input("main_graph", "hoverData")])
def make_individual_figure(main_graph_hover):

    layout_individual = copy.deepcopy(layout)

    if main_graph_hover is None:
        main_graph_hover = {
            "points": [
                {"curveNumber": 4, "pointNumber": 569, "customdata": 31101173130000}
            ]
        }

    chosen = [point["customdata"] for point in main_graph_hover["points"]]
    index, gas, oil, water = produce_individual(chosen[0])

    if index is None:
        annotation = dict(
            text="No data available",
            x=0.5,
            y=0.5,
            align="center",
            showarrow=False,
            xref="paper",
            yref="paper",
        )
        layout_individual["annotations"] = [annotation]
        data = []
    else:
        data = [
            dict(
                type="scatter",
                mode="lines+markers",
                name="Gas Produced (mcf)",
                x=index,
                y=gas,
                line=dict(shape="spline", smoothing=2, width=1, color="#fac1b7"),
                marker=dict(symbol="diamond-open"),
            ),
            dict(
                type="scatter",
                mode="lines+markers",
                name="Oil Produced (bbl)",
                x=index,
                y=oil,
                line=dict(shape="spline", smoothing=2, width=1, color="#a9bb95"),
                marker=dict(symbol="diamond-open"),
            ),
            dict(
                type="scatter",
                mode="lines+markers",
                name="Water Produced (bbl)",
                x=index,
                y=water,
                line=dict(shape="spline", smoothing=2, width=1, color="#92d8d8"),
                marker=dict(symbol="diamond-open"),
            ),
        ]
        layout_individual["title"] = dataset[chosen[0]]["Well_Name"]

    figure = dict(data=data, layout=layout_individual)
    return figure


# Selectors, main graph -> pie graph
@app.callback(
    Output("pie_graph", "figure"),
    [
        Input('input_data', 'data')
    ],
)
def make_pie_figure(input_data):
    EndPoint = getTestKeyLoc(input_data, "Entering Printing Procedure")
    fig = make_subplots(
        rows=1, cols=2,
        column_widths=[0.5, 0.5],
        specs=[[{"type": "scatter"}, {"type": "scatter"}]],
        subplot_titles = ['Exposure Time', 
                        'Layer Thickness']
    )


    ExpTime = ExtractStringData(input_data[EndPoint:], "Exposure: ", 3, "float")
    fig.add_trace(
        go.Scatter(x=list(range(0,len(ExpTime))), y=ExpTime,
                showlegend = False),
        row=1, col=1
    )

    DarkTime = ExtractStringData(input_data[EndPoint:], "Dark Time: ", 3, "float")
    fig.add_trace(
        go.Scatter(x=list(range(0,len(DarkTime))), y=DarkTime, 
                showlegend = False),
        row=1, col=1
    )

    LayerThickness = ExtractStringData(input_data[EndPoint:], "Moving Stage: ", 3,"float")
    fig.add_trace(
        go.Scatter(x=list(range(0,len(LayerThickness))), y=LayerThickness,
                showlegend = False),
        row=1, col=2
    )
    return fig


# Selectors -> count graph
@app.callback(
    Output("count_graph", "figure"),
    [
        Input("well_statuses", "value"),
        Input("well_types", "value"),
        Input("year_slider", "value"),
    ],
)
def make_count_figure(well_statuses, well_types, year_slider):

    layout_count = copy.deepcopy(layout)

    dff = filter_dataframe(df, well_statuses, well_types, [1960, 2017])
    g = dff[["API_WellNo", "Date_Well_Completed"]]
    g.index = g["Date_Well_Completed"]
    g = g.resample("A").count()

    colors = []
    for i in range(1960, 2018):
        if i >= int(year_slider[0]) and i < int(year_slider[1]):
            colors.append("rgb(123, 199, 255)")
        else:
            colors.append("rgba(123, 199, 255, 0.2)")

    data = [
        dict(
            type="scatter",
            mode="markers",
            x=g.index,
            y=g["API_WellNo"] / 2,
            name="All Wells",
            opacity=0,
            hoverinfo="skip",
        ),
        dict(
            type="bar",
            x=g.index,
            y=g["API_WellNo"],
            name="All Wells",
            marker=dict(color=colors),
        ),
    ]

    layout_count["title"] = "Completed Wells/Year"
    layout_count["dragmode"] = "select"
    layout_count["showlegend"] = False
    layout_count["autosize"] = True

    figure = dict(data=data, layout=layout_count)
    return figure



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

# Callback for input data
@app.callback(
    Output("input_data", "data"),
    [Input('upload-data', 'contents')]
)
def txtToList(contents):
    outputList = []
    if contents:
        outputList = parseContents(contents)
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

#Selectors, main graph -> aggregate graph
@app.callback(
    Output("aggregate_graph", "figure"),
    [Input("input_data", "data")],
)
def make_aggregate_figure(input_data):

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


# Testing graph
# @app.callback(
#     Output("aggregate_graph", "figure"),
#     [Input('input_data', 'data')],
# )
# def updateStagePosGraph(data):
#     df = px.data.iris()
#     fig = px.scatter(df, x="sepal_width", y="sepal_length", color="species", symbol="species")
#     #return fig
#     #test=1
#     if data:
#         test=1
#         layout_StagePos = copy.deepcopy(layout)

#         stagePos = ExtractStringData(data[PrintStart:], "Stage is currently at: ", 3, "float")
#         ExpEndList = ExtractStringData(data,  "Exp. end: ", 0, "str")
#         time = list(CalcTotalTime(ExpEndList))
#         time = range(0,len(stagePos))

#         data = px.scatter(df, x="sepal_width", y="sepal_length", color="species", symbol="species")
#         #data = [
#         #    dict(
#         #        type="scatter",
#         #        mode="lines",
#         #        name="Gas Produced (mcf)",
#         #        x=list(time),
#         #        y=stagePos,
#         #        line=dict(shape="spline", smoothing="2", color="#F9ADA0"),
#         #    )
#         #]
#         fig = go.Figure(
#             data=[go.Bar(x=[1, 2, 3], y=[1, 3, 2])]
#         )
#         return fig



#MY TEST CALLBACK
#@app.callback(
#    Output("aggregate_graph", "figure"),
#    Input('upload-data', 'contents'),
#    State('upload-data', 'filename'),
#    State('upload-data', 'last_modified')
#)
#def updatePosTimeGraph(contents, filename, last_modified):

#    return 0