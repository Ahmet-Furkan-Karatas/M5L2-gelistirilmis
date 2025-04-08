from config import *
from logic import *
import discord
from discord.ext import commands
from config import TOKEN

# Veri tabanı yöneticisini başlatma
manager = DB_Map("database.db")

bot = commands.Bot(command_prefix="!", intents=discord.Intents.all())

# Kullanıcı rengi tutan bir sözlük
user_color = {}

@bot.event
async def on_ready():
    print("Bot başlatıldı!")

@bot.command()
async def start(ctx: commands.Context):
    await ctx.send(f"Merhaba, {ctx.author.name}. Mevcut komutların listesini keşfetmek için !help_me yazın.")

@bot.command()
async def help_me(ctx: commands.Context):
    await ctx.send("""- `!start` - Botu başlatın ve hoş geldiniz mesajı alın.
- `!help_me` - Mevcut komutların listesini alın. 
- `!show_city <şehir_adı>` - Verilen şehri haritada görüntüleyin.
- `!remember_city <şehir_adı>` - Verilen şehri kaydedin.
- `!show_my_cities` - Tüm hatırlanan şehirleri görüntüleyin.
- `!isaretci_renk <renk>` - Haritada şehir işaretleme rengini belirleyin.
- `!filtre <ülke> <yoğunluk>` - Belirli bir ülkedeki şehirleri yoğunluk sırasına göre gösterin (örn: !filtre Turkey azalan).""")

@bot.command()
async def isaretci_renk(ctx, color: str):
    user_color[ctx.author.id] = color.lower()
    await ctx.send(f"İşaretçi renginiz {color} olarak ayarlandı!")

@bot.command()
async def show_city(ctx: commands.Context, *, city_name=""):
    if not city_name:
        await ctx.send("Hatalı format. Lütfen şehir adını İngilizce olarak ve komuttan sonra boşluk bırakarak girin.")
        return
    
    color = user_color.get(ctx.author.id, "red") 
    manager.create_graph(f"{ctx.author.id}.png", [city_name], color)
    await ctx.send(file=discord.File(f"{ctx.author.id}.png"))

@bot.command()
async def remember_city(ctx: commands.Context, *, city_name=""):
    if manager.add_city(ctx.author.id, city_name):
        await ctx.send(f'{city_name} şehri başarıyla kaydedildi!')
    else:
        await ctx.send("Hatalı format. Lütfen şehir adını İngilizce olarak ve komuttan sonra bir boşluk bırakarak girin.")

@bot.command()
async def show_my_cities(ctx: commands.Context):
    cities = manager.select_cities(ctx.author.id)
    if cities:
        manager.create_graph(f"{ctx.author.id}_cities.png", cities)
        await ctx.send(file=discord.File(f"{ctx.author.id}_cities.png"))
    else:
        await ctx.send("Henüz bir şehir kaydetmediniz.")

# ✅ Yeni eklenen filtre komutu
@bot.command()
async def filtre(ctx, country: str, order: str = "azalan"):
    try:
        # "azalan" kelimesini True, "artan" kelimesini False yapalım
        descending = True if order == "azalan" else False
        
        # Şehirleri nüfusa göre sıralıyoruz
        cities = manager.get_cities_by_country_and_population(country, descending)
        
        # Nüfusa göre renkler
        color = "Reds" if descending else "Blues"
        
        # Grafiği oluşturuyoruz
        manager.create_graph2(f"{ctx.author.id}_filtered.png", [c[0] for c in cities], color)
        
        # Görseli kullanıcıya gönderiyoruz
        await ctx.send(file=discord.File(f"{ctx.author.id}_filtered.png"))
    except Exception as e:
        await ctx.send(f"Bir hata oluştu: {str(e)}")

if __name__ == "__main__":
    bot.run(TOKEN)
