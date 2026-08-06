from datetime import datetime, timedelta
import time
weather_cache = []
weather_cache_time = 0

from flask import Flask, render_template, jsonify, request
from datetime import datetime, timedelta
import requests

app = Flask(__name__)

online_users={}
ziyaretciler = {}

API_KEY = "47c985532d16457337f109fb907d8a60"

# Arayüzdeki hava durumu panelleriyle eşleşen şehir koordinatları ve kodları
SEHIRLER = [
    {"isim": "İstanbul", "lat": 41.0082, "lng": 28.9784, "query": "Istanbul", "panel": "w-ist"},
    {"isim": "Ankara", "lat": 39.9334, "lng": 32.8597, "query": "Ankara", "panel": "w-ank"},
    {"isim": "İzmir", "lat": 38.4192, "lng": 27.1287, "query": "Izmir", "panel": "w-izm"},
    {"isim": "Adana Seyhan", "lat": 37.0000, "lng": 35.3213, "query": "Seyhan,Adana,TR", "panel": "w-adn"},
    {"isim": "Mersin", "lat": 36.8121, "lng": 34.6415, "query": "Mersin", "panel": "w-mer"},
    {"isim": "Antalya", "lat": 36.8841, "lng": 30.7056, "query": "Antalya", "panel": "w-ant"},
    {"isim": "Diyarbakır", "lat": 37.9144, "lng": 40.2306, "query": "Diyarbakir", "panel": "w-diy"},
    {"isim": "Trabzon", "lat": 41.0015, "lng": 39.7178, "query": "Trabzon", "panel": "w-tra"},
    {"isim": "Erzurum", "lat": 39.9043, "lng": 41.2679, "query": "Erzurum", "panel": "w-erz"}
]

@app.route("/api/online")
def online():
    import time
    simdi = time.time()
    global ziyaretciler

    ip = request.remote_addr
    ziyaretciler[ip] = simdi

    ziyaretciler = {
        k:v for k,v in ziyaretciler.items()
        if simdi-v < 300
    }

    return jsonify({"online": len(ziyaretciler)})

@app.route('/')
def home():
    import json
    try:
        with open("kameralar.json","r",encoding="utf-8") as f:
            kameralar=json.load(f)
    except:
        kameralar=[]
    return render_template('index.html', kameralar=kameralar)


@app.route('/api/cameras')
def cameras():
    import json
    try:
        with open("kameralar.json", "r", encoding="utf-8") as f:
            data = json.load(f)

        return jsonify([
            {
                "isim": x[0],
                "lat": x[1],
                "lng": x[2],
                "link": x[3],
                "type": x[4]
            }
            for x in data
        ])
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api')
def api_status():
    try:
        url = "https://api.orhanaydogdu.com.tr/deprem/kandilli/live"
        r = requests.get(url, timeout=10)
        veri = r.json()

        liste = []

        for d in veri.get("result", [])[:50]:
            c = d.get("geojson", {}).get("coordinates", [0,0])
            liste.append({
                "zaman": (datetime.strptime(d.get("date_time",""), "%Y-%m-%d %H:%M:%S") + timedelta(hours=3)).strftime("%Y-%m-%d %H:%M:%S"),
                "yer": d.get("title", ""),
                "mag": float(d.get("mag", 0)),
                "lat": float(c[1]),
                "lng": float(c[0])
            })

        return jsonify(liste)

    except Exception as e:
        print("Deprem hata:", e)
        return jsonify([])

@app.route('/api/weather')
def weather():
    sonuclar=[]

    for s in SEHIRLER:
        try:
            url=f"https://api.openweathermap.org/data/2.5/weather?lat={s['lat']}&lon={s['lng']}&appid={API_KEY}&units=metric&lang=tr"
            r=requests.get(url,timeout=10)

            if r.status_code==200:
                d=r.json()

                temp=round(d["main"]["temp"])
                feels=round(d["main"]["feels_like"])
                humidity=d["main"]["humidity"]

                alarm=None
                if temp>=38 or feels>=38:
                    alarm="sicak"
                elif temp<=0:
                    alarm="soguk"

                sonuclar.append({
                    "isim":s["isim"],
                    "lat":s["lat"],
                    "lng":s["lng"],
                    "anlik":temp,
                    "hissedilen":feels,
                    "nem":humidity,
                    "panel":s["panel"],
                    "alarm":alarm
                })
                continue

        except Exception as e:
            print("WEATHER:",e)

        sonuclar.append({
            "isim":s["isim"],
            "lat":s["lat"],
            "lng":s["lng"],
            "anlik":0,
            "hissedilen":0,
            "nem":0,
            "panel":s["panel"],
            "alarm":None
        })

    return jsonify(sonuclar)

