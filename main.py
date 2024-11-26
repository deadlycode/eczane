from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from seleniumbase import Driver
from typing import List, Dict
import time
from datetime import datetime
import json
from contextlib import contextmanager

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@contextmanager
def create_driver():
    driver = None
    try:
        driver = Driver(uc=True, headless=True)
        yield driver
    finally:
        if driver:
            driver.quit()

def scrape_eczaneler(sehir: str, ilce: str) -> List[Dict]:
    with create_driver() as driver:
        try:
            url = f"https://www.eczaneler.gen.tr/nobetci-{sehir}-{ilce}"
            driver.get(url)
            
            # Sayfanın yüklenmesini bekle
            driver.implicitly_wait(10)
            
            # Tablo elementinin yüklenmesini bekle
            table = driver.find_element("css selector", "table.table")
            if not table:
                return []
            
            eczaneler = []
            rows = driver.find_elements("css selector", "table.table tbody tr")
            
            for row in rows:
                try:
                    isim_element = row.find_element("css selector", "span.isim")
                    adres_element = row.find_element("css selector", "div.col-lg-6")
                    telefon_element = row.find_element("css selector", "div.col-lg-3.py-lg-2")
                    
                    eczane = {
                        "isim": isim_element.text.strip(),
                        "adres": adres_element.text.strip(),
                        "telefon": telefon_element.text.strip(),
                        "guncelleme": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    }
                    eczaneler.append(eczane)
                except Exception as e:
                    print(f"Row parsing error: {str(e)}")
                    continue
            
            return eczaneler
            
        except Exception as e:
            print(f"Scraping error: {str(e)}")
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
    return scrape_eczaneler(sehir, ilce)