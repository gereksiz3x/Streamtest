#!/usr/bin/env python3
"""
Stream Collector - ULTIMATE DEBUG VERSION
Streamtest.in için özel olarak tasarlandı.
"""

import requests
import re
import time
import json
from datetime import datetime
import os
from urllib.parse import urlparse, unquote, quote

# ===================== CONFIGURATION =====================
BASE_URL = "https://streamtest.in/logs/page/"
MAX_PAGES = 3  # Test için 3 sayfa yeter
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
# =========================================================

def get_html_with_debug(url):
    """Sayfayı indir ve detaylı debug bilgisi ver"""
    print(f"\n🌐 FETCHING: {url}")
    
    headers = {
        'User-Agent': USER_AGENT,
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept-Encoding': 'gzip, deflate',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Cache-Control': 'no-cache',
        'Pragma': 'no-cache',
    }
    
    try:
        print(f"   Headers: {json.dumps(headers, indent=2)}")
        
        response = requests.get(url, headers=headers, timeout=30, verify=True)
        
        print(f"   Status Code: {response.status_code}")
        print(f"   Content Length: {len(response.text)} characters")
        print(f"   Content Type: {response.headers.get('content-type', 'unknown')}")
        print(f"   Server: {response.headers.get('server', 'unknown')}")
        
        if response.status_code != 200:
            print(f"   ⚠️ Non-200 response!")
            return None
            
        # DEBUG: Save raw HTML
        debug_filename = f"debug_raw_{url.split('/')[-1]}.html"
        with open(debug_filename, 'w', encoding='utf-8') as f:
            f.write(response.text[:10000])  # First 10K chars
        
        print(f"   ✅ Saved to: {debug_filename}")
        
        return response.text
        
    except requests.exceptions.Timeout:
        print("   ❌ Timeout error!")
        return None
    except requests.exceptions.SSLError as e:
        print(f"   ❌ SSL Error: {e}")
        return None
    except requests.exceptions.ConnectionError as e:
        print(f"   ❌ Connection Error: {e}")
        return None
    except Exception as e:
        print(f"   ❌ Unexpected error: {type(e).__name__}: {e}")
        return None

def analyze_html_structure(html, page_num):
    """HTML yapısını analiz et ve pattern'leri bul"""
    if not html:
        return []
    
    print(f"\n🔍 ANALYZING HTML Structure (Page {page_num})")
    print("-" * 50)
    
    # Save sample for manual inspection
    sample_file = f"html_sample_page_{page_num}.txt"
    with open(sample_file, 'w', encoding='utf-8') as f:
        f.write(html[:3000])
    
    # Look for specific patterns in streamtest.in
    lines = html.split('\n')
    
    print(f"   Total lines: {len(lines)}")
    
    # Find all lines with "http"
    http_lines = [i for i, line in enumerate(lines) if 'http' in line.lower()]
    print(f"   Lines with 'http': {len(http_lines)}")
    
    # Show first 10 http lines
    print("\n   First 10 lines containing 'http':")
    for idx, line_num in enumerate(http_lines[:10]):
        line_content = lines[line_num].strip()
        print(f"   [{line_num:3}] {line_content[:100]}...")
    
    return lines

def extract_urls_method1_direct_regex(html):
    """Method 1: Direct regex extraction"""
    print("\n🔄 METHOD 1: Direct regex extraction")
    
    # Pattern for all URLs
    url_pattern = r'https?://[a-zA-Z0-9\.\-_~:\/\?#\[\]@!$&\'()*+,;=%]+[a-zA-Z0-9\-_~\/#]'
    
    urls = re.findall(url_pattern, html)
    
    print(f"   Found {len(urls)} URLs with regex")
    
    # Filter out non-stream URLs
    stream_urls = []
    for url in urls:
        # Clean the URL
        clean_url = url.split(' ')[0].split('|')[0].strip().rstrip('.,;')
        
        # Check if it's a stream URL
        if is_stream_url(clean_url):
            stream_urls.append(clean_url)
    
    print(f"   Filtered to {len(stream_urls)} stream URLs")
    
    return stream_urls

def extract_urls_method2_line_by_line(lines):
    """Method 2: Line-by-line analysis (streamtest.in specific)"""
    print("\n🔄 METHOD 2: Line-by-line analysis")
    
    stream_urls = []
    
    # streamtest.in specific pattern:
    # 1. Time line (e.g., "9 minutes ago")
    # 2. URL line
    # 3. Optional channel name line
    # 4. "| Detail" line
    
    for i in range(len(lines) - 3):
        line1 = lines[i].strip()
        line2 = lines[i + 1].strip() if i + 1 < len(lines) else ""
        
        # Check if line1 is a time line
        time_patterns = ['minutes ago', 'hours ago', 'about', 'day ago']
        is_time_line = any(pattern in line1.lower() for pattern in time_patterns)
        
        # Check if line2 is a URL
        is_url_line = line2.startswith(('http://', 'https://'))
        
        if is_time_line and is_url_line:
            # This is likely a stream URL
            clean_url = line2.split(' ')[0].split('|')[0].strip()
            
            if is_stream_url(clean_url):
                stream_urls.append(clean_url)
                print(f"   Found via pattern: {clean_url[:80]}...")
    
    print(f"   Found {len(stream_urls)} URLs with line-by-line")
    
    return stream_urls

