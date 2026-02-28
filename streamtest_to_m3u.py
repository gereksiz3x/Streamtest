#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
streamtest.in/logs sayfasındaki son test edilmiş yayınları çekip M3U playlist oluşturur.
"""

import requests
import re
import os
from datetime import datetime
from typing import Optional, List, Tuple

def sayfayi_getir(url: str) -> Optional[str]:
    """Belirtilen URL'deki sayfanın HTML içeriğini getirir."""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'tr-TR,tr;q=0.9,en;q=0.8',
            'Referer': 'https://www.google.com/',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        print(f"✅ Sayfa indirildi: {len(response.text)} byte")
        return response.text
    except Exception as e:
        print(f"❌ Sayfa indirilemedi: {e}")
        return None

def linkleri_bul(html_icerik: str) -> List[Tuple[str, str]]:
    """HTML içeriğinden linkleri ve kanal adlarını bulur."""
    bulunanlar = []
    
    # .m3u8 linkleri
    m3u8_linkleri = re.findall(r'(https?://[^\s"\'<>]+\.m3u8[^\s"\'<>]*)', html_icerik)
    for link in m3u8_linkleri:
        link = link.strip()
        if link not in [l[0] for l in bulunanlar]:
            bulunanlar.append((link, "Canlı Yayın"))
    
    # .mp4 linkleri
    mp4_linkleri = re.findall(r'(https?://[^\s"\'<>]+\.mp4[^\s"\'<>]*)', html_icerik)
    for link in mp4_linkleri:
        link = link.strip()
        if link not in [l[0] for l in bulunanlar]:
            bulunanlar.append((link, "Video Kayıt"))
    
    # Diğer muhtemel stream linkleri
    stream_linkleri = re.findall(r'(https?://[^\s"\'<>]+/(?:live|playlist|stream|hls)/[^\s"\'<>]*\.m3u8[^\s"\'<>]*)', html_icerik)
    for link in stream_linkleri:
        link = link.strip()
        if link not in [l[0] for l in bulunanlar]:
            bulunanlar.append((link, "Stream"))
    
    print(f"🔗 {len(bulunanlar)} link bulundu")
    return bulunanlar

def m3u_olustur(linkler: List[Tuple[str, str]]) -> bool:
    """M3U dosyası oluşturur."""
    if not linkler:
        print("⚠️ Hiç link bulunamadı!")
        return False
    
    # outputs klasörünü oluştur
    os.makedirs("outputs", exist_ok=True)
    m3u_path = "outputs/son_yayinlar.m3u"
    
    with open(m3u_path, "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n")
        f.write(f"# {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - streamtest.in/logs\n")
        f.write(f"# Toplam {len(linkler)} yayın\n\n")
        
        for i, (link, kanal) in enumerate(linkler, 1):
            f.write(f'#EXTINF:-1,{kanal} {i}\n')
            f.write(f"{link}\n\n")
    
    print(f"✅ M3U dosyası oluşturuldu: {m3u_path}")
    print(f"📁 Dosya boyutu: {os.path.getsize(m3u_path)} byte")
    
    # İlk birkaç linki göster
    print("\n📄 İlk 5 yayın:")
    for i, (link, kanal) in enumerate(linkler[:5], 1):
        print(f"  {i}. {kanal}: {link[:50]}...")
    
    return True

def main():
    print("🔄 streamtest.in/logs taranıyor...")
    
    # Sayfayı çek
    html = sayfayi_getir('https://streamtest.in/logs')
    if not html:
        return False
    
    # Linkleri bul
    linkler = linkleri_bul(html)
    
    # M3U oluştur
    basarili = m3u_olustur(linkler)
    
    return basarili

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
