import pandas as pd
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import matplotlib.pyplot as plt
import numpy as np

from pyFTS.benchmarks import Measures
from pyFTS.partitioners import Grid
from pyFTS.models import chen

st.set_option('deprecation.showPyplotGlobalUse', False)

st.info(""" 

Universitas Sebelas Maret, Surakarta

Nama Anggota Kelompok :
1. Agung Budi Santoso (L0122008)
2. Alvito Muhammad Yan Fahriel (L0122017)
3. Arma Nasrul Mustofa (L0122026)

Program Studi :   
Informatika 

Kelas / Angkatan :        
A / 2022
""")

st.title("""Data Harga Beras Premium di Provinsi Jawa Barat""")
st.write("""Data ini diambil dari dataset harga beras premium di tingkat penggilingan Provinsi Jawa Barat.""")

# Path file lokal
file_path = 'dataset.csv'

data_bulanan_ei = pd.read_csv(file_path)
data_bulanan_ei["Bulan-Tahun"] = pd.to_datetime(data_bulanan_ei["Bulan-Tahun"])
data_bulanan_ei["Bulan-Tahun"] = data_bulanan_ei["Bulan-Tahun"].dt.date

with st.sidebar:
    st.subheader("Filter Controls Configuration")
    month = ["All", "Januari", "Februari", "Maret", "April", "Mei", "Juni", "Juli",
             "Agustus", "September", "Oktober", "November", "Desember"]
    year = [i for i in range(2019, 2024)]

    show_filter = st.radio("Filter Dataframe", ("No", "Yes"), index=0)

    if show_filter == "Yes":
        col1, col2 = st.columns(2)

        with col1:
            choosen_month = st.selectbox("Select month", month)

        with col2:
            choosen_year = st.selectbox("Select year", year)

        if choosen_month == "All":
            data_bulanan_ei = data_bulanan_ei[data_bulanan_ei["Bulan-Tahun"].apply(lambda x: x.year) == choosen_year]
        else:
            data_bulanan_ei = data_bulanan_ei[
                (data_bulanan_ei["Bulan-Tahun"].apply(lambda x: x.year) == choosen_year) & 
                (data_bulanan_ei["Bulan-Tahun"].apply(lambda x: x.month) == month.index(choosen_month))
            ]

with st.sidebar:
    indicator = "Harga"
    n_part = st.slider("Partitions", 1, 20, 8)

tab_eda, tab_model = st.tabs(["EDA", "Model"])

with tab_eda:
    st.subheader("Exploratory Data Analysis Harga Beras Premium di Provinsi Jawa Barat")
    st.dataframe(data_bulanan_ei)

    fig = go.Figure()
    if show_filter == "Yes":
        year_data = data_bulanan_ei[data_bulanan_ei["Bulan-Tahun"].apply(lambda x: x.year) == choosen_year]
        fig.add_trace(go.Bar(
            x=year_data['Bulan-Tahun'].apply(lambda x: x.strftime('%B')),
            y=year_data[indicator],
            name=indicator,
            marker_color='blue',
            hovertemplate='<b>%{x}</b><br><i>Harga</i>: Rp %{y:.2f} <br>'
        ))
        fig.update_layout(
            title=f"Bar Plot Harga Beras {choosen_year}",
            xaxis_title='Bulan',
            yaxis_title='Harga (Rp)',
            xaxis=dict(tickmode='array', tickvals=list(range(1, 13)), 
                       ticktext=['Januari', 'Februari', 'Maret', 'April', 'Mei', 'Juni', 'Juli', 
                                 'Agustus', 'September', 'Oktober', 'November', 'Desember'])
        )
    else:
        fig.add_trace(go.Bar(
            x=data_bulanan_ei['Bulan-Tahun'].apply(lambda x: x.strftime('%Y-%m')),
            y=data_bulanan_ei[indicator],
            name=indicator,
            marker_color='blue',
            hovertemplate='<b>%{x}</b><br><i>Harga</i>: Rp %{y:.2f} <br>'
        ))
        fig.update_layout(
            title=f"Bar Plot Harga Beras 2019 - 2023",
            xaxis_title='Bulan-Tahun',
            yaxis_title='Harga (Rp)',
            xaxis=dict(tickmode='array', 
                       tickvals=data_bulanan_ei['Bulan-Tahun'].apply(lambda x: x.strftime('%Y-%m')), 
                       ticktext=data_bulanan_ei['Bulan-Tahun'].apply(lambda x: x.strftime('%Y-%m')))
        )
    st.plotly_chart(fig)

