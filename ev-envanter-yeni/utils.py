# utils.py
from datetime import datetime, timedelta
from typing import List, Dict, Tuple
import streamlit as st


def days_until_expiry(expiry_date_str: str) -> int:
    """Son kullanma tarihine kaç gün kaldığını hesapla"""
    try:
        expiry_date = datetime.strptime(expiry_date_str, '%Y-%m-%d')
        today = datetime.now()
        return (expiry_date - today).days
    except:
        return 999


def get_expiry_status(days_left: int) -> Tuple[str, str, str]:
    """Son kullanma durumuna göre emoji, durum ve renk döndür"""
    if days_left < 0:
        return "🔴", "Süresi Geçmiş", "red"
    elif days_left == 0:
        return "🟠", "Bugün Bitiyor", "orange"
    elif days_left <= 3:
        return "🟡", "Kritik (3 gün)", "orange"
    elif days_left <= 7:
        return "🟡", "Yaklaşıyor (1 hafta)", "yellow"
    elif days_left <= 30:
        return "🟢", "İyi (1 ay)", "green"
    else:
        return "🟢", "İyi", "green"


def calculate_inventory_stats(inventory: List[Dict]) -> Dict:
    """Envanter istatistiklerini hesapla"""
    if not inventory:
        return {
            'total_items': 0,
            'expiring_soon': 0,
            'expired': 0,
            'low_stock': 0,
            'categories': {}
        }

    total_items = len(inventory)
    expiring_soon = 0
    expired = 0
    low_stock = 0
    categories = {}

    for item in inventory:
        # Kategori sayısı
        category = item.get('category', 'Diğer')
        categories[category] = categories.get(category, 0) + 1

        # Son kullanma tarihi kontrolü
        expiry_date = item.get('expiry_date', '')
        if expiry_date:
            days_left = days_until_expiry(expiry_date)
            if days_left < 0:
                expired += 1
            elif days_left <= 7:
                expiring_soon += 1

        # Stok kontrolü
        quantity = item.get('quantity', 0)
        if quantity <= 5:
            low_stock += 1

    return {
        'total_items': total_items,
        'expiring_soon': expiring_soon,
        'expired': expired,
        'low_stock': low_stock,
        'categories': categories
    }


def get_expiring_items(inventory: List[Dict], days_threshold: int = 7) -> List[Dict]:
    """Belirtilen gün içinde son kullanma tarihi gelecek ürünleri getir"""
    expiring_items = []

    for item in inventory:
        expiry_date = item.get('expiry_date', '')
        if expiry_date:
            days_left = days_until_expiry(expiry_date)
            if 0 <= days_left <= days_threshold:
                item['days_left'] = days_left
                expiring_items.append(item)

    # Gün sayısına göre sırala
    expiring_items.sort(key=lambda x: x['days_left'])
    return expiring_items


def format_date_turkish(date_str: str) -> str:
    """Tarihi Türkçe formatta göster"""
    try:
        date_obj = datetime.strptime(date_str, '%Y-%m-%d')
        months = [
            'Ocak', 'Şubat', 'Mart', 'Nisan', 'Mayıs', 'Haziran',
            'Temmuz', 'Ağustos', 'Eylül', 'Ekim', 'Kasım', 'Aralık'
        ]
        return f"{date_obj.day} {months[date_obj.month - 1]} {date_obj.year}"
    except:
        return date_str


# Kategori listesi
CATEGORIES = [
    "Meyve & Sebze",
    "Et & Tavuk & Balık",
    "Süt Ürünleri",
    "Tahıl & Baklagiller",
    "İçecekler",
    "Atıştırmalık",
    "Donmuş Gıda",
    "Konserve",
    "Baharat & Sos",
    "Temizlik",
    "Kişisel Bakım",
    "Diğer"
]

# Birim listesi
UNITS = [
    "adet",
    "kg",
    "gram",
    "litre",
    "ml",
    "paket",
    "kutu",
    "şişe",
    "poşet"
]