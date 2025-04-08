import sqlite3
import requests
import matplotlib
import matplotlib.cm as cm
import numpy as np

matplotlib.use('Agg')  # Matplotlib arka planını, pencere göstermeden dosyaları bellekte kaydetmek için ayarlama
import matplotlib.pyplot as plt
import cartopy.crs as ccrs  # Harita projeksiyonlarıyla çalışmamızı sağlayacak modülü içe aktarma
import cartopy.feature as cfeature  # Coğrafi özellikleri eklemek için

import sqlite3

class DB_Map:
    def __init__(self, db_name, database = "database.db"):
        self.conn = sqlite3.connect(db_name)  # Veritabanı bağlantısını başlat
        self.cursor = self.conn.cursor()  # Cursor nesnesi oluştur
        self.database = database

    def close(self):
        self.conn.close()  # Bağlantıyı kapat

    # Diğer fonksiyonlar burada yer alacak
    def create_user_table(self):
        conn = sqlite3.connect(self.database)  # Veri tabanına bağlanma
        with conn:
            # Kullanıcı şehirlerini depolamak için bir tablo oluşturma (eğer yoksa)
            conn.execute('''CREATE TABLE IF NOT EXISTS users_cities (
                                user_id INTEGER,
                                city_id TEXT,
                                FOREIGN KEY(city_id) REFERENCES cities(id)
                            )''')
            conn.commit()  # Değişiklikleri onaylama

    def add_city(self, user_id, city_name):
        conn = sqlite3.connect(self.database)
        with conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM cities WHERE city=?", (city_name,))
            city_data = cursor.fetchone()
            if city_data:
                city_id = city_data[0]
                conn.execute('INSERT INTO users_cities VALUES (?, ?)', (user_id, city_id))
                conn.commit()
                return 1
            else:
                return 0
            
    def get_population(self, city_name):
        conn = sqlite3.connect(self.database)
        with conn:
            cursor = conn.cursor()
            cursor.execute('''SELECT population FROM cities WHERE city = ?''', (city_name,))
            population = cursor.fetchone()
            return population[0] if population else None

    def select_cities(self, user_id):
        conn = sqlite3.connect(self.database)
        with conn:
            cursor = conn.cursor()
            cursor.execute('''SELECT cities.city FROM users_cities  
                            JOIN cities ON users_cities.city_id = cities.id
                            WHERE users_cities.user_id = ?''', (user_id,))
            cities = [row[0] for row in cursor.fetchall()]
            return cities

    def get_coordinates(self, city_name):
        conn = sqlite3.connect(self.database)
        with conn:
            cursor = conn.cursor()
            cursor.execute('''SELECT lat, lng FROM cities WHERE city = ?''', (city_name,))
            coordinates = cursor.fetchone()
            return coordinates

    def get_weather(self, city_name):
        api_key = '3a2a04fdde1455ab16481bbbf06a8209'
        url = f"http://api.openweathermap.org/data/2.5/weather?q={city_name}&appid={api_key}&units=metric"
        response = requests.get(url)
        weather_data = response.json()

        if weather_data.get("cod") != 200:
            return None
        else:
            temp = weather_data["main"]["temp"]
            weather = weather_data["weather"][0]["description"]
            return temp, weather
        
    def get_time(self, city_name):
        # Veritabanında şehir adı örneğin "Istanbul" olarak kaydedildi, API için "Europe/Istanbul" formatını oluşturuyoruz
        formatted_city_name = f"Europe/{city_name.capitalize()}"
        url = f"http://worldtimeapi.org/api/timezone/{formatted_city_name}"
        response = requests.get(url)
        time_data = response.json()

        if "datetime" in time_data:
            current_time = time_data["datetime"]
            return current_time
        else:
            print("API Yanıtı Hata:", time_data)  # Yanıtı debug etmek için yazdırıyoruz
            return None

    def create_graph(self, path, cities, color):
        ax = plt.axes(projection=ccrs.PlateCarree())
        ax.set_global() 

        ax.add_feature(cfeature.LAND, facecolor='#d4b79f') 
        ax.add_feature(cfeature.OCEAN, facecolor='#A1C6EA')  
        ax.add_feature(cfeature.BORDERS, linestyle=':', linewidth=0.8, edgecolor='#4C4C4C') 
        ax.add_feature(cfeature.COASTLINE, linewidth=0.8, edgecolor='#4C4C4C')
        ax.add_feature(cfeature.LAKES, edgecolor='#5577A1', facecolor='#A3C8D5', linewidth=0.4) 
        ax.add_feature(cfeature.RIVERS, edgecolor='#A1A1A1', linewidth=0.5) 
        ax.add_feature(cfeature.STATES, linestyle='--', linewidth=0.4, edgecolor='#808080')  

        for city in cities:
            coordinates = self.get_coordinates(city)
            if coordinates:
                lat, lng = coordinates

                weather = self.get_weather(city)
                time = self.get_time(city)
                
                city_info = f"{city}\n"
                if weather:
                    city_info += f"Weather: {weather[1]} at {weather[0]}°C\n"
                if time:
                    city_info += f"Time: {time}\n"

                plt.plot([lng], [lat], color=color, linewidth=1, marker="o", transform=ccrs.Geodetic())
                plt.text(lng - 20, lat + 12, city_info, horizontalalignment="left", transform=ccrs.Geodetic())
        plt.savefig(path)
        plt.close()

    def create_graph2(self, path, cities, color_scale="YlOrRd"):
        ax = plt.axes(projection=ccrs.PlateCarree())
        ax.set_global()

        ax.add_feature(cfeature.LAND, facecolor='#d4b79f')
        ax.add_feature(cfeature.OCEAN, facecolor='#A1C6EA')  
        ax.add_feature(cfeature.BORDERS, linestyle=':', linewidth=0.8, edgecolor='#4C4C4C') 
        ax.add_feature(cfeature.COASTLINE, linewidth=0.8, edgecolor='#4C4C4C')
        ax.add_feature(cfeature.LAKES, edgecolor='#5577A1', facecolor='#A3C8D5', linewidth=0.4) 
        ax.add_feature(cfeature.RIVERS, edgecolor='#A1A1A1', linewidth=0.5) 
        ax.add_feature(cfeature.STATES, linestyle='--', linewidth=0.4, edgecolor='#808080')  

        # Nüfusu sıralayarak renklerle şehirleri çizelim
        city_populations = {}
        for city in cities:
            coordinates = self.get_coordinates(city)
            if coordinates:
                lat, lng = coordinates
                city_populations[city] = self.get_population(city)  # Şehri ve nüfusunu al

        # Şehirlerin nüfuslarına göre renk skalası oluşturma
        min_population = min(city_populations.values())
        max_population = max(city_populations.values())
        norm = plt.Normalize(vmin=min_population, vmax=max_population)
        colormap = cm.get_cmap(color_scale)

        # Şehirleri çiz
        for city, population in city_populations.items():
            coordinates = self.get_coordinates(city)
            if coordinates:
                lat, lng = coordinates
                color = colormap(norm(population))  # Nüfus için renk skalası
                plt.plot([lng], [lat], color=color, linewidth=3, marker="o", transform=ccrs.Geodetic())

        plt.colorbar(cm.ScalarMappable(norm=norm, cmap=colormap), ax=ax, orientation='vertical', label='Population')
        plt.savefig(path)
        plt.close()

    def draw_distance(self, city1, city2):
        city1_coords = self.get_coordinates(city1)
        city2_coords = self.get_coordinates(city2)
        ig, ax = plt.subplots(subplot_kw={"projection": ccrs.PlateCarree()})
        ax.stock_img()
        plt.plot([city1_coords[1], city2_coords[1]], [city1_coords[0], city2_coords[0]], color="red", linewidth=2, marker="0", transform=ccrs.Geodetic())
        plt.text(city1_coords[1] + 3, city1_coords[0] + 12, city1, horizontalalignment="left", transform=ccrs.Geodetic())
        plt.text(city2_coords[1] + 3, city2_coords[0] + 12, city2, horizontalalignment="left", transform=ccrs.Geodetic())
        plt.savefig("distance_map.png")
        plt.close()

    def get_cities_by_country(self, country_name):
        conn = sqlite3.connect(self.database)
        with conn:
            cursor = conn.cursor()
            cursor.execute("SELECT city FROM cities WHERE country = ?", (country_name,))
            return cursor.fetchall()
        
    def get_cities_by_population(self, descending=True):
        order = "DESC" if descending else "ASC"
        conn = sqlite3.connect(self.database)
        with conn:
            cursor = conn.cursor()
            cursor.execute(f"""
                SELECT city FROM cities 
                ORDER BY CAST(population AS FLOAT) {order}
            """)
            return cursor.fetchall()

    def get_cities_by_country_and_population(self, country, descending=True):
        conn = sqlite3.connect(self.database)
        with conn:
            cursor = conn.cursor()
            order = "DESC" if descending else "ASC"
            cursor.execute(f'''
                SELECT cities.city, cities.population 
                FROM cities 
                WHERE cities.country = ? 
                ORDER BY cities.population {order}
            ''', (country,))
            cities = cursor.fetchall()
            return cities
