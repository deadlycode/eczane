from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import httpx
from bs4 import BeautifulSoup
from typing import List, Dict
import asyncio

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
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers, follow_redirects=True)
            response.raise_for_status()
            
        soup = BeautifulSoup(response.text, 'html.parser')
        eczaneler = []
        
        table = soup.find('table', class_='table')
        if not table:
            return []
            
        for row in table.find_all('tr')[1:]:  # Skip header row
            cols = row.find_all('div', class_='col-lg-3') + row.find_all('div', class_='col-lg-6')
            if len(cols) >= 3:
                isim_elem = cols[0].find('span', class_='isim')
                if isim_elem:
                    isim = isim_elem.text.strip()
                    adres = cols[1].get_text(strip=True)
                    telefon = cols[2].get_text(strip=True)
                    
                    eczane = {
                        "isim": isim,
                        "adres": adres,
                        "telefon": telefon
                    }
                    eczaneler.append(eczane)
        
        return eczaneler
        
    except httpx.HTTPError as e:
        raise HTTPException(status_code=500, detail=f"HTTP error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))