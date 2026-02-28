#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
streamtest.in/logs sayfasındaki son test edilmiş yayınları çekip M3U playlist oluşturur.
"""

import requests
import re
from datetime import datetime
from typing import List, Tuple, Optional

def sayfayi_getir(url: str) -> Optional[str]:
    """Belirtilen URL'deki sayfanın HTML içeriğini getirir."""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        return response.text
    except requests.exceptions.RequestException as e:
        print(f"Sayfa yüklenirken hata oluştu: {e}")
        return None

def linkleri_ve_kanallari_bul(html_icerik: str) -> List[Tuple[str, str]]:
    """
    HTML içeriğinde medya linklerini (m3u8, mp4 vb.) ve muhtemel kanal/isimleri bulur.
    Her bir öğe için (link, kanal_adi) döndürür.
    """
    bulunanlar = []
    # Linkleri bul (basit bir regex, tırnak içindeki veya satır başındaki linkleri yakalar)
    # Bu regex, http veya https ile başlayıp, yaygın medya uzantıları veya belirli anahtar kelimeler içeren linkleri hedefler.
    link_regex = r'(https?://[^\s"\'<>]+?\.(?:m3u8|mp4|ts|mpd)[^\s"\'<>]*)'
    link_regex_genis = r'(https?://[^\s"\'<>]+(?:playlist|master|live|stream|index)[^\s"\'<>]*\.m3u8[^\s"\'<>]*)'
    
    tum_linkler = re.findall(link_regex, html_icerik, re.IGNORECASE)
    tum_linkler += re.findall(link_regex_genis, html_icerik, re.IGNORECASE)
    
    # Satırları satır satır inceleyip linkten hemen önce gelen ismi bulmaya çalışalım
    satirlar = html_icerik.split('\n')
    for i, satir in enumerate(satirlar):
        # Satırda link var mı?
        link_match = re.search(link_regex + '|' + link_regex_genis, satir, re.IGNORECASE)
        if link_match:
            link = link_match.group(0).strip()
            kanal_adi = None
            
            # Linkten hemen önceki satırda isim olabilir (genellikle streamtest.in'in yapısı böyle)
            if i > 0:
                onceki_satir = satirlar[i-1].strip()
                # Eğer önceki satır link değilse ve boş değilse, muhtemelen kanal adıdır.
                if onceki_satir and not re.search(r'https?://', onceki_satir, re.IGNORECASE):
                    # Tarih/saat formatlarını ve gereksiz ifadeleri temizle
                    aday = onceki_satir
                    # "Detail" kelimesini, saatleri ve tarihleri kaldır
                    aday = re.sub(r'\s*\|\s*Detail$', '', aday, flags=re.IGNORECASE)
                    aday = re.sub(r'\d{1,2}:\d{2}(?:AM|PM|am|pm)?\s*[A-Z]{2,3}\s*\d{1,2}[/-]\d{1,2}[/-]\d{2,4}', '', aday)
                    aday = re.sub(r'\d+\s*(?:minute|minutes|second|seconds|hour|hours)\s+ago', '', aday, flags=re.IGNORECASE)
                    aday = aday.strip()
                    
                    if aday and len(aday) < 100:  # Çok uzun satırları at
                        kanal_adi = aday
                    else:
                         # Önceki satır işe yaramazsa, linkin içinden bir isim türet (örneğin domain)
                         domain_match = re.search(r'https?://([^/]+)', link)
                         if domain_match:
                             kanal_adi = domain_match.group(1).replace('www.', '')
            
            # Hala isim yoksa domain adını kullan
            if not kanal_adi:
                domain_match = re.search(r'https?://([^/]+)', link)
                if domain_match:
                    kanal_adi = domain_match.group(1).replace('www.', '')
                else:
                    kanal_adi = "Bilinmeyen Kanal"
            
            # Eğer link daha önce eklenmemişse ekle
            if not any(link in l for l, _ in bulunanlar):
                bulunanlar.append((link, kanal_adi))
    
    return bulunanlar

def m3u_olustur(linkler_ve_kanallar: List[Tuple[str, str]], dosya_adi: str = "canli_yayinlar.m3u"):
    """Bulunan linklerden bir M3U playlist dosyası oluşturur."""
    with open(dosya_adi, 'w', encoding='utf-8') as f:
        f.write("#EXTM3U\n")
        f.write(f"# {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - streamtest.in/logs'dan otomatik oluşturuldu.\n\n")
        
        for link, kanal_adi in linkler_ve_kanallar:
            # Kanal adını daha düzenli hale getir
            temiz_kanal_adi = kanal_adi.strip().replace('|', '-').replace('  ', ' ').replace('  ', ' ')
            if not temiz_kanal_adi:
                temiz_kanal_adi = "İsimsiz Kanal"
                
            f.write(f'#EXTINF:-1 tvg-logo="" group-title="streamtest",{temiz_kanal_adi}\n')
            f.write(f"{link}\n\n")
    
    print(f"{len(linkler_ve_kanallar)} yayın linki '{dosya_adi}' dosyasına kaydedildi.")

def main():
    print("streamtest.in/logs sayfası taranıyor...")
    html_icerik = sayfayi_getir("https://streamtest.in/logs")
    
    if html_icerik:
        print("Sayfa başarıyla indirildi, linkler ve kanal isimleri çıkarılıyor...")
        bulunan_linkler = linkleri_ve_kanallari_bul(html_icerik)
        
        if bulunan_linkler:
            print(f"Toplam {len(bulunan_linkler)} medya linki bulundu.")
            m3u_olustur(bulunan_linkler)
        else:
            print("Sayfada hiç medya linki bulunamadı.")
    else:
        print("Sayfa içeriği alınamadığı için işlem durduruldu.")

if __name__ == "__main__":
    main()