@app.route('/api/risk')
def risk():
    return jsonify({"dusuk": 70, "orta": 20, "yuksek": 10})



@app.route('/api/havadalgasi')
def havadalgasi():
    try:
        import requests

        url=f"https://api.openweathermap.org/data/2.5/forecast?lat=37.025&lon=35.371&appid={API_KEY}&units=metric&lang=tr"
        data=requests.get(url,timeout=10).json()

        liste=data.get("list", [])

        if not liste:
            return jsonify({
                "durum":"veri yok",
                "mesaj":"Tahmin verisi alınamadı"
            })

        bugun=[]
        gelecek=[]

        for x in liste:
            sic=round(x["main"]["temp"])
            tarih=x["dt_txt"].split(" ")[0]

            if tarih == liste[0]["dt_txt"].split(" ")[0]:
                bugun.append(sic)
            else:
                gelecek.append(sic)

        simdi=max(bugun) if bugun else 0
        sonraki=max(gelecek) if gelecek else simdi

        fark=sonraki-simdi

        if sonraki >= 38:
            return jsonify({
                "alarm":"sicak",
                "mesaj":f"🔥 Sıcak hava dalgası riski ({gunluk[1]}°C)",

                "bugun":simdi,
                "beklenen":sonraki,
                "degisim":fark
            })

        if fark <= -8 and sonraki <= 15:
            return jsonify({
                "alarm":"soguk",
                "mesaj":"❄️ Soğuk hava girişi olabilir",
                "bugun":simdi,
                "beklenen":sonraki,
                "degisim":fark
            })

        return jsonify({
            "alarm":"yok",
            "mesaj":"🟢 Belirgin sıcak/soğuk hava dalgası görünmüyor",
            "bugun":simdi,
            "beklenen":sonraki,
            "degisim":fark
        })

    except Exception as e:
        return jsonify({
            "alarm":"hata",
            "mesaj":str(e)
        })



@app.route('/api/turkiye_havadalgasi')
def turkiye_havadalgasi():
    try:
        riskler=[]

        for sehir in SEHIRLER:
            url=f"https://api.openweathermap.org/data/2.5/forecast?lat={sehir['lat']}&lon={sehir['lng']}&appid={API_KEY}&units=metric&lang=tr"

            data=requests.get(url,timeout=8).json()
            liste=data.get("list",[])

            if not liste:
                continue

            gunler={}

            for x in liste:
                tarih=x["dt_txt"].split(" ")[0]
                sic=round(max(x["main"]["temp"], x["main"]["feels_like"]))

                if tarih not in gunler:
                    gunler[tarih]=[]
                gunler[tarih].append(sic)

            gunluk=[max(v) for v in gunler.values()]

            if len(gunluk) < 2:
                continue

            fark=max(gunluk[1:])-gunluk[0]

            if gunluk[1] >= 38 and fark >= 3:
                riskler.append({
                    "sehir":sehir["isim"],
                    "tip":"sicak",
                    "fark":fark,
                    "mesaj":f"🔥 Sıcak hava dalgası riski ({gunluk[1]}°C)"
                })
            elif fark >= 5:
                riskler.append({
                    "sehir":sehir["isim"],
                    "tip":"artis",
                    "fark":fark,
                    "mesaj":f"📈 Ani sıcaklık artışı (+{fark}°C)"
                })

            elif fark <= -8 and gunluk[1] <= 15:
                riskler.append({
                    "sehir":sehir["isim"],
                    "tip":"soguk",
                    "fark":fark,
                    "mesaj":"❄️ Soğuk hava girişi riski"
                })


        if riskler:
            return jsonify({
                "durum":"uyari",
                "riskler":riskler
            })

        return jsonify({
            "durum":"normal",
            "mesaj":"🟢 Türkiye genelinde belirgin hava dalgası görünmüyor",
            "riskler":[]
        })

    except Exception as e:
        return jsonify({
            "durum":"hata",
            "mesaj":str(e)
        })

@app.route('/api/forecast5')
def forecast5():
    try:
        url=f"https://api.openweathermap.org/data/2.5/forecast?lat=37.025&lon=35.371&appid={API_KEY}&units=metric&lang=tr"
        data=requests.get(url,timeout=10).json()

        gunler={}
        for x in data["list"]:
            tarih=x["dt_txt"].split(" ")[0]
            if tarih not in gunler:
                gunler[tarih]={
                    "min":round(x["main"]["temp_min"]),
                    "max":round(x["main"]["temp_max"]),
                    "durum":x["weather"][0]["description"]
                }
            else:
                gunler[tarih]["min"]=min(gunler[tarih]["min"],round(x["main"]["temp_min"]))
                gunler[tarih]["max"]=max(gunler[tarih]["max"],round(x["main"]["temp_max"]))

        sonuc=[]
        for tarih,v in list(gunler.items())[:5]:
            sonuc.append({
                "ikon":"☀️",
                "tarih":tarih,
                "durum":v["durum"],
                "min":v["min"],
                "max":v["max"]
            })

        return jsonify({"tahminler":sonuc})

    except Exception as e:
        return jsonify({"tahminler":[]})
