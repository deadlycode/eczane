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
    try:
        url = "https://www.eczaneler.gen.tr/nobetci-izmir-foca"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(url, headers=headers)
        if response.status_code == 404:
            raise HTTPException(
                status_code=404,
                detail="Foça'da nöbetçi eczane bulunamadı"
            )
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        eczaneler = []
        
        # Tüm eczane satırlarını bul
        rows = soup.find_all('div', {'class': 'row', 'style': 'font-size:110%;'})
        
        if not rows:
            raise HTTPException(
                status_code=404,
                detail="Foça'da nöbetçi eczane bulunamadı"
            )
        
        for row in rows:
            try:
                # İsim
                isim_span = row.find('span', {'class': 'isim'})
                if not isim_span:
                    continue
                    
                isim = isim_span.text.strip()
                
                # Adres ve telefon
                col_divs = row.find_all('div', {'class': ['col-lg-6', 'col-lg-3']})
                if len(col_divs) < 2:
                    continue
                
                adres_div = next((div for div in col_divs if 'col-lg-6' in div.get('class', [])), None)
                telefon_div = next((div for div in col_divs if 'col-lg-3' in div.get('class', [])), None)
                
                if not adres_div or not telefon_div:
                    continue
                
                adres = ' '.join(adres_div.stripped_strings)
                telefon = telefon_div.get_text(strip=True)
                
                if isim and adres and telefon:
                    eczane = {
                        "isim": isim,
                        "adres": adres,
                        "telefon": telefon,
                        "guncelleme": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    }
                    eczaneler.append(eczane)
            
            except Exception as e:
                print(f"Satır ayrıştırma hatası: {str(e)}")
                continue
        
        if not eczaneler:
            raise HTTPException(
                status_code=404,
                detail="Foça'da nöbetçi eczane bulunamadı"
            )
            
        return eczaneler
        
    except requests.RequestException as e:
        print(f"HTTP isteği hatası: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Veri çekme hatası: Sunucuya erişilemedi"
        )
    except HTTPException as he:
        raise he
    except Exception as e:
        print(f"Genel hata: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Veri çekme hatası: {str(e)}"
        )

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