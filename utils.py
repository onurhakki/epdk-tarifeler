
import pandas as pd
import sqlite3
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
import matplotlib.pyplot as plt

cmap = plt.get_cmap('tab20')

def data(table_name = "tarifeler.db"
):
    df = pd.read_excel("tarifeler.xlsx")
    # tarife_list = df.groupby(["Gerilim", "Terim", "Kullanıcı", ])["Tarih"].agg({"min","max"}).rename(columns = {"min":"İlk Tarih","max":"Son Tarih"}).reset_index()
    listeler = pd.read_excel("tarife-eşleşme.xlsx").iloc[:,1:]
    
    conn = sqlite3.connect(table_name)
    df.to_sql("tarifeler", conn, if_exists="replace", index = False)
    listeler.to_sql("tarife_liste", conn, if_exists="replace", index = False)
    conn.close()


class QueryData():
    table = 'tarifeler.db'
    tarifeler_columns = ['No', 'Kullanıcı', 'Perakende Tek Zamanlı Enerji Bedeli',
       'Perakende Gündüz Enerji Bedeli', 'Perakende Puant Enerji Bedeli',
       'Perakende Gece Enerji Bedeli', 'Dağıtım Bedeli', 'Tek Zamanlı',
       'Gündüz', 'Puant', 'Gece', 'Gerilim', 'Terim', 'Tarih']
    tarifeler_liste_columns = ['Ad', 'İlk Tarih', 'Son Tarih', 'Gerilim', 'Terim', 'Kullanıcı',"id", "pre_id"]
    def __init__(self):
        self.tarifeler = self.load_all("tarifeler")
        self.tarifeler_liste = self.load_all("tarife_liste")

    def load_all(self,table_name):
        if table_name == "tarifeler":
            cols = self.tarifeler_columns
        elif table_name == "tarife_liste":
            cols = self.tarifeler_liste_columns
        else:
            return
        conn = sqlite3.connect(self.table)
        c = conn.cursor()
        c.execute(
            f"""  
            SELECT * FROM {table_name}
            """
        )
        res = pd.DataFrame(c.fetchall(), columns = cols)
        conn.close()
        return res
    

def rgb2hex(x):
    r,g,b = x
    r,g,b = int(r*255),int(g*255),int(b*255)
    return "#{:02x}{:02x}{:02x}".format(r,g,b)


def plot_frame(frame, birim, stepwise):
    fig = make_subplots(
        rows=1, cols=1,
        # subplot_titles=["(TWh)"],
        shared_xaxes=True,
        vertical_spacing = 0.02
        )

    colors = dict()

    text_filter = frame[
                frame.pct_change().abs() > 0.1

        # frame.div(10).round().apply(lambda x: ~x.duplicated())*frame.div(10).round().apply(lambda x: ~x.duplicated(), axis = 1)
        ].fillna(0)

    for th,val in enumerate(frame):
        diff = frame[val].pct_change().multiply(100).fillna(0)
        if val not in colors:
            colors[val] = rgb2hex(cmap(th%20)[:3])

        fig.add_trace(go.Scatter(
            x = frame.index,
            y = frame[val].to_list(),
            hovertemplate= [f'{frame[val].iloc[nth]:,.2f} (%{i:,.2f})'.replace(".","_").replace(",",".").replace("_",",") for nth, i in enumerate(diff.tolist())],
            name= val,
            marker_color=colors[val],
            # {frame[val].iloc[nth]:,.2f} 
            text= [f'(%{diff.iloc[nth]:,.1f})'.replace(".","_").replace(",",".").replace("_",",") if abs(i) >10 else "" for nth, i in enumerate(text_filter[val].tolist())],
            textfont_color= ["red" if i > 0 else "green" for nth, i in enumerate(diff.tolist())],
    textposition="top center" if th == 2 else "bottom center",
        mode="lines+text+markers",
        line_shape = "hv" if stepwise else "linear",


        # width = 500
        ),
        row=1, col=1
        )

    fig.update_yaxes(showline=True, gridcolor='rgb(230,230,230)')
    fig.update_layout(
        dict(
legend=dict(
    orientation="h",
    yanchor="bottom",
    y=1.02,
    xanchor="right",
    x=1
),
yaxis_title = birim,

            xaxis_tickangle=-0,
            xaxis_tickformat = '%Y-%m-%d',
            yaxis_tickformat = ',',
            separators="*..*",

            margin=dict(l=5, r=5, t=75, b=10),
            font_family="arial",
            font_size = 12,
            plot_bgcolor='rgb(255, 255, 255)',
            hovermode = "x unified",
            yaxis1_range=[0,frame.max().max()*1.1],
            # yaxis2_range=[0,frame.pct_change().multiply(100).fillna(0).max().max()*1.1]

)
)


    return fig

def plot_compare(frame, birim, stepwise):
    fig = make_subplots(
        rows=1, cols=1,
        # subplot_titles=["(TWh)"],
        shared_xaxes=True,
        vertical_spacing = 0.02
        )

    colors = dict()

    for th,val in enumerate(frame):
        diff = frame[val].pct_change().multiply(100).fillna(0)
        if val not in colors:
            colors[val] = rgb2hex(cmap(th%20)[:3])

        fig.add_trace(go.Scatter(
            x = frame.index,
            y = frame[val].to_list(),
            hovertemplate= [f'{frame[val].iloc[nth]:,.2f} (%{i:,.2f})'.replace(".","_").replace(",",".").replace("_",",") for nth, i in enumerate(diff.tolist())],
            name= val,
            marker_color=colors[val],
        mode="lines+markers",
        line_shape = "hv" if stepwise else "linear",

        ),
        row=1, col=1
        )

    fig.update_yaxes(showline=True, gridcolor='rgb(230,230,230)')
    fig.update_layout(
        dict(
legend=dict(
    orientation="h",
    yanchor="bottom",
    y=1.02,
    xanchor="right",
    x=1
),

yaxis_title = birim,
            xaxis_tickformat = '%Y-%m-%d',
            yaxis_tickformat = ',',
            separators="*..*",
            margin=dict(l=5, r=5, t=90, b=10),
            font_family="arial",
            font_size = 12,
            plot_bgcolor='rgb(255, 255, 255)',
            hovermode = "x unified",
            yaxis1_range=[frame.min().min()*0.9 if frame.min().min() > 0 else frame.min().min()*1.1,frame.max().max()*1.1],
            # yaxis2_range=[0,frame.pct_change().multiply(100).fillna(0).max().max()*1.1]

)
)


    return fig

