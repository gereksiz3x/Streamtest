#!/usr/bin/env python3
"""
EN BASİT Stream Collector
streamtest.in'den görünen linkleri alır, M3U yapar.
"""

import requests
import re

def get_page(url):
    """Sayfayı indir"""
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        response = requests.get(url, headers=headers, timeout=10)
        return response.text
    except:
        return ""

def extract_visible_links(html):
    """Sayfadaki görünen linkleri çıkar"""
    links = []
    
    # Tüm http/https ile başlayanları bul
    urls = re.findall(r'https?://[^\s<>"\']+', html)
    
    for url in urls:
        # Sadece stream olanları al
        if is_stream_link(url):
            # Temizle
            clean_url = url.split(' ')[0].split('|')[0].strip()
            if clean_url not in links:
                links.append(clean_url)
    
    return links

def is_stream_link(url):
    """Bu link stream linki mi?"""
    # streamtest'in kendi linklerini atla
    if 'streamtest.in' in url:
        return False
    
    # Stream pattern'leri
    stream_patterns = [
        '.m3u8', '.m3u', '.mpd',      # Stream dosyaları
        'get.php',                     # IPTV
        '/live/', '/stream/', '/hls/', # Stream yolları
        ':8080/', ':1935/',            # Stream portları
        'id=tvb', 'id=sz', 'id=%',     # TV parametreleri
    ]
    
    for pattern in stream_patterns:
        if pattern in url:
            return True
    
    return False

def create_m3u(links, filename="streams.m3u"):
    """M3U dosyası oluştur"""
    with open(filename, 'w', encoding='utf-8') as f:
        f.write("#EXTM3U\n")
        f.write(f"# Toplam: {len(links)} kanal\n\n")
        
        for i, url in enumerate(links, 1):
            f.write(f"#EXTINF:-1, Kanal {i}\n")
            f.write(f"{url}\n")
    
    print(f"M3U oluşturuldu: {filename} ({len(links)} link)")

def main():
    print("Stream Collector - Basit Sürüm")
    
    # 5 sayfayı tara
    all_links = []
    
    for page in range(1, 6):
        print(f"Sayfa {page} taranıyor...")
        url = f"https://streamtest.in/logs/page/{page}"
        html = get_page(url)
        
        if html:
            links = extract_visible_links(html)
            all_links.extend(links)
            print(f"  {len(links)} link bulundu")
        else:
            print(f"  Sayfa çekilemedi")
    
    # Tekilleri al
    unique_links = list(set(all_links))
    
    if unique_links:
        print(f"\nToplam {len(unique_links)} benzersiz link bulundu")
        
        # İlk 5 linki göster
        print("\nİlk 5 link:")
        for link in unique_links[:5]:
            print(f"  {link}")
        
        # M3U oluştur
        create_m3u(unique_links)
    else:
        print("Hiç link bulunamadı!")
        
        # Test için örnek linkler
        print("Test linkleri ekleniyor...")
        test_links = [
            "http://xxip9.top:8080/get.php?username=test&password=test&type=m3u_plus",
            "https://clubbingtv-samsunguk.amagi.tv/playlist720_p.m3u8",
            "http://nn.7x9d.cn/%E6%B7%B1%E5%9C%B3%E6%9C%80%E6%96%B0.php?id=gdxw",
        ]
        create_m3u(test_links)

if __name__ == "__main__":
    main()