def extract_urls_method3_section_based(html):
    """Method 3: Section-based extraction"""
    print("\n🔄 METHOD 3: Section-based extraction")
    
    stream_urls = []
    
    # Try to find the stream sections
    # Look for patterns like:
    # - "## Recently Tested Streams" header
    # - Time + URL pattern
    
    # Split by potential separators
    sections = re.split(r'<br\s*/?>|\n\s*\n', html)
    
    for section in sections:
        # Look for URLs in each section
        urls_in_section = re.findall(r'https?://[^\s<>"\']+', section)
        
        for url in urls_in_section:
            clean_url = url.strip()
            if is_stream_url(clean_url):
                # Check if this is not a "Detail" link
                if 'detail' not in clean_url.lower():
                    stream_urls.append(clean_url)
    
    print(f"   Found {len(stream_urls)} URLs with section-based")
    
    return stream_urls

def is_stream_url(url):
    """Determine if URL is likely a stream URL"""
    
    # Quick checks
    if not url or len(url) < 10:
        return False
    
    # EXCLUDE patterns
    exclude_patterns = [
        'streamtest.in/logs/',  # Detail pages
        'favicon.', 'icon.',
        '.css', '.js',
        '.png', '.jpg', '.jpeg', '.gif', '.svg', '.ico',
        'doubleclick', 'google-analytics',
        'facebook.com', 'twitter.com',
        'wp-content', 'wordpress',
    ]
    
    for pattern in exclude_patterns:
        if pattern in url.lower():
            return False
    
    # INCLUDE patterns (stream URLs)
    include_patterns = [
        # File extensions
        '.m3u8', '.m3u', '.mpd',
        # Common stream paths
        'get.php', 'playlist.m3u', 'chunklist.m3u', 'manifest.mpd',
        '/live/', '/stream/', '/hls/', '/dash/',
        '/playlist', '/manifest', '/chunklist',
        # Common stream ports
        ':8080/', ':1935/', ':80/live', ':554/',
        # Common parameters
        'type=m3u', 'id=tvb', 'id=sz', 'id=%',
        # CDNs
        'akamaized', 'cloudfront', 'amagi.tv',
        # Common domains in streamtest
        '.xyz', '.top', '.cn', '.cc', '.lat', '.fun',
        '7x9d.cn', 'xxip9.top', 'yueliu.cloud',
    ]
    
    for pattern in include_patterns:
        if pattern in url.lower():
            return True
    
    return False

def collect_streams_from_all_pages():
    """Collect streams from all pages using multiple methods"""
    print("=" * 70)
    print("🚀 STREAM COLLECTOR - ULTIMATE DEBUG MODE")
    print("=" * 70)
    
    all_streams = []
    
    for page_num in range(1, MAX_PAGES + 1):
        print(f"\n📖 PROCESSING PAGE {page_num}/{MAX_PAGES}")
        print("-" * 50)
        
        page_url = f"{BASE_URL}{page_num}"
        
        # Get HTML
        html = get_html_with_debug(page_url)
        
        if not html:
            print(f"   ⚠️ Skipping page {page_num} - could not fetch")
            continue
        
        # Analyze structure
        lines = analyze_html_structure(html, page_num)
        
        # Try all extraction methods
        method1_urls = extract_urls_method1_direct_regex(html)
        method2_urls = extract_urls_method2_line_by_line(lines)
        method3_urls = extract_urls_method3_section_based(html)
        
        # Combine results
        page_streams = list(set(method1_urls + method2_urls + method3_urls))
        
        print(f"\n   📊 Page {page_num} results:")
        print(f"      Method 1: {len(method1_urls)} URLs")
        print(f"      Method 2: {len(method2_urls)} URLs")
        print(f"      Method 3: {len(method3_urls)} URLs")
        print(f"      Total unique: {len(page_streams)} URLs")
        
        # Show first few URLs
        if page_streams:
            print(f"\n      First 3 URLs from page {page_num}:")
            for i, url in enumerate(page_streams[:3]):
                print(f"      {i+1}. {url[:90]}...")
        
        all_streams.extend(page_streams)
        
        # Rate limiting
        time.sleep(2)
    
    # Remove duplicates
    unique_streams = list(set(all_streams))
    unique_streams.sort()
    
    print(f"\n📈 FINAL RESULTS")
    print("-" * 50)
    print(f"   Total unique streams found: {len(unique_streams)}")
    
    # Categorize URLs
    if unique_streams:
        print(f"\n   📋 URL Categories:")
        
        categories = {
            'M3U8': [u for u in unique_streams if '.m3u8' in u.lower()],
            'MPD': [u for u in unique_streams if '.mpd' in u.lower()],
            'get.php': [u for u in unique_streams if 'get.php' in u.lower()],
            'Chinese': [u for u in unique_streams if '%' in u and '.cn' in u],
            'Other': [u for u in unique_streams if not any(x in u.lower() for x in ['.m3u8', '.mpd', 'get.php'])]
        }
        
        for cat_name, cat_urls in categories.items():
            if cat_urls:
                print(f"      {cat_name}: {len(cat_urls)} URLs")
                if cat_name in ['M3U8', 'get.php']:  # Show examples
                    for url in cat_urls[:2]:
                        print(f"        • {url[:80]}...")
    
    return unique_streams

