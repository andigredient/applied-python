import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import plotly.graph_objects as go
from datetime import datetime, timedelta
import requests

def month_to_season(month):
    match month:
        case 12 | 1 | 2:
            return "winter"
        case 3 | 4 | 5:
            return "spring"
        case 6 | 7 | 8:
            return "summer"
        case 9 | 10 | 11:
            return "autumn"
    

def city_to_rus(str):
    match str:
        case "New York":
            return "Нью-Йорке"
        case "London":
            return "Лондоне"        
        case "Paris":
            return "Париже"        
        case "Tokyo":
            return "Токио"                
        case "Moscow":
            return "Москве"        
        case "Sydney":
            return "Сиднее"        
        case "Berlin":
            return "Берлине"        
        case "Beijing":
            return "Пекине"        
        case "Rio de Janeiro":
            return "Рио-де-Жанейро"        
        case "Dubai":
            return "Дубае"        
        case "Los Angeles":
            return "Лос-Анджелесе"        
        case "Singapore":
            return "Сингапуре"        
        case "Mumbai":
            return "Мумбаи"        
        case "Cairo":
            return "Каире"        
        case "Mexico City":
            return "Мехико"

st.set_page_config(
    layout="wide",
)
file = st.file_uploader(
    "Выберите CSV файл",
        type=['csv'],
    )

#df_weather = pd.read_csv('./temperature_data.csv')
if file is not None:
    df_weather = pd.read_csv(file)

    cities = sorted(df_weather['city'].unique())

    city = st.selectbox(
        "Выберите город",
        cities,
        index=0
    )

    df_city = df_weather[df_weather['city'] == city].copy().reset_index(drop=True)
    df_city['mean30'] = df_city['temperature'].rolling(window=30, center=True).mean() 
    df_city['timestamp'] = pd.to_datetime(df_weather['timestamp'])


    season_data = []
    for season in df_city['season'].unique():
        
            mask = df_city['season'] == season
            weather_data = df_city.loc[mask, 'temperature']
                
            mean_data = weather_data.mean()
            std_data = weather_data.std()

            season_data.append({
                    'Город': city,
                    'Сезон': season,
                    'Средняя температура': mean_data,
                    'Стандартное отклонение': std_data,
                })

    df_season_stats = pd.DataFrame(season_data)

    anom_data = []
    anom_alert =[]
    countAnom = 0
    for index in range(len(df_city)):
        if pd.notna(df_city.loc[index, "mean30"]):
            result = df_season_stats.loc[(df_season_stats['Город'] == df_city.loc[index, "city"]) & (df_season_stats['Сезон'] == df_city.loc[index, "season"]), ['Средняя температура', 'Стандартное отклонение']]
            dataAnom = df_city.loc[index, "timestamp"].date()
            if (abs(df_city.loc[index, 'mean30'] - result['Средняя температура'].iloc[0]) > 2 * result['Стандартное отклонение'].iloc[0]):
                anom_alert.append(f"{dataAnom} Аномалия: ({df_city.loc[index, 'mean30']} - {result['Средняя температура'].iloc[0]}) > (2 * {result['Стандартное отклонение'].iloc[0]})")
                countAnom = countAnom + 1
                anom_data.append({
                    'Город': city,
                    'Дата': dataAnom,
                    'Температура': df_city.loc[index, "temperature"] ,
                    'Средняя температура': result['Средняя температура'].iloc[0],
                    'Стандартное отклонение': result['Стандартное отклонение'].iloc[0],
                })

    tab1, tab2, tab3 = st.tabs([
        "Информация",
        "Графики",
        "API"
    ])
    with tab1:
        st.write("Общая таблица с первоначальными данными. Добавлен столбец mean30 - скользящее среднее")
        st.dataframe(df_city)
        st.write(f'Количество аномалий: {countAnom}')
        st.dataframe(anom_alert)
        st.write("Таблица с данными, которые выявили аномалию")
        st.dataframe(anom_data)


        st.write("Табличные данные по сезонам в городе")
        st.dataframe(df_season_stats)

    with tab2:
        fig, ax = plt.subplots(figsize=(20, 8))
        ax.plot(df_city["timestamp"], df_city["mean30"], color='blue', linewidth=2)
        ax.set_title("Скользящее среднее в период 30 дней")
        ax.set_xlabel("Дата")
        ax.set_ylabel("Температура °C")
        ax.grid(True)
        st.pyplot(fig)


        fig, ax = plt.subplots(figsize=(20, 8))    

        ax.plot(df_city['timestamp'], df_city['temperature'], 
                color='blue', linewidth=2, label='Температура')
        if anom_data:
            anom_df = pd.DataFrame(anom_data)
            anom_df['Дата'] = pd.to_datetime(anom_df['Дата'])
            ax.scatter(anom_df['Дата'], anom_df['Температура'],
                        color='red', s=100, 
                        marker='o',         
                        edgecolors='black', 
                        linewidth=1.5,      
                        zorder=10,          
                        label='Аномалии')
            
        ax.set_title('График температуры с аномалиями (при наличии)')
        ax.set_xlabel('Дата')
        ax.set_ylabel('Температура °C')
        ax.grid(True)
        ax.legend(loc='best')
        st.pyplot(fig)

    with tab3: 
        # Мой API. Мне не жалко
        #API_KEY = "ffb8bb9490f8f877c4a600b145f497d9"     
        API_KEY = st.text_input(f"Введите Ваш API_KEY")
        API_URL = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={API_KEY}&units=metric&lang=ru"
        response = requests.get(API_URL) 
        if st.button("Что там по погоде?"):
            if response.status_code == 401:
                error_data = response.json()
                st.error('cod":401, "message": "Invalid API key. Please see https://openweathermap.org/faq#error401 for more info.')
                st.stop()


            data_from_API = response.json()
            city_rus = city_to_rus(city)
            st.header(f"Онлайн температура в {city_rus}")
            st.divider()
            st.write(f"Сейчас в {city_rus} {data_from_API['weather'][0]['description']}, ")
            st.write(f'Температура: {data_from_API['main']['temp']}°C, ощущается как {data_from_API['main']['feels_like']}°C. Минимальная температура {data_from_API['main']['temp_min']}°C, максимальная температура {data_from_API['main']['temp_max']}°C')
            result = df_season_stats.loc[(df_season_stats['Город'] == city) & (df_season_stats['Сезон'] == month_to_season(datetime.now().month)), ['Средняя температура', 'Стандартное отклонение']]
            if (abs(data_from_API['main']['temp'] - result['Средняя температура'].iloc[0]) > 2 * result['Стандартное отклонение'].iloc[0]):
                st.write(f"Аномалия: ({data_from_API['main']['temp']} - {result['Средняя температура'].iloc[0]}) > 2 * {result['Стандартное отклонение'].iloc[0]} \n")
            else:
                st.write(f"Аномалии на данный момент нет: ({data_from_API['main']['temp']} - {result['Средняя температура'].iloc[0]}) > 2 * {result['Стандартное отклонение'].iloc[0]} \n")

        