with tab_model:
    st.subheader("Pemodelan Data Harga Beras Premium di Provinsi Jawa Barat")

    predict_tab, forecast_tab = st.tabs(["Prediksi", "Peramalan"])

    with predict_tab:
        bulan_tahun = data_bulanan_ei['Bulan-Tahun'].values
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=bulan_tahun,
            y=data_bulanan_ei[indicator],
            name=f"{indicator}",
            marker_color='blue',
            hovertemplate='<b>%{x}</b><br><i>Harga</i>: Rp %{y:.2f} <br>'
        ))
        fig.update_layout(
            title=f"Line Plot {indicator} Bulanan",
            xaxis_title='Bulan-Tahun',  
            yaxis_title=f"Harga (Rp)",
            xaxis=dict(tickmode='array', 
                       tickvals=data_bulanan_ei['Bulan-Tahun'].apply(lambda x: x.strftime('%Y-%m')), 
                       ticktext=data_bulanan_ei['Bulan-Tahun'].apply(lambda x: x.strftime('%Y-%m')))
        )
        st.plotly_chart(fig)

        fs = Grid.GridPartitioner(data=data_bulanan_ei[indicator], npart=n_part)

        fig, ax = plt.subplots(nrows=1, ncols=1, figsize=[25, 10])
        ax.set_xlim(0, len(data_bulanan_ei))
        ax.set_ylim(-0.1, 0.1)
        ax.tick_params(axis='x', labelsize=20)
        ax.tick_params(axis='y', labelsize=20)
        fs.plot(ax)
        ax.set_title(f"Fuzzy Set {indicator}", fontsize=30)
        st.pyplot(fig)

        np.int = int
        model = chen.ConventionalFTS(partitioner=fs)
        model.fit(data_bulanan_ei[indicator].values)
        st.code(model)

        prediction = model.predict(data_bulanan_ei[indicator].values)

        data_fts_result = pd.DataFrame({
            'date': bulan_tahun,
            'actual': data_bulanan_ei[indicator],
            'prediction': prediction
        })

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=data_fts_result['date'], y=data_fts_result['actual'], mode='lines', name='Actual'))
        fig.add_trace(go.Scatter(
            x=data_fts_result['date'], y=data_fts_result['prediction'], mode='lines', name='Prediction'))
        fig.update_layout(
            xaxis=dict(tickangle=45, tickfont=dict(size=12), tickformat='%Y-%m-%d'),
            yaxis=dict(title_font=dict(size=20), tickfont=dict(size=20)),
            legend=dict(x=1, y=0, xanchor='right', yanchor='bottom', font=dict(size=12))
        )
        for i in range(len(bulan_tahun)):
            fig.add_shape(type='line', x0=bulan_tahun[i], y0=0, x1=bulan_tahun[i], y1=1, line=dict(
                color='black', width=1, dash='solid' if i % 2 == 0 else 'dash'))
        st.plotly_chart(fig)

        st.write(data_fts_result)
        # Calculate RMSE
        rmse = Measures.rmse(data_fts_result.prediction, data_fts_result.actual)
        st.write(f"RMSE: {rmse}")

        # Calculate MAPE
        mape = np.mean(np.abs((data_fts_result['actual'] - data_fts_result['prediction']) / data_fts_result['actual'])) * 100
        st.write(f"MAPE: {mape:.2f}%")

    with forecast_tab:
        st.write("Under Construction")
