#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
streamtest.in/logs sayfasındaki son test edilmiş yayınları çekip M3U playlist oluşturur.
GitHub Actions ile otomatik çalışacak şekilde tasarlanmıştır.
"""

import requests
import re
import os
import json
from datetime import datetime
from typing import List, Tuple, Optional, Dict
import sys

class StreamTestScraper:
    def __init__(self):
        self.base_url = "https://streamtest.in/logs"
        self.output_dir = "outputs"
        self.archive_file = os.path.join(self.output_dir, "stream_archive.json")
        
    def sayfayi_getir(self) -> Optional[str]:
        """Sayfanın HTML içeriğini getirir."""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            response = requests.get(self.base_url, headers=headers, timeout=20)
            response.raise_for_status()
            return response.text
        except requests.exceptions.RequestException as e:
            print(f"❌ Sayfa yüklenirken hata: {e}")
            return None

    def linkleri_ve_kanallari_bul(self, html_icerik: str) -> List[Dict]:
        """
        HTML içeriğinden linkleri ve kanal bilgilerini çıkarır.
        Gelişmiş regex ve pattern tanıma kullanır.
        """
        bulunanlar = []
        
        # Gelişmiş link patternleri
        link_patterns = [
            r'(https?://[^\s"\'<>]+?\.(?:m3u8|mp4|ts|mpd)[^\s"\'<>]*)',
            r'(https?://[^\s"\'<>]+/(?:live|playlist|master|stream|index)[^\s"\'<>]*\.m3u8[^\s"\'<>]*)',
            r'(https?://[^\s"\'<>]+/hls/[^\s"\'<>]*\.m3u8[^\s"\'<>]*)',
            r'(https?://[^\s"\'<>]+\.(?:akamaihd|cloudfront)\.net/[^\s"\'<>]*\.m3u8[^\s"\'<>]*)'
        ]
        
        # HTML'i satırlara böl ve analiz et
        satirlar = html_icerik.split('\n')
        
        for i, satir in enumerate(satirlar):
            for pattern in link_patterns:
                link_match = re.search(pattern, satir, re.IGNORECASE)
                if link_match:
                    link = link_match.group(0).strip()
                    
                    # Kanal adını bul (gelişmiş algoritma)
                    kanal_adi = self._kanal_adi_bul(satirlar, i, link)
                    
                    # Link tipini belirle
                    link_tipi = self._link_tipini_belirle(link)
                    
                    # Benzersizlik kontrolü
                    if not any(l['url'] == link for l in bulunanlar):
                        bulunanlar.append({
                            'url': link,
                            'kanal_adi': kanal_adi,
                            'tip': link_tipi,
                            'bulunma_zamani': datetime.now().isoformat(),
                            'kaynak_satir': i
                        })
                    break
        
        return bulunanlar

    def _kanal_adi_bul(self, satirlar: List[str], link_satiri_index: int, link: str) -> str:
        """En uygun kanal adını bulmak için gelişmiş algoritma"""
        kanal_adi = None
        
        # 1. Önceki satırlarda isim ara
        for j in range(max(0, link_satiri_index-3), link_satiri_index):
            onceki_satir = satirlar[j].strip()
            if onceki_satir and len(onceki_satir) < 100 and not re.search(r'https?://', onceki_satir):
                # Tarih/saat ve gereksiz ifadeleri temizle
                temiz_metin = self._temizle_metin(onceki_satir)
                if temiz_metin and len(temiz_metin) > 2:
                    kanal_adi = temiz_metin
                    break
        
        # 2. Link içinden domain adını çıkar
        if not kanal_adi:
            domain_match = re.search(r'https?://([^/]+)', link)
            if domain_match:
                domain = domain_match.group(1)
                # Alt domain'leri temizle
                domain = re.sub(r'^www\.', '', domain)
                domain = domain.split('.')[0].capitalize()
                kanal_adi = domain
        
        # 3. Hiçbir şey bulunamazsa
        if not kanal_adi:
            kanal_adi = "Bilinmeyen Kanal"
        
        return kanal_adi

    def _temizle_metin(self, metin: str) -> str:
        """Metinden tarih, saat ve gereksiz ifadeleri temizler"""
        # Saat formatlarını temizle
        metin = re.sub(r'\d{1,2}:\d{2}\s*(?:AM|PM|am|pm)?', '', metin)
        metin = re.sub(r'\d{1,2}[/-]\d{1,2}[/-]\d{2,4}', '', metin)
        metin = re.sub(r'\d+\s*(?:minute|minutes|hour|hours|second|seconds)\s+ago', '', metin, flags=re.IGNORECASE)
        metin = re.sub(r'\|\s*Detail$', '', metin, flags=re.IGNORECASE)
        metin = re.sub(r'[<>"\'|]', '', metin)
        metin = re.sub(r'\s+', ' ', metin)
        
        return metin.strip()

    def _link_tipini_belirle(self, link: str) -> str:
        """Link tipini belirler"""
        if '.m3u8' in link.lower():
            return 'hls'
        elif '.mp4' in link.lower():
            return 'mp4'
        elif '.mpd' in link.lower():
            return 'dash'
        else:
            return 'unknown'

    def m3u_olustur(self, linkler: List[Dict], dosya_adi: str = None):
        """Bulunan linklerden M3U playlist oluşturur"""
        if not dosya_adi:
            tarih = datetime.now().strftime('%Y%m%d_%H%M%S')
            dosya_adi = f"streamtest_{tarih}.m3u"
        
        # Çıktı klasörünü oluştur
        os.makedirs(self.output_dir, exist_ok=True)
        dosya_yolu = os.path.join(self.output_dir, dosya_adi)
        
        with open(dosya_yolu, 'w', encoding='utf-8') as f:
            f.write("#EXTM3U\n")
            f.write(f"# {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - streamtest.in/logs'dan otomatik oluşturuldu (GitHub Actions)\n")
            f.write(f"# Toplam {len(linkler)} yayın bulundu\n\n")
            
            for link in linkler:
                f.write(f'#EXTINF:-1 tvg-logo="" group-title="{link["tip"].upper()}",{link["kanal_adi"]}\n')
                f.write(f"{link['url']}\n\n")
        
        print(f"✅ {len(linkler)} yayın '{dosya_yolu}' dosyasına kaydedildi")
        return dosya_yolu

    def arsivi_guncelle(self, yeni_linkler: List[Dict]):
        """Link arşivini günceller"""
        eski_linkler = []
        
        # Eski arşivi yükle
        if os.path.exists(self.archive_file):
            try:
                with open(self.archive_file, 'r', encoding='utf-8') as f:
                    eski_linkler = json.load(f)
            except:
                pass
        
        # Yeni linkleri ekle
        tum_linkler = eski_linkler + yeni_linkler
        
        # URL bazlı benzersiz yap (en son eklenen kalsın)
        unique = {}
        for link in tum_linkler:
            unique[link['url']] = link
        
        # Tekrar kaydet
        os.makedirs(self.output_dir, exist_ok=True)
        with open(self.archive_file, 'w', encoding='utf-8') as f:
            json.dump(list(unique.values()), f, indent=2, ensure_ascii=False)
        
        print(f"📚 Arşiv güncellendi: {len(unique)} benzersiz link")

    def calistir(self):
        """Ana çalıştırma fonksiyonu"""
        print("🔍 streamtest.in/logs taranıyor...")
        
        html = self.sayfayi_getir()
        if not html:
            return False
        
        print("📡 Linkler ve kanal bilgileri çıkarılıyor...")
        linkler = self.linkleri_ve_kanallari_bul(html)
        
        if not linkler:
            print("⚠️ Hiç link bulunamadı!")
            return False
        
        print(f"✅ {len(linkler)} link bulundu")
        
        # M3U oluştur
        m3u_dosyasi = self.m3u_olustur(linkler)
        
        # Ana M3U olarak da kaydet (son güncel)
        ana_m3u = os.path.join(self.output_dir, "son_yayinlar.m3u")
        with open(ana_m3u, 'w', encoding='utf-8') as f:
            with open(m3u_dosyasi, 'r', encoding='utf-8') as kaynak:
                f.write(kaynak.read())
        
        # Arşivi güncelle
        self.arsivi_guncelle(linkler)
        
        return True

if __name__ == "__main__":
    scraper = StreamTestScraper()
    basarili = scraper.calistir()
    sys.exit(0 if basarili else 1)
