#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
streamtest.in/logs sayfasından linkleri çekip M3U oluşturur.
"""

import requests
import re
import os
from datetime import datetime

def main():
    print("🔄 streamtest.in/logs taranıyor...")
    
    # Sayfayı çek
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get('https://streamtest.in/logs', headers=headers, timeout=30)
        response.raise_for_status()
        html = response.text
        print(f"✅ Sayfa indirildi: {len(html)} byte")
    except Exception as e:
        print(f"❌ Sayfa indirilemedi: {e}")
        return False
    
    # Linkleri bul (basit regex)
    linkler = []
    
    # .m3u8 linkleri
    m3u8_linkleri = re.findall(r'(https?://[^\s"\'<>]+\.m3u8[^\s"\'<>]*)', html)
    for link in m3u8_linkleri:
        link = link.strip()
        if link not in [l[0] for l in linkler]:
            linkler.append((link, "Canlı Yayın"))
    
    # .mp4 linkleri
    mp4_linkleri = re.findall(r'(https?://[^\s"\'<>]+\.mp4[^\s"\'<>]*)', html)
    for link in mp4_linkleri:
        link = link.strip()
        if link not in [l[0] for l in linkler]:
            linkler.append((link, "Video Kayıt"))
    
    print(f"🔗 {len(linkler)} link bulundu")
    
    if not linkler:
        print("⚠️ Hiç link bulunamadı!")
        return False
    
    # M3U dosyasını oluştur
    os.makedirs("outputs", exist_ok=True)
    m3u_path = "outputs/son_yayinlar.m3u"
    
    with open(m3u_path, "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n")
        f.write(f"# {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - streamtest.in/logs\n\n")
        
        for i, (link, kanal) in enumerate(linkler, 1):
            f.write(f'#EXTINF:-1,{kanal} {i}\n')
            f.write(f"{link}\n\n")
    
    print(f"✅ M3U dosyası oluşturuldu: {m3u_path}")
    print(f"📁 Dosya boyutu: {os.path.getsize(m3u_path)} byte")
    
    # Dosyanın içeriğini göster (debug)
    with open(m3u_path, "r") as f:
        print("\n📄 M3U İÇERİĞİ:")
        print(f.read()[:500] + "...")
    
    return True

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
