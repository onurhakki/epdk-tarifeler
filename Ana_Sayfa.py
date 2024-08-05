import streamlit as st
import pandas as pd
import numpy as np
import streamlit.components.v1 as components
from utils import QueryData, plot_compare

import numpy as np
def normal_close(close):
    return np.log(close.div(close.shift(1))).cumsum().apply(np.exp).fillna(1)


@st.cache_data
def load_data():
    q = QueryData()
    given_columns = q.tarifeler_liste[~q.tarifeler_liste["id"].duplicated(keep="last")]
    columns_dict = given_columns[["Ad","id", "pre_id"]].set_index("Ad").T.to_dict()
    df = q.tarifeler.merge(q.tarifeler_liste[["Gerilim", "Terim", "Kullanıcı", "id", "pre_id"]], on = ["Gerilim", "Terim", "Kullanıcı"])

    avoid = set(v["pre_id"] for v in columns_dict.values() if v["pre_id"] != "-")
    avoid = [int(i) for i in avoid]
    columns_dict = {k:v for k,v in columns_dict.items() if v["id"] not in avoid}

    storage = list()
    for k,v in columns_dict.items():
        selected = df.query(
        f"id == {v['id']}"
        if v['pre_id'] == "-" else
        f"id == {v['id']} or id == {v['pre_id']}"
        ).sort_values("Tarih").set_index("Tarih")
        selected["Ad"] = k
        storage.append(selected[[
            "Ad", 
            "Perakende Tek Zamanlı Enerji Bedeli",
            "Perakende Gündüz Enerji Bedeli",
            "Perakende Puant Enerji Bedeli",
            "Perakende Gece Enerji Bedeli",
            "Dağıtım Bedeli"
            ]])

    compare = pd.concat(storage).reset_index().set_index(["Tarih", "Ad"])

    return df, given_columns, columns_dict, compare

st.set_page_config(
    page_title="EPDK Tarifeler",
    page_icon=":bar_chart:",
    layout="wide",
)

st.markdown("## EPDK Toplu Tarifeler ")

df, given_columns, columns_dict, compare = load_data()

columns = st.selectbox("Tarifeler (Tek zamanlı tarife, üç zamanlı tarife ve dağıtım bedeli)",[
    ['Perakende Tek Zamanlı Enerji Bedeli'],
    ['Perakende Gündüz Enerji Bedeli'], 
    ['Perakende Puant Enerji Bedeli'],
    ['Perakende Gece Enerji Bedeli'],
    ["Dağıtım Bedeli"],
    ['Perakende Tek Zamanlı Enerji Bedeli', "Dağıtım Bedeli"],
    ['Perakende Gündüz Enerji Bedeli', "Dağıtım Bedeli"], 
    ['Perakende Puant Enerji Bedeli', "Dağıtım Bedeli"],
    ['Perakende Gece Enerji Bedeli', "Dağıtım Bedeli"],
], index = 5)


option = st.sidebar.selectbox("Seçenekler",["Birim Fiyat", "Yüzde", "Normal"])

birim_columns = st.sidebar.columns((1,2))
with birim_columns[0]:
    birim = st.checkbox("Birim:", False)
with birim_columns[1]:
    if birim:
        birim_name = "TL/MWh"
        st.write("TL/MWh")
        compare = compare.multiply(10)
    else:
        birim_name = "kr/kWh"

        st.write("kr/kWh")

if len(columns) == 1:
    export = compare[columns[0]].unstack("Tarih")
    export.columns = [i.split()[0] for i in export.columns]
    if option == "Yüzde":
        export = export.pct_change(axis = 1).multiply(100).dropna(axis = 1, how = "all")
    if option == "Normal":
        export = export.dropna(axis = 1, how = "all").T
        export = normal_close(export).T

    
if len(columns) == 2:
    export = compare[columns].sum(axis = 1).unstack("Tarih")
    export.columns = [i.split()[0] for i in export.columns]
    if option == "Yüzde":
        export = export.pct_change(axis = 1).multiply(100).dropna(axis = 1, how = "all")
    if option == "Normal":
        export = export.dropna(axis = 1, how = "all").T
        export = normal_close(export).T
    
fres = export.style.format(precision=2, thousands=".",decimal=",").background_gradient("RdYlGn_r",axis = None)
st.dataframe(fres, use_container_width=True, height=len(export)*40)

st.markdown("### Görselleştirme")
seçilenler = st.multiselect("Tarife grubu seçiniz. (Maks. : 6 adet)", export.index, 
                            [
                                # 'Aydınlatma | Tek | AG', 
                                # 'Aydınlatma | Tek | OG',
                                # 'Aydınlatma | Çift | OG', 'Genel Aydınlatma | Tek | AG',
       'Kamu ve Özel Hizmetler Sektörü ile Diğer (30 kWh/gün ve altı) | Tek | AG',
       'Kamu ve Özel Hizmetler Sektörü ile Diğer (30 kWh/gün üstü) | Tek | AG',
    #    'Kamu ve Özel Hizmetler Sektörü ile Diğer | Tek | OG',
    #    'Kamu ve Özel Hizmetler Sektörü ile Diğer | Çift | OG',
       'Mesken (8 kWh/gün ve altı) | Tek | AG',
       'Mesken (8 kWh/gün üstü) | Tek | AG', 
    #    'Mesken | Tek | OG',
    #    'Mesken | Çift | OG', 
       'Sanayi | Tek | AG', 
    #    'Sanayi | Tek | OG',
    #    'Sanayi | Çift | OG', 
       'Tarımsal Faaliyetler | Tek | AG',
    #    'Tarımsal Faaliyetler | Tek | OG', 
    #    'Tarımsal Faaliyetler | Çift | OG',
    #    'İletim | - | YG',
    #    'Şehit Aileleri ve Muharip Malul Gaziler | Tek | AG'
                            ], max_selections=6, )
if len(seçilenler) != 0:
    fig = plot_compare(export.loc[seçilenler].T, birim_name)
    st.plotly_chart(fig, use_container_width=True)



## Footer
st.markdown("## ")
st.markdown("## ")
HtmlFile = open("./footer.html", 'r', encoding='utf-8')
footer = HtmlFile.read() 
components.html(footer, height = 400)
