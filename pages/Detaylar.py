import streamlit as st
import pandas as pd
import numpy as np
import streamlit.components.v1 as components

from utils import QueryData, plot_frame

import numpy as np



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


selected_name = st.sidebar.selectbox("Tarifeler", columns_dict.keys())

zaman = st.sidebar.selectbox("Zaman", ["Tek Zamanlı", "Üç Zamanlı"])
if zaman == "Üç Zamanlı":
    periyot = st.sidebar.selectbox("Zaman", ["Gündüz", "Puant", "Gece", "Ortalama"])
else:
    periyot = None

keys = columns_dict[selected_name]
selected = df.query(
    f"id == {keys['id']}"
    if keys['pre_id'] == "-" else
    f"id == {keys['id']} or id == {keys['pre_id']}"
    ).sort_values("Tarih")




if zaman == "Tek Zamanlı":
    columns = ["Tarih", 'Perakende Tek Zamanlı Enerji Bedeli', "Dağıtım Bedeli"]
if zaman == "Üç Zamanlı":
    if periyot == "Gündüz":
        columns = ["Tarih", 'Perakende Gündüz Enerji Bedeli', "Dağıtım Bedeli"]
    elif periyot == "Puant":
        columns = ["Tarih", 'Perakende Puant Enerji Bedeli', "Dağıtım Bedeli"]
    elif periyot == "Gece":
        columns = ["Tarih", 'Perakende Gece Enerji Bedeli', "Dağıtım Bedeli"]
    elif periyot == "Ortalama":
        selected["Perakende Üç Zamanlı Ortalama Enerji Bedeli"] = selected[['Perakende Gündüz Enerji Bedeli', 'Perakende Puant Enerji Bedeli',
           'Perakende Gece Enerji Bedeli']].mean(axis = 1)
        columns = ["Tarih", 'Perakende Üç Zamanlı Ortalama Enerji Bedeli', "Dağıtım Bedeli"]
        
fselected = selected[columns+["Kullanıcı"]].set_index("Tarih")
fselected["Toplam (Perakende+Dağıtım) Enerji Bedeli"] = fselected.iloc[:,:-1].sum(axis = 1)
fselected = fselected[[
    columns[1:][1],
    columns[1:][0],
    "Toplam (Perakende+Dağıtım) Enerji Bedeli",
    "Kullanıcı",
]].rename(columns = {"Kullanıcı": "Kullanıcı Adı"})

fselected = fselected.T.drop_duplicates().T


birim_columns = st.sidebar.columns((1,2))
with birim_columns[0]:
    birim = st.checkbox("Birim:", False)
with birim_columns[1]:
    if birim:
        birim_name = "TL/MWh"
        st.write("TL/MWh")
        fselected.iloc[:,:-1] = fselected.iloc[:,:-1].multiply(10)
    else:
        birim_name = "kr/kWh"

        st.write("kr/kWh")

if fselected.shape[1] == 3:
    fig = plot_frame(fselected.iloc[:, :2], birim_name)
elif fselected.shape[1] == 4:
    fig = plot_frame(fselected.iloc[:, :3], birim_name)


st.markdown(f"### {selected_name}")
st.plotly_chart(fig, use_container_width=True)

st.markdown(" - Bir önceki tarife değerine göre eğer mutlak olarak %10'dan fazla değişim göstermiş ise tarifedeki artışlar kırmızı, düşüşler yeşil renklendirmeyle yüzdesel olarak gösterilmiştir.")
st.markdown(" - Bazı tarife gruplarının isimleri değişmiştir, en son yayınlanan isimleriyle verilmiştir. İsimlerin detayı data kısmında paylaşılmıştır.")
with st.expander("Data"):
    st.dataframe(fselected, use_container_width=True)


## Footer
st.markdown("## ")
st.markdown("## ")
HtmlFile = open("./footer.html", 'r', encoding='utf-8')
footer = HtmlFile.read() 
components.html(footer, height = 400)
