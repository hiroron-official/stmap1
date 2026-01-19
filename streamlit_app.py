import streamlit as st
import requests
import pandas as pd
import pydeck as pdk
from datetime import datetime, timedelta

# --- ページ設定 ---
st.set_page_config(page_title="都市別気温 3D Map", layout="wide")
st.title("主要都市の現在気温 3Dビジュアライゼーション")

# 対象都市のデータ
target_cities = {
    'Fukuoka':    {'lat': 33.5904, 'lon': 130.4017},
    'Saga':       {'lat': 33.2494, 'lon': 130.2974},
    'Nagasaki':   {'lat': 32.7450, 'lon': 129.8739},
    'Kumamoto':   {'lat': 32.7900, 'lon': 130.7420},
    'Oita':       {'lat': 33.2381, 'lon': 131.6119},
    'Miyazaki':   {'lat': 31.9110, 'lon': 131.4240},
    'Kagoshima':  {'lat': 31.5600, 'lon': 130.5580},
    'Osaka':      {'lat': 34.6937, 'lon': 135.5023}, 
    'Tokyo':      {'lat': 35.6895, 'lon': 139.6917}
}

# --- データ取得関数 ---
@st.cache_data(ttl=600)
def fetch_weather_data():
    weather_info = []
    BASE_URL = 'https://api.open-meteo.com/v1/forecast'
    
    for city, coords in target_cities.items():
        params = {
            'latitude':  coords['lat'],
            'longitude': coords['lon'],
            'current': 'temperature_2m',
            'timezone': 'Asia/Tokyo'
        }
        try:
            response = requests.get(BASE_URL, params=params)
            response.raise_for_status()
            data = response.json()
            
            # 計測時刻のフォーマット (ISO形式から読みやすい形式へ)
            time_str = datetime.fromisoformat(data['current']['time']).strftime('%Y/%m/%d %H:%M')
            temp = data['current']['temperature_2m']
            
            # 気温に応じた色設定 [R, G, B, Alpha]
            # 25度以上なら赤っぽく、15度以下なら青っぽく簡易設定
            if temp >= 20:
                color = [255, 100, 0, 200]  # オレンジ/赤
            elif temp >= 10:
                color = [255, 200, 0, 200]  # 黄
            else:
                color = [0, 150, 255, 200]  # 青
            
            weather_info.append({
                'City': city,
                'lat': coords['lat'],
                'lon': coords['lon'],
                'Temperature': temp,
                'Time': time_str,
                'color': color,
                'elevation': temp * 5000  # 高さを強調するために係数を調整
            })
        except Exception as e:
            st.error(f"Error fetching {city}: {e}")
            
    return pd.DataFrame(weather_info)

# データの取得
with st.spinner('最新の気温データを取得中...'):
    df = fetch_weather_data()

# --- メインレイアウト ---
col1, col2 = st.columns([1, 2])

with col1:
    st.subheader("📊 都市別データ")
    # 時刻も表示
    st.dataframe(df[['City', 'Temperature', 'Time']], use_container_width=True)
    
    st.info("※ 1度あたり 5,000m の高さで表示しています。")
    
    if st.button('データを更新'):
        st.cache_data.clear()
        st.rerun()

with col2:
    st.subheader("🌡️ 3D カラムマップ")

    # 初期表示位置を全都市が収まるように調整 (九州〜東京の中間付近)
    view_state = pdk.ViewState(
        latitude=33.5,
        longitude=134.5,
        zoom=5.5,
        pitch=50,
        bearing=0
    )

    # ColumnLayer の定義
    layer = pdk.Layer(
        "ColumnLayer",
        data=df,
        get_position='[lon, lat]',
        get_elevation='elevation',
        radius=15000,
        get_fill_color='color', # 都市ごとに設定した色を使用
        pickable=True,
        auto_highlight=True,
    )

    # 描画
    st.pydeck_chart(pdk.Deck(
        layers=[layer],
        initial_view_state=view_state,
        map_style='mapbox://styles/mapbox/light-v10', # 明るい地図スタイル
        tooltip={
            "html": "<b>{City}</b><br>気温: {Temperature}°C<br>時刻: {Time}",
            "style": {"color": "white", "backgroundColor": "black"}
        }
    ))
