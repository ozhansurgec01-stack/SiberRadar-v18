import requests
from rich.console import Console
from rich.table import Table
from datetime import datetime

console = Console()

API_KEY = "47c985532d16457337f109fb907d8a60"
SEHIR = "Istanbul"
ULKE = "TR"


def hava_al():
    url = (
        f"https://api.openweathermap.org/data/2.5/weather?"
        f"q={SEHIR},{ULKE}&appid={API_KEY}"
        "&units=metric&lang=tr"
    )

    try:
        cevap = requests.get(url, timeout=10)
        return cevap.json()
    except Exception as e:
        console.print(e)
        return None


def analiz(d):
    skor = 0
    durum = []

    sicaklik = d["main"]["temp"]
    basinc = d["main"]["pressure"]
    ruzgar = d["wind"]["speed"]

    if basinc < 1005:
        skor += 30
        durum.append("Alçak basınç etkisi")

    if ruzgar > 7:
        skor += 30
        durum.append("Rüzgar güçleniyor")

    if sicaklik < 15:
        skor += 20
        durum.append("Serin hava")

    if not durum:
        durum.append("Normal atmosferik durum")

    return skor, durum


def goster(d):

    tablo = Table(title="🌐 SİBER RADAR")

    tablo.add_column("Bilgi")
    tablo.add_column("Değer")

    tablo.add_row("Şehir", SEHIR)
    tablo.add_row("Sıcaklık", str(d["main"]["temp"])+" °C")
    tablo.add_row("Hissedilen", str(d["main"]["feels_like"])+" °C")
    tablo.add_row("Nem", str(d["main"]["humidity"])+" %")
    tablo.add_row("Basınç", str(d["main"]["pressure"])+" hPa")
    tablo.add_row("Rüzgar", str(d["wind"]["speed"])+" m/s")
    tablo.add_row("Durum", d["weather"][0]["description"])
    tablo.add_row("Saat", datetime.now().strftime("%H:%M:%S"))

    console.print(tablo)

    skor, mesaj = analiz(d)

    console.print("\n[cyan]Hava Kütlesi Analizi[/cyan]")
    console.print("Sinyal:", skor,"%")

    for x in mesaj:
        console.print("•",x)


veri = hava_al()

if veri and "main" in veri:
    goster(veri)
else:
    console.print("API bağlantı hatası")
    console.print(veri)