@app.route('/api/rain-check')
def rain_check():
    try:
        url = f"http://api.openweathermap.org/data/2.5/weather?lat=37.025&lon=35.371&appid={API_KEY}&units=metric&lang=tr"
        r = requests.get(url, timeout=10).json()

        hava = r.get("weather", [{}])[0].get("description", "").lower()

        if any(x in hava for x in ["yağmur", "rain", "sağanak", "drizzle", "fırtına"]):
            durum = "Yağmur yağıyor"
        else:
            durum = "Yağış yok / Açık"

        return jsonify({
            "yerler": [
                {
                    "il": "Adana",
                    "ilçe": "Merkez",
   "ilce": "Merkez",
                    "durum": durum
                }
            ]
        })

    except Exception as e:
        return jsonify({"yerler":[{"il":"Adana","ilçe":"Merkez","ilce":"Merkez","durum":"Veri alınamadı"}]})

@app.route('/api/polen')
def polen():
    return jsonify([{"isim": "Adana Merkez", "agac": "Orta", "cayir": "Yüksek", "ot": "Düşük", "alerji": "Orta Risk"}])


@app.route('/api/havakutlesi')
def havakutlesi():
    try:
        analiz=[]
        for s in SEHIRLER:
            try:
                url=f"https://api.open-meteo.com/v1/forecast?latitude={s['lat']}&longitude={s['lng']}&current=temperature_2m,relative_humidity_2m,wind_speed_10m,wind_direction_10m,surface_pressure"
                d=requests.get(url,timeout=8).json()

                c=d.get("current",{})

                analiz.append({
                    "isim":s["isim"],
                    "sicaklik":round(c.get("temperature_2m",0)),
                    "nem":c.get("relative_humidity_2m",0),
                    "ruzgar":round(c.get("wind_speed_10m",0)),
                    "yon":c.get("wind_direction_10m",0),
                    "basinc":round(c.get("surface_pressure",0))
                })

            except:
                pass

        if not analiz:
            return jsonify({"durum":"veri yok"})

        en_sicak=max(analiz,key=lambda x:x["sicaklik"])
        en_soguk=min(analiz,key=lambda x:x["sicaklik"])

        fark=en_sicak["sicaklik"]-en_soguk["sicaklik"]

        tip="normal"

        if fark >= 10:
            if en_sicak["nem"] <= 30:
                tip="kuru_sicak"
                mesaj=f"🌡️ Sıcak merkez: {en_sicak['isim']} ({en_sicak['sicaklik']}°C, nem %{en_sicak['nem']})"
            elif en_sicak["nem"] >= 60:
                tip="nemli_sicak"
                mesaj=f"🌡️ Sıcak ve nemli hava kütlesi etkisi. Kaynak: {en_sicak['isim']}"
            else:
                tip="hava_kutlesi"
                mesaj=f"🌡️ Sıcak merkez: {en_sicak["isim"]} ({en_sicak["sicaklik"]}°C) | Soğuk merkez: {en_soguk["isim"]} ({en_soguk["sicaklik"]}°C) | Fark: {fark}°C"
        else:
            mesaj="🟢 Belirgin hava kütlesi hareketi yok"

        yon= en_sicak["yon"]

        if yon >= 315 or yon < 45:
            kaynak="Kuzey"
        elif yon < 135:
            kaynak="Doğu"
        elif yon < 225:
            kaynak="Güney"
        else:
            kaynak="Batı"

        ruzgar=en_sicak["ruzgar"]
        basinc_fark=abs(en_sicak["basinc"]-en_soguk["basinc"])

        puan=0

        if fark >= 10:
            puan += 2
        if fark >= 15:
            puan += 1

        if ruzgar >= 25:
            puan += 2
        elif ruzgar >= 15:
            puan += 1

        if basinc_fark >= 10:
            puan += 2
        elif basinc_fark >= 5:
            puan += 1

        if puan >= 5:
            guc="Çok güçlü"
        elif puan >= 3:
            guc="Güçlü"
        elif puan >= 1:
            guc="Orta"
        else:
            guc="Zayıf"

        hareket=f"🌬️ {kaynak} sektörlü rüzgar"

        if en_sicak["sicaklik"] >= 35 and en_sicak["nem"] <= 35:
            hava_kaynagi="🔥 Sıcak hava baskısı<br>📍 Muhtemel kaynak: Güney Akdeniz / Kuzey Afrika etkisi olabilir"
        elif kaynak=="Kuzey" and fark >= 10 and en_soguk["sicaklik"] <= 15:
            hava_kaynagi="🥶 Soğuk hava girişi<br>📍 Muhtemel kaynak: Balkanlar / kuzey bölgeler"
        elif kaynak=="Kuzey" and fark >= 8:
            hava_kaynagi="🌬️ Kuzey serin hava etkisi<br>📍 Daha serin hava akışı olabilir"
        elif kaynak=="Güney" and fark >= 8:
            hava_kaynagi="🌡️ Ilık hava taşınımı<br>📍 Muhtemel kaynak: Akdeniz çevresi"
        elif kaynak=="Batı" and fark >= 10:
            hava_kaynagi="🌬️ Batı yönlü hava hareketi"
        else:
            hava_kaynagi="🌍 Belirgin hava girişi yok"

        if tip=="kuru_sicak":
            etki="İç ve güney kesimlerde sıcaklık baskısı oluşturabilir"
        elif tip=="nemli_sicak":
            etki="Bunaltıcı sıcaklık ve yüksek nem etkisi oluşturabilir"
        elif tip=="hava_kutlesi":
            etki="Bölgesel hava değişimi takip edilmeli"
        else:
            etki="Belirgin hava kütlesi etkisi yok"

        return jsonify({
            "durum":"analiz",
            "tip":tip,
            "mesaj":mesaj,
            "kaynak_yon":kaynak,
            "hareket":hareket,
            "hava_kaynagi":hava_kaynagi,
            "etki":etki,
            "guc":guc,
            "sicak_merkez":en_sicak,
            "soguk_merkez":en_soguk,
            "fark":fark,
            "veriler":analiz
        })

    except Exception as e:
        return jsonify({"durum":"hata","mesaj":str(e)})