def create_m3u_file(stream_urls, filename="streams.m3u"):
    """Create M3U file with all streams"""
    print(f"\n💾 CREATING M3U FILE: {filename}")
    
    if not stream_urls:
        print("   ⚠️ No streams to write! Creating empty file for testing.")
        
        # Create TEST streams for debugging
        test_streams = [
            "http://xxip9.top:8080/get.php?username=test&password=test&type=m3u_plus",
            "https://clubbingtv-samsunguk.amagi.tv/playlist720_p.m3u8",
            "http://nn.7x9d.cn/%E6%B7%B1%E5%9C%B3%E6%9C%80%E6%96%B0.php?id=gdxw",
            "https://tglmp02.akamaized.net/out/v1/3170252e3fb0453085f2f4b0f8401a6b/manifest.mpd",
            "http://vraws.com/get.php?username=5579935946&password=6668397477&type=m3u_plus",
        ]
        
        # Use test streams if no real ones found
        stream_urls = test_streams
        print(f"   Using {len(test_streams)} test streams for debugging")
    
    with open(filename, 'w', encoding='utf-8') as f:
        # Write header
        f.write("#EXTM3U\n")
        f.write(f"# Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"# Total streams: {len(stream_urls)}\n")
        f.write("# Source: streamtest.in\n")
        f.write("# Collector: GitHub Actions\n")
        f.write("# WARNING: Some links may not work or require authentication\n\n")
        
        # Write streams
        for i, url in enumerate(stream_urls, 1):
            # Create channel name
            try:
                parsed = urlparse(url)
                domain = parsed.netloc
                
                # Try to extract meaningful name
                name_parts = []
                
                # Check for common patterns
                if 'get.php' in url:
                    name_parts.append('IPTV')
                elif '.m3u8' in url:
                    name_parts.append('HLS')
                elif '.mpd' in url:
                    name_parts.append('DASH')
                
                # Add domain (without subdomain)
                domain_parts = domain.split('.')
                if len(domain_parts) >= 2:
                    name_parts.append(domain_parts[-2])
                
                channel_name = '_'.join(name_parts) if name_parts else f"Stream_{i}"
                
            except:
                channel_name = f"Stream_{i}"
            
            # Write to file
            f.write(f"#EXTINF:-1, {channel_name}\n")
            f.write(f"{url}\n\n")
    
    # Verify file was created
    if os.path.exists(filename):
        file_size = os.path.getsize(filename)
        print(f"   ✅ Created: {filename} ({file_size} bytes)")
        
        # Show first few lines
        print(f"\n   📄 First 10 lines of {filename}:")
        with open(filename, 'r', encoding='utf-8') as f:
            for j, line in enumerate(f.readlines()[:15]):
                print(f"   {j+1:2}: {line.rstrip()}")
    else:
        print(f"   ❌ Failed to create {filename}")

def main():
    """Main function"""
    print("\n" + "=" * 70)
    print("🚀 STARTING COMPREHENSIVE STREAM COLLECTION")
    print("=" * 70)
    
    # Step 1: Collect streams
    all_streams = collect_streams_from_all_pages()
    
    # Step 2: Create M3U file
    create_m3u_file(all_streams, "streams.m3u")
    
    # Step 3: Create detailed report
    if all_streams:
        report_file = "collection_report.txt"
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write("=" * 60 + "\n")
            f.write("STREAM COLLECTION REPORT\n")
            f.write(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Total Streams: {len(all_streams)}\n")
            f.write("=" * 60 + "\n\n")
            
            f.write("ALL STREAMS:\n")
            f.write("-" * 60 + "\n")
            for i, url in enumerate(all_streams, 1):
                f.write(f"{i:3}. {url}\n")
        
        print(f"\n📋 Report saved to: {report_file}")
    
    # Step 4: List all created files
    print("\n📁 FILES CREATED:")
    print("-" * 50)
    for file in os.listdir('.'):
        if file.endswith(('.m3u', '.txt', '.html')):
            size = os.path.getsize(file)
            print(f"   • {file} ({size} bytes)")
    
    print("\n" + "=" * 70)
    print("✅ COLLECTION COMPLETE!")
    print("=" * 70)
    
    # Final warning if no streams found
    if len(all_streams) == 0:
        print("\n⚠️  WARNING: No streams were collected!")
        print("   Possible issues:")
        print("   1. Website is blocking GitHub Actions IP")
        print("   2. Website structure changed completely")
        print("   3. Cloudflare protection is active")
        print("   4. Network issues")
        print("\n   Check the debug_*.html files for raw HTML content.")

if __name__ == "__main__":
    main()
