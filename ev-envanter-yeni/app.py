# app.py
import streamlit as st
from firebase_client import get_firebase
from ai_client import get_gemini
from utils import *
import pandas as pd
from datetime import datetime, timedelta
import plotly.express as px

# Sayfa konfigürasyonu
st.set_page_config(
    page_title="🏠 Ev Envanter Sistemi",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS stilleri
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 10px;
        border-left: 5px solid #1f77b4;
    }
    .expiry-warning {
        background-color: #fff3cd;
        border: 1px solid #ffeaa7;
        border-radius: 5px;
        padding: 10px;
        margin: 10px 0;
    }
    .expiry-critical {
        background-color: #f8d7da;
        border: 1px solid #f5c6cb;
        border-radius: 5px;
        padding: 10px;
        margin: 10px 0;
    }
</style>
""", unsafe_allow_html=True)


def init_session_state():
    """Session state'i başlat"""
    if 'user' not in st.session_state:
        st.session_state.user = None
    if 'firebase' not in st.session_state:
        st.session_state.firebase = get_firebase()
    if 'gemini' not in st.session_state:
        st.session_state.gemini = get_gemini()


def login_page():
    """Giriş sayfası"""
    st.markdown('<h1 class="main-header">🏠 Ev Envanter Sistemi</h1>', unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        st.markdown("### 🔐 Giriş Yap")

        tab1, tab2 = st.tabs(["Giriş", "Kayıt Ol"])

        with tab1:
            with st.form("login_form"):
                email = st.text_input("📧 E-posta", placeholder="ornek@email.com")
                password = st.text_input("🔒 Şifre", type="password")
                submit = st.form_submit_button("Giriş Yap", use_container_width=True)

                if submit:
                    if email and password:
                        user = st.session_state.firebase.sign_in(email, password)
                        if user:
                            st.session_state.user = user
                            st.success("✅ Başarıyla giriş yaptınız!")
                            st.rerun()
                    else:
                        st.error("❌ Lütfen tüm alanları doldurun!")

        with tab2:
            with st.form("register_form"):
                new_email = st.text_input("📧 E-posta", placeholder="ornek@email.com", key="reg_email")
                new_password = st.text_input("🔒 Şifre (min 6 karakter)", type="password", key="reg_password")
                confirm_password = st.text_input("🔒 Şifre Tekrar", type="password", key="reg_confirm")
                register = st.form_submit_button("Kayıt Ol", use_container_width=True)

                if register:
                    if new_email and new_password and confirm_password:
                        if new_password == confirm_password:
                            user = st.session_state.firebase.sign_up(new_email, new_password)
                            if user:
                                st.session_state.user = user
                                st.success("✅ Başarıyla kayıt oldunuz!")
                                st.rerun()
                        else:
                            st.error("❌ Şifreler eşleşmiyor!")
                    else:
                        st.error("❌ Lütfen tüm alanları doldurun!")

        # Test kullanıcı bilgileri
        st.info("""
        **Test Kullanıcıları:**
        - E-posta: test@test.com, Şifre: 123456
        - E-posta: admin@admin.com, Şifre: admin123
        """)


def main_dashboard():
    """Ana dashboard"""
    # Sidebar
    with st.sidebar:
        st.markdown(f"### 👋 Hoş geldin!")
        st.markdown(f"**{st.session_state.user['email']}**")

        if st.button("🚪 Çıkış Yap", use_container_width=True):
            st.session_state.user = None
            st.rerun()

        st.markdown("---")

        # Navigasyon
        page = st.selectbox(
            "📍 Sayfa Seç",
            ["🏠 Ana Sayfa", "📦 Envanter", "⚠️ Uyarılar", "🍽️ Tarif Önerileri"]
        )

    # Ana içerik
    if page == "🏠 Ana Sayfa":
        show_dashboard()
    elif page == "📦 Envanter":
        show_inventory()
    elif page == "⚠️ Uyarılar":
        show_warnings()
    elif page == "🍽️ Tarif Önerileri":
        show_recipes()


def show_dashboard():
    """Ana dashboard göster"""
    st.markdown('<h1 class="main-header">🏠 Ev Envanter Dashboard</h1>', unsafe_allow_html=True)

    # Envanter verilerini al
    user_id = st.session_state.user['localId']
    inventory = st.session_state.firebase.get_inventory(user_id)
    stats = calculate_inventory_stats(inventory)

    # Üst metrikler
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            label="📦 Toplam Ürün",
            value=stats['total_items']
        )

    with col2:
        st.metric(
            label="⚠️ Yakında Bitecek",
            value=stats['expiring_soon'],
            delta=f"-{stats['expired']} süresi geçmiş" if stats['expired'] > 0 else None
        )

    with col3:
        st.metric(
            label="📉 Stok Azalıyor",
            value=stats['low_stock']
        )

    with col4:
        st.metric(
            label="📊 Kategori Sayısı",
            value=len(stats['categories'])
        )

    st.markdown("---")

    # Grafikler
    col1, col2 = st.columns(2)

    with col1:
        if stats['categories']:
            st.subheader("📊 Kategori Dağılımı")
            fig = px.pie(
                values=list(stats['categories'].values()),
                names=list(stats['categories'].keys()),
                title="Ürün Kategorileri"
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("📦 Henüz ürün eklenmemiş.")

    with col2:
        if inventory:
            st.subheader("📅 Son Kullanma Tarihi Durumu")

            # Son kullanma durumu analizi
            expiry_status = {"İyi": 0, "Yaklaşıyor": 0, "Kritik": 0, "Geçmiş": 0}

            for item in inventory:
                expiry_date = item.get('expiry_date', '')
                if expiry_date:
                    days_left = days_until_expiry(expiry_date)
                    if days_left < 0:
                        expiry_status["Geçmiş"] += 1
                    elif days_left <= 3:
                        expiry_status["Kritik"] += 1
                    elif days_left <= 7:
                        expiry_status["Yaklaşıyor"] += 1
                    else:
                        expiry_status["İyi"] += 1

            fig = px.bar(
                x=list(expiry_status.keys()),
                y=list(expiry_status.values()),
                title="Son Kullanma Tarihi Durumu",
                color=list(expiry_status.values()),
                color_continuous_scale="RdYlGn_r"
            )
            st.plotly_chart(fig, use_container_width=True)

    # Son eklenen ürünler
    if inventory:
        st.subheader("🆕 Son Eklenen Ürünler")
        recent_items = sorted(inventory, key=lambda x: x.get('created_at', ''), reverse=True)[:5]

        for item in recent_items:
            col1, col2, col3, col4 = st.columns([3, 2, 2, 1])

            with col1:
                st.write(f"**{item.get('name', 'Bilinmeyen')}**")
            with col2:
                st.write(f"📦 {item.get('quantity', 0)} {item.get('unit', 'adet')}")
            with col3:
                expiry_date = item.get('expiry_date', '')
                if expiry_date:
                    days_left = days_until_expiry(expiry_date)
                    emoji, status, color = get_expiry_status(days_left)
                    st.write(f"{emoji} {format_date_turkish(expiry_date)}")
            with col4:
                st.write(f"🏷️ {item.get('category', 'Diğer')}")


def show_inventory():
    """Envanter sayfası"""
    st.markdown('<h1 class="main-header">📦 Envanter Yönetimi</h1>', unsafe_allow_html=True)

    user_id = st.session_state.user['localId']

    # Yeni ürün ekleme formu
    with st.expander("➕ Yeni Ürün Ekle", expanded=False):
        with st.form("add_item_form"):
            col1, col2 = st.columns(2)

            with col1:
                name = st.text_input("🏷️ Ürün Adı", placeholder="Örn: Domates")
                category = st.selectbox("📂 Kategori", CATEGORIES)
                quantity = st.number_input("📦 Miktar", min_value=0.0, value=1.0, step=0.1)
                unit = st.selectbox("📏 Birim", UNITS)

            with col2:
                expiry_date = st.date_input("📅 Son Kullanma Tarihi", value=datetime.now() + timedelta(days=7))
                location = st.text_input("📍 Konum", placeholder="Örn: Buzdolabı, Dolap")
                notes = st.text_area("📝 Notlar", placeholder="Ek bilgiler...")

            submit = st.form_submit_button("✅ Ürün Ekle", use_container_width=True)

            if submit:
                if name:
                    item = {
                        'name': name,
                        'category': category,
                        'quantity': quantity,
                        'unit': unit,
                        'expiry_date': expiry_date.strftime('%Y-%m-%d'),
                        'location': location,
                        'notes': notes
                    }

                    if st.session_state.firebase.add_item(user_id, item):
                        st.success("✅ Ürün başarıyla eklendi!")
                        st.rerun()
                else:
                    st.error("❌ Ürün adı gereklidir!")

    # Mevcut ürünleri listele
    inventory = st.session_state.firebase.get_inventory(user_id)

    if inventory:
        st.subheader(f"📋 Mevcut Ürünler ({len(inventory)} adet)")

        # Filtreleme
        col1, col2, col3 = st.columns(3)

        with col1:
            filter_category = st.selectbox("🔍 Kategori Filtresi", ["Tümü"] + CATEGORIES)
        with col2:
            filter_expiry = st.selectbox("⏰ Son Kullanma Filtresi",
                                         ["Tümü", "Bugün Bitiyor", "3 Gün İçinde", "1 Hafta İçinde", "Süresi Geçmiş"])
        with col3:
            search_term = st.text_input("🔍 Ürün Ara", placeholder="Ürün adı...")

        # Filtreleme uygula
        filtered_inventory = inventory.copy()

        if filter_category != "Tümü":
            filtered_inventory = [item for item in filtered_inventory if item.get('category') == filter_category]

        if search_term:
            filtered_inventory = [item for item in filtered_inventory
                                  if search_term.lower() in item.get('name', '').lower()]

        if filter_expiry != "Tümü":
            temp_filtered = []
            for item in filtered_inventory:
                expiry_date = item.get('expiry_date', '')
                if expiry_date:
                    days_left = days_until_expiry(expiry_date)
                    if filter_expiry == "Bugün Bitiyor" and days_left == 0:
                        temp_filtered.append(item)
                    elif filter_expiry == "3 Gün İçinde" and 0 <= days_left <= 3:
                        temp_filtered.append(item)
                    elif filter_expiry == "1 Hafta İçinde" and 0 <= days_left <= 7:
                        temp_filtered.append(item)
                    elif filter_expiry == "Süresi Geçmiş" and days_left < 0:
                        temp_filtered.append(item)
            filtered_inventory = temp_filtered

        # Ürünleri göster
        for item in filtered_inventory:
            with st.container():
                col1, col2, col3, col4, col5 = st.columns([3, 2, 2, 2, 1])

                with col1:
                    st.write(f"**{item.get('name', 'Bilinmeyen')}**")
                    if item.get('notes'):
                        st.caption(f"📝 {item.get('notes')}")

                with col2:
                    st.write(f"📦 {item.get('quantity', 0)} {item.get('unit', 'adet')}")
                    st.caption(f"🏷️ {item.get('category', 'Diğer')}")

                with col3:
                    expiry_date = item.get('expiry_date', '')
                    if expiry_date:
                        days_left = days_until_expiry(expiry_date)
                        emoji, status, color = get_expiry_status(days_left)
                        st.write(f"{emoji} {format_date_turkish(expiry_date)}")
                        st.caption(f"({days_left} gün kaldı)" if days_left >= 0 else "(Süresi geçmiş)")

                with col4:
                    if item.get('location'):
                        st.write(f"📍 {item.get('location')}")

                with col5:
                    if st.button("🗑️", key=f"delete_{item['id']}", help="Sil"):
                        if st.session_state.firebase.delete_item(user_id, item['id']):
                            st.rerun()

                st.markdown("---")
    else:
        st.info("📦 Henüz ürün eklenmemiş. Yukarıdaki formu kullanarak ürün ekleyebilirsiniz.")


def show_warnings():
    """Uyarılar sayfası"""
    st.markdown('<h1 class="main-header">⚠️ Son Kullanma Tarihi Uyarıları</h1>', unsafe_allow_html=True)

    user_id = st.session_state.user['localId']
    inventory = st.session_state.firebase.get_inventory(user_id)

    if not inventory:
        st.info("📦 Henüz ürün eklenmemiş.")
        return

    # Uyarı kategorileri
    expired_items = []
    critical_items = []
    warning_items = []

    for item in inventory:
        expiry_date = item.get('expiry_date', '')
        if expiry_date:
            days_left = days_until_expiry(expiry_date)
            if days_left < 0:
                expired_items.append(item)
            elif days_left <= 3:
                critical_items.append(item)
            elif days_left <= 7:
                warning_items.append(item)

    # Süresi geçmiş ürünler
    if expired_items:
        st.markdown("### 🔴 Süresi Geçmiş Ürünler")
        for item in expired_items:
            st.markdown(f"""
            <div class="expiry-critical">
                <strong>🔴 {item.get('name', 'Bilinmeyen')}</strong><br>
                📅 Son Kullanma: {format_date_turkish(item.get('expiry_date', ''))}<br>
                📦 Miktar: {item.get('quantity', 0)} {item.get('unit', 'adet')}<br>
                📍 Konum: {item.get('location', 'Belirtilmemiş')}
            </div>
            """, unsafe_allow_html=True)

    # Kritik ürünler (3 gün içinde)
    if critical_items:
        st.markdown("### 🟡 Kritik Uyarı (3 Gün İçinde)")
        for item in critical_items:
            days_left = days_until_expiry(item.get('expiry_date', ''))
            st.markdown(f"""
            <div class="expiry-critical">
                <strong>🟡 {item.get('name', 'Bilinmeyen')}</strong><br>
                📅 Son Kullanma: {format_date_turkish(item.get('expiry_date', ''))} ({days_left} gün kaldı)<br>
                📦 Miktar: {item.get('quantity', 0)} {item.get('unit', 'adet')}<br>
                📍 Konum: {item.get('location', 'Belirtilmemiş')}
            </div>
            """, unsafe_allow_html=True)

    # Uyarı ürünleri (1 hafta içinde)
    if warning_items:
        st.markdown("### 🟠 Uyarı (1 Hafta İçinde)")
        for item in warning_items:
            days_left = days_until_expiry(item.get('expiry_date', ''))
            st.markdown(f"""
            <div class="expiry-warning">
                <strong>🟠 {item.get('name', 'Bilinmeyen')}</strong><br>
                📅 Son Kullanma: {format_date_turkish(item.get('expiry_date', ''))} ({days_left} gün kaldı)<br>
                📦 Miktar: {item.get('quantity', 0)} {item.get('unit', 'adet')}<br>
                📍 Konum: {item.get('location', 'Belirtilmemiş')}
            </div>
            """, unsafe_allow_html=True)

    # Uyarı yoksa
    if not expired_items and not critical_items and not warning_items:
        st.success("✅ Harika! Şu anda acil uyarı gerektiren ürün bulunmuyor.")
        st.balloons()


def show_recipes():
    """Gelişmiş tarif önerileri sayfası"""
    st.markdown('<h1 class="main-header">🍽️ AI Tarif Önerileri</h1>', unsafe_allow_html=True)

    user_id = st.session_state.user['localId']
    inventory = st.session_state.firebase.get_inventory(user_id)

    if not inventory:
        st.info("📦 Henüz ürün eklenmemiş. Tarif önerisi için önce ürün ekleyin.")
        return

    # Tab sistemi
    tab1, tab2 = st.tabs(["⏰ Acil Tarifler", "🎯 Özel Tarif Oluştur"])

    with tab1:
        st.markdown("### ⏰ Son Kullanma Tarihi Yaklaşan Ürünler İçin Tarifler")

        # Son kullanma tarihi yaklaşan ürünleri bul
        expiring_items = get_expiring_items(inventory, days_threshold=7)

        if expiring_items:
            # Yaklaşan ürünleri göster
            st.markdown("**🚨 Öncelikle bunları değerlendirin:**")

            cols = st.columns(min(len(expiring_items), 4))
            for i, item in enumerate(expiring_items[:4]):
                with cols[i % 4]:
                    days_left = item.get('days_left', 0)
                    emoji, status, color = get_expiry_status(days_left)
                    st.metric(
                        label=f"{emoji} {item.get('name', 'Bilinmeyen')}",
                        value=f"{days_left} gün",
                        delta=f"{item.get('quantity', 0)} {item.get('unit', 'adet')}"
                    )

            st.markdown("---")

            # AI tarif önerileri
            col1, col2 = st.columns([3, 1])
            with col1:
                st.markdown("### 🤖 AI Tarif Önerileri")
            with col2:
                if st.button("🔄 Yeni Tarifler", use_container_width=True):
                    st.cache_resource.clear()

            if st.button("🤖 AI Tarif Önerileri Al", use_container_width=True, type="primary"):
                with st.spinner("🤖 AI tarifler hazırlanıyor..."):
                    recipes = st.session_state.gemini.get_recipe_suggestions(inventory, expiring_items)
                    st.markdown(recipes)
        else:
            st.success("✅ Harika! Şu anda yakında son kullanma tarihi gelecek ürün bulunmuyor.")
            st.balloons()

    with tab2:
        st.markdown("### 🎯 Kendi Tarifini Oluştur")
        st.info("💡 Dolabınızdaki malzemeleri seçin, size özel tarifler önerelim!")

        # Malzeme seçimi
        col1, col2 = st.columns([2, 1])

        with col1:
            # Kategoriye göre malzeme seçimi
            categories = {}
            for item in inventory:
                category = item.get('category', 'Diğer')
                if category not in categories:
                    categories[category] = []
                categories[category].append(item.get('name', 'Bilinmeyen'))

            selected_items = []

            st.markdown("**📦 Malzemelerinizi Seçin:**")

            for category, items in categories.items():
                with st.expander(f"🏷️ {category} ({len(items)} ürün)"):
                    for item in items:
                        if st.checkbox(f"{item}", key=f"recipe_{item}"):
                            selected_items.append(item)

        with col2:
            st.markdown("**🍽️ Mutfak Türü:**")
            cuisine_type = st.selectbox(
                "Hangi mutfak?",
                ["Türk", "İtalyan", "Çin", "Meksika", "Hint", "Akdeniz", "Vejetaryen"]
            )

            st.markdown("**⏱️ Pişirme Süresi:**")
            cooking_time = st.selectbox(
                "Ne kadar sürede?",
                ["Fark etmez", "15 dakika altı", "15-30 dakika", "30-60 dakika", "1 saat üzeri"]
            )

            st.markdown("**👥 Kaç Kişilik:**")
            serving_size = st.selectbox(
                "Kaç kişi için?",
                ["Fark etmez", "1 kişilik", "2-3 kişilik", "4-6 kişilik", "6+ kişilik"]
            )

        # Seçilen malzemeleri göster
        if selected_items:
            st.markdown("### 🛒 Seçilen Malzemeler:")
            selected_text = ", ".join(selected_items)
            st.success(f"✅ **{len(selected_items)} malzeme seçildi:** {selected_text}")

            # Özel tarif önerisi al
            if st.button("🎯 Özel Tarif Önerisi Al", use_container_width=True, type="primary"):
                with st.spinner("🤖 Size özel tarifler hazırlanıyor..."):
                    custom_recipes = st.session_state.gemini.get_custom_recipe_suggestions(
                        selected_items, cuisine_type
                    )
                    st.markdown("### 🍽️ Size Özel Tarifler:")
                    st.markdown(custom_recipes)
        else:
            st.info("👆 Yukarıdan en az bir malzeme seçin!")

    # Genel malzeme listesi (alt kısımda)
    st.markdown("---")
    st.markdown("### 📦 Tüm Malzemeleriniz")

    # Kategorilere göre grupla
    categories = {}
    for item in inventory:
        category = item.get('category', 'Diğer')
        if category not in categories:
            categories[category] = []
        categories[category].append({
            'name': item.get('name', 'Bilinmeyen'),
            'quantity': item.get('quantity', 0),
            'unit': item.get('unit', 'adet'),
            'expiry_date': item.get('expiry_date', ''),
            'days_left': days_until_expiry(item.get('expiry_date', '')) if item.get('expiry_date') else 999
        })

    # Kategorileri göster
    cols = st.columns(min(len(categories), 3))
    for i, (category, items) in enumerate(categories.items()):
        with cols[i % 3]:
            with st.expander(f"🏷️ {category} ({len(items)} ürün)"):
                for item in items:
                    emoji, status, color = get_expiry_status(item['days_left'])
                    st.write(f"{emoji} **{item['name']}** - {item['quantity']} {item['unit']}")
                    if item['expiry_date']:
                        st.caption(f"SKT: {format_date_turkish(item['expiry_date'])}")

def main():
    """Ana fonksiyon"""
    init_session_state()

    if st.session_state.user is None:
        login_page()
    else:
        main_dashboard()


if __name__ == "__main__":
    main()