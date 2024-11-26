from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import requests
from bs4 import BeautifulSoup
from typing import List, Dict
from datetime import datetime

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def scrape_foca_eczaneler() -> List[Dict]:
    url = "https://www.eczaneler.gen.tr/nobetci-izmir-foca"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        eczaneler = []
        
        # Aktif tab-pane'i bul (show active class'ına sahip olan)
        aktif_tab = soup.find('div', {'class': 'tab-pane fade show active'})
        if not aktif_tab:
            raise HTTPException(status_code=404, detail="Aktif nöbetçi eczane verisi bulunamadı")
        
        # Tarih bilgisini al
        tarih_div = aktif_tab.find('div', {'class': 'alert alert-warning'})
        tarih = tarih_div.text.strip() if tarih_div else "Tarih bilgisi bulunamadı"
        
        # Eczane satırlarını bul
        rows = aktif_tab.find_all('div', {'class': 'row', 'style': 'font-size:110%;'})
        
        for row in rows:
            # Eczane adını bul
            isim_span = row.find('span', {'class': 'isim'})
            if not isim_span:
                continue
            isim = isim_span.text.strip()
            
            # Adres ve ek bilgileri al
            adres_div = row.find('div', {'class': 'col-lg-6'})
            if not adres_div:
                continue
                
            # Adres metnini ve ek bilgileri ayır
            adres_text = adres_div.get_text('\n', strip=True).split('\n')
            adres = adres_text[0]
            
            # Ek bilgileri kontrol et
            ek_bilgiler = []
            for bilgi in adres_text[1:]:
                if bilgi.startswith('»'):
                    bilgi = bilgi.replace('»', '').strip()
                ek_bilgiler.append(bilgi)
            
            # Telefon bilgisini al
            telefon_div = row.find('div', {'class': 'col-lg-3 py-lg-2'})
            telefon = telefon_div.text.strip() if telefon_div else "Telefon bilgisi bulunamadı"
            
            eczane = {
                "isim": isim,
                "adres": adres,
                "telefon": telefon,
                "ek_bilgiler": ek_bilgiler if ek_bilgiler else None,
                "nobetci_tarih": tarih,
                "kaynak": url,
                "guncelleme": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            eczaneler.append(eczane)
        
        if not eczaneler:
            raise HTTPException(status_code=404, detail="Nöbetçi eczane bulunamadı")
            
        return eczaneler
        
    except requests.Timeout:
        raise HTTPException(status_code=504, detail="Sunucu yanıt vermedi")
    except requests.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Veri çekme hatası: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Beklenmeyen hata: {str(e)}")

@app.get("/")
async def root():
    return {
        "message": "Foça Nöbetçi Eczane API",
        "status": "active",
        "endpoints": {
            "eczaneler": "/eczaneler"
        }
    }

@app.get("/eczaneler")
async def get_foca_eczaneler() -> List[Dict]:
    return scrape_foca_eczaneler()