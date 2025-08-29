# firebase_client.py - Gerçek Firebase ile
import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
from typing import Dict, Any, List, Optional
import json
import os


class FirebaseClient:
    def __init__(self):
        """Firebase bağlantısını başlat"""
        if not firebase_admin._apps:
            try:
                # Seçenek 1: Service Account Key dosyası (Önerilen)
                if os.path.exists("firebase-key.json"):
                    cred = credentials.Certificate("firebase-key.json")
                    firebase_admin.initialize_app(cred)
                    st.success("🔥 Firebase (Service Account) bağlantısı başarılı!")

                # Seçenek 2: Streamlit secrets'tan
                elif "FIREBASE_SERVICE_ACCOUNT" in st.secrets:
                    firebase_secrets = st.secrets["FIREBASE_SERVICE_ACCOUNT"]
                    cred = credentials.Certificate(dict(firebase_secrets))
                    firebase_admin.initialize_app(cred)
                    st.success("🔥 Firebase (Secrets) bağlantısı başarılı!")

                # Seçenek 3: Test modu (yerel JSON)
                else:
                    st.warning("⚠️ Firebase bulunamadı, yerel test modu aktif!")
                    self._use_local_storage = True
                    self.data_file = "inventory_database.json"
                    self._init_local_database()
                    return

            except Exception as e:
                st.error(f"❌ Firebase başlatma hatası: {str(e)}")
                st.info("Yerel test moduna geçiliyor...")
                self._use_local_storage = True
                self.data_file = "inventory_database.json"
                self._init_local_database()
                return

        self._use_local_storage = False
        self.db = firestore.client()

        # Test kullanıcıları
        self.test_users = {
            "test@test.com": {"password": "123456", "uid": "test_user_123"},
            "admin@admin.com": {"password": "admin123", "uid": "admin_user_456"}
        }

    def _init_local_database(self):
        """Yerel database başlat"""
        if not os.path.exists(self.data_file):
            initial_data = {
                "users": {
                    "test@test.com": {"password": "123456", "uid": "test_user_123"},
                    "admin@admin.com": {"password": "admin123", "uid": "admin_user_456"}
                },
                "inventory": {}
            }
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(initial_data, f, ensure_ascii=False, indent=2)

    def _load_local_data(self):
        """Yerel veriyi yükle"""
        try:
            with open(self.data_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {"users": {}, "inventory": {}}

    def _save_local_data(self, data):
        """Yerel veriyi kaydet"""
        with open(self.data_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def sign_in(self, email: str, password: str) -> Optional[Dict]:
        """Kullanıcı girişi"""
        if self._use_local_storage:
            data = self._load_local_data()
            users = data.get("users", {})
            if email in users and users[email]["password"] == password:
                return {"localId": users[email]["uid"], "email": email}
        else:
            # Firebase Authentication burada olacak
            if email in self.test_users and self.test_users[email]["password"] == password:
                return {"localId": self.test_users[email]["uid"], "email": email}

        st.error("❌ E-posta veya şifre hatalı!")
        return None

    def get_inventory(self, user_id: str) -> List[Dict]:
        """Kullanıcının envanterini getir"""
        if self._use_local_storage:
            data = self._load_local_data()
            inventory = data.get("inventory", {}).get(user_id, {})
            items = []
            for item_id, item_data in inventory.items():
                item_data['id'] = item_id
                items.append(item_data)
            return items
        else:
            # Firebase Firestore'dan veri çek
            try:
                docs = self.db.collection('inventory').where('user_id', '==', user_id).stream()
                items = []
                for doc in docs:
                    item = doc.to_dict()
                    item['id'] = doc.id
                    items.append(item)
                return items
            except Exception as e:
                st.error(f"❌ Envanter getirme hatası: {str(e)}")
                return []

    def add_item(self, user_id: str, item: Dict) -> bool:
        """Yeni ürün ekle"""
        if self._use_local_storage:
            try:
                data = self._load_local_data()
                if "inventory" not in data:
                    data["inventory"] = {}
                if user_id not in data["inventory"]:
                    data["inventory"][user_id] = {}

                import time
                item_id = f"item_{int(time.time() * 1000)}"
                item['created_at'] = time.time()
                data["inventory"][user_id][item_id] = item
                self._save_local_data(data)
                return True
            except Exception as e:
                st.error(f"❌ Ürün ekleme hatası: {str(e)}")
                return False
        else:
            # Firebase Firestore'a ekle
            try:
                item['user_id'] = user_id
                item['created_at'] = firestore.SERVER_TIMESTAMP
                self.db.collection('inventory').add(item)
                return True
            except Exception as e:
                st.error(f"❌ Ürün ekleme hatası: {str(e)}")
                return False

    def delete_item(self, user_id: str, item_id: str) -> bool:
        """Ürün sil"""
        if self._use_local_storage:
            try:
                data = self._load_local_data()
                if (user_id in data.get("inventory", {}) and
                        item_id in data["inventory"][user_id]):
                    del data["inventory"][user_id][item_id]
                    self._save_local_data(data)
                    return True
                return False
            except Exception as e:
                st.error(f"❌ Ürün silme hatası: {str(e)}")
                return False
        else:
            # Firebase'dan sil
            try:
                self.db.collection('inventory').document(item_id).delete()
                return True
            except Exception as e:
                st.error(f"❌ Ürün silme hatası: {str(e)}")
                return False


@st.cache_resource
def get_firebase():
    return FirebaseClient()