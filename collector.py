import requests
from bs4 import BeautifulSoup
import re
from datetime import datetime
import os

def extract_stream_urls_from_page(page_url):
    """Tek bir sayfadan stream URL'lerini çıkar"""
    try:
        print(f"📄 Fetching: {page_url}")
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(page_url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Sayfadaki tüm bağlantıları bul
        stream_urls = []
        
        # 1. Doğrudan <a> tag'lerindeki href'leri kontrol et
        for link in soup.find_all('a', href=True):
            href = link['href']
            if is_stream_url(href):
                stream_urls.append(href)
        
        # 2. Sayfa içindeki düz metinde URL'leri ara (güçlü regex)
        text_urls = re.findall(r'https?://[^\s<>"\']+', response.text)
        for url in text_urls:
            if is_stream_url(url) and url not in stream_urls:
                stream_urls.append(url)
        
        # 3. Sayfadaki düz metin satırlarında URL ara
        lines = response.text.split('\n')
        for line in lines:
            # "http" ile başlayan ve "Detail" içermeyen satırlar
            if 'http' in line and 'Detail' not in line:
                # Satırdaki URL'yi çıkar
                url_match = re.search(r'(https?://[^\s<>"\']+)', line)
                if url_match:
                    url = url_match.group(1)
                    if is_stream_url(url) and url not in stream_urls:
                        stream_urls.append(url)
        
        print(f"  ✅ Found {len(stream_urls)} URLs")
        return list(set(stream_urls))  # Tekilleri döndür
        
    except Exception as e:
        print(f"  ❌ Error fetching {page_url}: {e}")
        return []

def is_stream_url(url):
    """URL'nin stream URL'si olup olmadığını kontrol et"""
    # İstenmeyen URL'leri filtrele
    if 'detail' in url.lower() or 'streamtest.in' in url:
        return False
    
    # Stream dosya uzantıları/pattern'leri
    stream_patterns = [
        '.m3u', '.m3u8', '.mpd',          # Stream formatları
        'get.php?type=m3u',                # IPTV get.php
        '/playlist', '/live/', '/stream',  # Stream yolları
        'manifest.', 'chunklist.',         # HLS/DASH
        'id=tvb', 'id=sz', 'id=%'          # Sayfadaki özel pattern'ler
    ]
    
    # URL stream pattern'lerinden birini içeriyor mu?
    for pattern in stream_patterns:
        if pattern in url.lower():
            return True
    
    return False

def collect_all_streams():
    """Tüm sayfalardan stream'leri topla"""
    all_streams = []
    base_url = "https://streamtest.in/logs/page/"
    
    # Kaç sayfa tarayacağımızı belirle
    max_pages = 5  # İstediğiniz sayfa sayısı
    
    for page_num in range(1, max_pages + 1):
        page_url = f"{base_url}{page_num}"
        page_streams = extract_stream_urls_from_page(page_url)
        all_streams.extend(page_streams)
    
    # Tekilleri al ve sırala
    unique_streams = list(set(all_streams))
    unique_streams.sort()
    
    print(f"\n📊 Total unique streams found: {len(unique_streams)}")
    return unique_streams

def create_m3u_file(stream_urls, filename="streams.m3u"):
    """M3U dosyası oluştur"""
    with open(filename, 'w', encoding='utf-8') as f:
        f.write("#EXTM3U\n")
        f.write(f"# Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"# Total streams: {len(stream_urls)}\n")
        f.write("# Source: streamtest.in\n\n")
        
        for i, url in enumerate(stream_urls, 1):
            # Kanal ismini URL'den çıkar
            channel_name = f"Stream_{i}"
            
            # URL'den anlamlı isim çıkarmaya çalış
            try:
                domain = url.split('/')[2] if len(url.split('/')) > 2 else "Unknown"
                # Özel durumlar
                if 'get.php' in url:
                    if 'username=' in url:
                        channel_name = f"IPTV_{domain}"
                    else:
                        channel_name = f"IPTV_Stream_{i}"
                elif '.m3u8' in url:
                    channel_name = f"HLS_Stream_{domain}"
                elif '.mpd' in url:
                    channel_name = f"DASH_Stream_{domain}"
                elif 'id=' in url or 'id=%' in url:
                    channel_name = f"TV_Channel_{i}"
                else:
                    channel_name = f"Stream_{domain}"
            except:
                channel_name = f"Stream_{i}"
            
            # M3U formatında yaz
            f.write(f"#EXTINF:-1, {channel_name}\n")
            f.write(f"{url}\n\n")
    
    print(f"✅ M3U file created: {filename}")
    print(f"📁 File size: {os.path.getsize(filename)} bytes")

def main():
    print("🚀 Starting Stream Collector...")
    print("=" * 50)
    
    # Tüm stream'leri topla
    all_streams = collect_all_streams()
    
    if not all_streams:
        print("❌ No streams found!")
        return
    
    # M3U dosyası oluştur
    create_m3u_file(all_streams)
    
    # İstatistikleri yazdır
    print("\n📈 Statistics:")
    print(f"   • Total URLs: {len(all_streams)}")
    
    # URL türlerini say
    m3u_count = sum(1 for url in all_streams if '.m3u' in url.lower())
    m3u8_count = sum(1 for url in all_streams if '.m3u8' in url.lower())
    mpd_count = sum(1 for url in all_streams if '.mpd' in url.lower())
    php_count = sum(1 for url in all_streams if 'get.php' in url.lower())
    
    print(f"   • M3U URLs: {m3u_count}")
    print(f"   • M3U8 URLs: {m3u8_count}")
    print(f"   • MPD URLs: {mpd_count}")
    print(f"   • get.php URLs: {php_count}")

if __name__ == "__main__":
    main()