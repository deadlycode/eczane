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

def scrape_eczaneler(sehir: str, ilce: str) -> List[Dict]:
    try:
        url = f"https://www.eczaneler.gen.tr/nobetci-{sehir}-{ilce}"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        table = soup.find('table', {'class': 'table'})
        
        if not table:
            return []
        
        eczaneler = []
        rows = table.find('tbody').find_all('tr')
        
        for row in rows:
            try:
                isim_element = row.find('span', {'class': 'isim'})
                adres_element = row.find('div', {'class': 'col-lg-6'})
                telefon_element = row.find('div', {'class': 'col-lg-3 py-lg-2'})
                
                if isim_element and adres_element and telefon_element:
                    isim = isim_element.text.strip()
                    adres = adres_element.text.strip()
                    telefon = telefon_element.text.strip()
                    
                    if isim and adres and telefon:  # Boş kayıtları filtrele
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
        
        return eczaneler
        
    except Exception as e:
        print(f"Veri çekme hatası: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Veri çekme hatası: {str(e)}"
        )

@app.get("/")
async def root():
    return {
        "message": "Nöbetçi Eczane API",
        "status": "active",
        "endpoints": {
            "eczaneler": "/eczaneler/{sehir}/{ilce}"
        }
    }

@app.get("/eczaneler/{sehir}/{ilce}")
async def get_eczaneler(sehir: str, ilce: str) -> List[Dict]:
    eczaneler = scrape_eczaneler(sehir, ilce)
    if not eczaneler:
        raise HTTPException(
            status_code=404,
            detail="Bu bölgede nöbetçi eczane bulunamadı"
        )
    return eczaneler