@app.route('/api/storm')
def storm():
    sonuc=[]
    try:
        for s in SEHIRLER:
            try:
                url=f"http://api.openweathermap.org/data/2.5/weather?lat={s['lat']}&lon={s['lng']}&appid={API_KEY}&units=metric&lang=tr"
                d=requests.get(url,timeout=5).json()

                ruzgar=round(d.get("wind",{}).get("speed",0)*3.6)
                sicaklik=round(d.get("main",{}).get("temp",0))

                if ruzgar >= 60:
                    durum="Fırtına uyarısı"
                elif ruzgar >= 40:
                    durum="Fırtına riski"
                else:
                    durum="Normal"

                sonuc.append({
                    "isim":s["isim"],
                    "ruzgar":ruzgar,
                    "sicaklik":sicaklik,
                    "durum":durum
                })
            except:
                pass

        return jsonify(sonuc)

    except Exception:
        return jsonify([])
@app.route('/api/get-visits', methods=['GET'])
def api_get_visits_fix():
    return jsonify([])

@app.context_processor
def inject_kameralar():
    kameralar_listesi = [
        ["Adana Sismik İstasyonu", 37.0, 35.3, "", "radar"],
        ["İstanbul Boğaz Kamerası", 41.0, 29.0, "https://www.youtube.com/embed/live_stream?channel=UC...", "yt"]
    ]
    return dict(kameralar=kameralar_listesi)


@app.route('/<sehir>-hava-durumu')
def sehir_sayfasi(sehir):
    isimler = {
        "istanbul":"İstanbul",
        "ankara":"Ankara",
        "izmir":"İzmir",
        "adana":"Adana Seyhan",
        "mersin":"Mersin",
        "antalya":"Antalya",
        "diyarbakir":"Diyarbakır",
        "trabzon":"Trabzon",
        "erzurum":"Erzurum"
    }

    ad = isimler.get(sehir.lower())
    if not ad:
        return "Şehir bulunamadı", 404

    return render_template("sehir.html", sehir=ad)




@app.route('/sitemap.xml')
def sitemap():
    from flask import Response
    base = request.host_url.rstrip('/')

    sayfalar = [
        "istanbul-hava-durumu",
        "ankara-hava-durumu",
        "izmir-hava-durumu",
        "adana-hava-durumu",
        "mersin-hava-durumu",
        "antalya-hava-durumu",
        "diyarbakir-hava-durumu",
        "trabzon-hava-durumu",
        "erzurum-hava-durumu"
    ]

    xml = '<?xml version="1.0" encoding="UTF-8"?>'
    xml += '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'

    for x in sayfalar:
        xml += f"<url><loc>{base}/{x}</loc></url>"

    xml += "</urlset>"

    return Response(xml, mimetype="application/xml")




@app.route('/robots.txt')
def robots():
    from flask import Response
    text = f"User-agent: *\nAllow: /\nSitemap: {request.host_url.rstrip('/')}/sitemap.xml"
    return Response(text, mimetype="text/plain")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)



