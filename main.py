from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from seleniumbase import Driver
from bs4 import BeautifulSoup
from typing import List, Dict
import json

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "Nöbetçi Eczane API"}

@app.get("/eczaneler/{sehir}/{ilce}")
async def get_eczaneler(sehir: str, ilce: str) -> List[Dict]:
    url = f"https://www.eczaneler.gen.tr/nobetci-{sehir}-{ilce}"
    
    try:
        # SeleniumBase ile sayfayı aç
        driver = Driver(uc=True, headless=True)
        driver.get(url)
        
        # Sayfanın yüklenmesini bekle
        driver.wait_for_element("table.table")
        
        # Sayfa kaynağını al
        html = driver.page_source
        driver.quit()
        
        soup = BeautifulSoup(html, 'html.parser')
        eczaneler = []
        
        # Eczane tablosunu bul
        table = soup.find('table', class_='table')
        if not table:
            return []

        # Her bir eczane satırını işle
        for row in table.find_all('tr')[1:]:
            cols = row.find_all('div', class_='col-lg-3') + row.find_all('div', class_='col-lg-6')
            if len(cols) >= 3:
                isim = cols[0].find('span', class_='isim')
                adres = cols[1].get_text(strip=True)
                telefon = cols[2].get_text(strip=True)
                
                if isim:
                    eczane = {
                        "isim": isim.text,
                        "adres": adres,
                        "telefon": telefon
                    }
                    eczaneler.append(eczane)

        return eczaneler
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))