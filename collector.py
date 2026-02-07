import requests
import re
from datetime import datetime
import os
from urllib.parse import urlparse

def extract_stream_urls_from_page(page_url):
    """Streamtest.in sayfasından stream URL'lerini çıkar (DÜZELTİLDİ)"""
    try:
        print(f"📄 Fetching: {page_url}")
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        }
        
        response = requests.get(page_url, headers=headers, timeout=15)
        
        if response.status_code != 200:
            print(f"  ❌ HTTP {response.status_code}")
            return []
        
        print(f"  ✅ Status: {response.status_code}, Length: {len(response.text)} chars")
        
        # DEBUG: İlk 1000 karakteri kaydet
        with open("debug_page.html", "w", encoding="utf-8") as f:
            f.write(response.text[:2000])
        
        stream_urls = []
        lines = response.text.split('\n')
        
        # ÖNEMLİ: Streamtest.in sayfa yapısı analizi
        # URL'ler genellikle şu formatta:
        # 1. Zaman bilgisi olan satır
        # 2. Boş satır  
        # 3. URL satırı
        # 4. "| Detail" satırı
        
        for i, line in enumerate(lines):
            line = line.strip()
            
            # URL içeren satırları bul
            if line.startswith('http://') or line.startswith('https://'):
                # "Detail" sayfası linki mi kontrol et
                if 'streamtest.in/logs/' in line and 'Detail' in lines[i+1] if i+1 < len(lines) else False:
                    continue  # Bu "Detail" linki, atla
                
                # Bu bir stream URL'si mi?
                if is_likely_stream_url(line):
                    # URL'yi temizle
                    clean_url = line.split(' ')[0].split('|')[0].strip()
                    
                    # Geçersiz karakterleri kontrol et
                    if ' ' in clean_url or '<' in clean_url:
                        continue
                    
                    # "Detail" kelimesini içeriyor mu?
                    if 'Detail' in clean_url:
                        continue
                    
                    # Benzersizse ekle
                    if clean_url not in stream_urls:
                        stream_urls.append(clean_url)
                        print(f"    ➕ Found: {clean_url[:80]}...")
        
        print(f"  📊 Found {len(stream_urls)} URLs on this page")
        return stream_urls
        
    except Exception as e:
        print(f"  ❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return []

def is_likely_stream_url(url):
    """URL'nin stream URL'si olma olasılığını kontrol et"""
    
    # KESİNLİKLE ATLANACAK pattern'ler
    exclude_patterns = [
        'streamtest.in',      # Kendi sayfası
        '/detail',            # Detail sayfaları
        'favicon',            # Favicon
        '.css', '.js',        # CSS/JS dosyaları
        '.png', '.jpg', '.gif', '.ico',  # Resimler
    ]
    
    for pattern in exclude_patterns:
        if pattern in url.lower():
            return False
    
    # STREAM OLMA İHTİMALİ YÜKSEK pattern'ler
    stream_patterns = [
        '.m3u', '.m3u8', '.mpd',                    # Stream formatları
        'get.php',                                   # IPTV get.php
        '.php?id=', '.php?type=', '.php?auth=',     # PHP stream script'leri
        '/live/', '/stream/', '/playlist/',         # Stream yolları
        '/manifest.', '/chunklist.',                # HLS/DASH manifest
        ':8080/', ':1935/', ':80/',                 # Stream portları
        '/hls/', '/dash/', '/mpegts/',              # Stream path'leri
    ]
    
    for pattern in stream_patterns:
        if pattern in url.lower():
            return True
    
    # Alternatif: Domain analizi
    try:
        parsed = urlparse(url)
        domain = parsed.netloc.lower()
        
        # Bilinen stream domain pattern'leri
        stream_domains = ['.xyz', '.top', '.cn', '.cloud', '.tv', '.net', 'akamaized']
        for d in stream_domains:
            if d in domain:
                return True
    except:
        pass
    
    return False

def collect_all_streams():
    """Tüm sayfalardan stream'leri topla"""
    all_streams = []
    base_url = "https://streamtest.in/logs/page/"
    
    # TEST: Sadece ilk 2 sayfa ile başla
    max_pages = 2
    
    print(f"\n🔍 Scanning {max_pages} pages from {base_url}")
    print("=" * 60)
    
    for page_num in range(1, max_pages + 1):
        page_url = f"{base_url}{page_num}"
        page_streams = extract_stream_urls_from_page(page_url)
        
        if page_streams:
            all_streams.extend(page_streams)
        else:
            print(f"  ⚠️ No URLs found on page {page_num}, stopping scan")
            break
        
        # Kısa bekle (rate limiting için)
        import time
        time.sleep(1)
    
    # Tekilleri al
    unique_streams = list(set(all_streams))
    unique_streams.sort()
    
    print(f"\n📊 TOTAL: Found {len(unique_streams)} unique streams")
    
    # DEBUG: Bulunanları kaydet
    with open("found_urls.txt", "w", encoding="utf-8") as f:
        for url in unique_streams:
            f.write(url + "\n")
    
    return unique_streams

def create_m3u_file(stream_urls, filename="streams.m3u"):
    """M3U dosyası oluştur"""
    if not stream_urls:
        print("❌ No streams to write to M3U file!")
        
        # Boş da olsa M3U dosyası oluştur (header ile)
        with open(filename, 'w', encoding='utf-8') as f:
            f.write("#EXTM3U\n")
            f.write(f"# Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("# WARNING: No streams found!\n")
            f.write("# Check the extraction logic.\n")
        
        print(f"⚠️ Created empty M3U file: {filename}")
        return
    
    with open(filename, 'w', encoding='utf-8') as f:
        f.write("#EXTM3U\n")
        f.write(f"# Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"# Total streams: {len(stream_urls)}\n")
        f.write("# Source: streamtest.in\n")
        f.write("# Format: #EXTINF:-1, Channel Name\n")
        f.write("#         URL\n\n")
        
        for i, url in enumerate(stream_urls, 1):
            # Kanal adını oluştur
            try:
                parsed = urlparse(url)
                domain = parsed.netloc
                path = parsed.path
                
                # Path'ten isim çıkar
                if path:
                    # Son segmenti al
                    name = path.split('/')[-1]
                    if '.' in name:
                        name = name.split('.')[0]
                    
                    if name and len(name) > 1:
                        channel_name = f"Channel_{i}_{name}"
                    else:
                        channel_name = f"Channel_{i}_{domain}"
                else:
                    channel_name = f"Channel_{i}_{domain}"
                    
                # Çok uzunsa kısalt
                if len(channel_name) > 50:
                    channel_name = channel_name[:47] + "..."
                    
            except:
                channel_name = f"Stream_{i}"
            
            # M3U formatında yaz
            f.write(f"#EXTINF:-1, {channel_name}\n")
            f.write(f"{url}\n")
    
    print(f"✅ M3U file created: {filename}")
    print(f"📁 File size: {os.path.getsize(filename)} bytes")
    
    # İlk birkaç satırı göster
    print("\n📄 First 5 entries:")
    with open(filename, 'r', encoding='utf-8') as f:
        lines = f.readlines()[:15]
        for line in lines:
            print(f"  {line.rstrip()}")

def main():
    print("🚀 Stream Collector - DEBUG VERSION")
    print("=" * 60)
    
    # Debug bilgileri
    print("Python version:", os.sys.version)
    print("Current dir:", os.getcwd())
    print("Files in dir:", os.listdir('.'))
    
    # Tüm stream'leri topla
    all_streams = collect_all_streams()
    
    # M3U dosyası oluştur
    create_m3u_file(all_streams)
    
    # Eğer hala boşsa, test yap
    if not all_streams:
        print("\n🔧 DEBUG MODE: Testing extraction manually...")
        test_extraction()

def test_extraction():
    """Manuel test fonksiyonu"""
    test_url = "https://streamtest.in/logs/page/1"
    
    print(f"\n🧪 Testing extraction from: {test_url}")
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(test_url, headers=headers, timeout=10)
        
        print(f"Status: {response.status_code}")
        print(f"Length: {len(response.text)} characters")
        
        # Tüm http/https bağlantılarını bul
        all_urls = re.findall(r'https?://[^\s<>"\']+', response.text)
        
        print(f"\nFound {len(all_urls)} total URLs in page")
        
        # İlk 10 URL'yi göster
        print("\nFirst 10 URLs found:")
        for i, url in enumerate(all_urls[:10], 1):
            print(f"{i:2}. {url}")
            
        # Stream olabilecekleri filtrele
        stream_urls = [url for url in all_urls if is_likely_stream_url(url)]
        
        print(f"\nFiltered to {len(stream_urls)} likely stream URLs:")
        for i, url in enumerate(stream_urls[:10], 1):
            print(f"{i:2}. {url}")
            
        # Debug için kaydet
        with open("test_all_urls.txt", "w", encoding="utf-8") as f:
            for url in all_urls:
                f.write(url + "\n")
                
        with open("test_stream_urls.txt", "w", encoding="utf-8") as f:
            for url in stream_urls:
                f.write(url + "\n")
                
    except Exception as e:
        print(f"Test error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
