from flask import Flask, render_template, request
from folium.plugins import HeatMap
import pandas as pd
import folium
import os

app = Flask(__name__)

df = pd.DataFrame()
print(df)
intervalo_minutos = 3

def carregar_dataframe_csv(caminho):
    try:
        global df
        df = pd.read_csv(caminho, encoding='ISO-8859-1')

        # Verifique se as colunas 'Data' e 'Hora' existem no DataFrame
        if 'Data' not in df.columns or 'Hora' not in df.columns:
            raise ValueError("O arquivo CSV não contém as colunas 'Data' e 'Hora'.")

        # Crie a coluna 'DataHora' a partir das colunas 'Data' e 'Hora'
        df['DataHora'] = pd.to_datetime(df['Data'] + ' ' + df['Hora'], format='%d/%m/%Y %I:%M:%S %p')

        # Converta as colunas 'Latitude' e 'Longitude' para float
        df['Latitude'] = df['Latitude'].str.replace(',', '.').astype(float)
        df['Longitude'] = df['Longitude'].str.replace(',', '.').astype(float)

        print(df)

        return df
    except Exception as e:
        print(f'Erro ao carregar arquivo CSV: {e}')
        return pd.DataFrame()


def criar_mapa(df_filtrado):
    mapa = folium.Map(location=[df_filtrado.iloc[0]['Latitude'], df_filtrado.iloc[0]['Longitude']], zoom_start=14)

    df_velocidade_zero = df_filtrado[df_filtrado['Velocidade'] == 0]
    dados_heatmap = df_velocidade_zero[['Latitude', 'Longitude']].values.tolist()

    HeatMap(dados_heatmap).add_to(mapa)
    tempo_anterior = None

    for _, row in df_filtrado.iterrows():
        if tempo_anterior is None or (row['DataHora'] - tempo_anterior).seconds >= intervalo_minutos * 60:
            latitude, longitude = row['Latitude'], row['Longitude']
            google_maps_link = f"https://www.google.com/maps/search/?api=1&query={latitude},{longitude}"
            popup_content = f"{row['Placa']} - {row['Data']} {row['Hora']} - Velocidade: {row['Velocidade']} km/h - LatLong: {[latitude, longitude]}<br><a href='{google_maps_link}' target='_blank'>Ver no Google Maps</a>"

            marker = folium.Marker(location=[latitude, longitude],
                                  popup=folium.Popup(popup_content, max_width=300)
                                  ).add_to(mapa)

            tempo_anterior = row['DataHora']

    # Use um caminho relativo para salvar o mapa
    mapa.save('static/mapa_deslocamento.html')

def escolher_arquivo():
    file_path = filedialog.askopenfilename(filetypes=[("Arquivos CSVs", "*.csv")])
    if file_path:
        global df
        df = carregar_dataframe_csv(file_path)

@app.route('/', methods=['GET', 'POST'])
def index():
    global df

    if request.method == 'POST':
        data_inicial = request.form['data_inicial']
        hora_inicial = request.form['hora_inicial']
        data_final = request.form['data_final']
        hora_final = request.form['hora_final']

        if not all([data_inicial, hora_inicial, data_final, hora_final]):
            return render_template('index.html', mapa_gerado=False, mensagem_erro="Forneça todas datas e horas")

        filtro = ((df['DataHora'] >= pd.to_datetime(f'{data_inicial} {hora_inicial}', format='%Y-%m-%d %H:%M:%S')) &
                  (df['DataHora'] <= pd.to_datetime(f'{data_final} {hora_final}', format='%Y-%m-%d %H:%M:%S')))
        df_filtrado = df[filtro].copy()

        if df_filtrado.empty:
            return render_template('index.html', mapa_gerado=False, mensagem_erro=f"Não há dados no intervalo de datas especificado: {data_inicial} {hora_inicial} - {data_final} {hora_final}")
        
        criar_mapa(df_filtrado)
        return render_template('index.html', mapa_gerado=True)

    return render_template('index.html', mapa_gerado=False)

if __name__ == '__main__':
    app.run(debug=True)
