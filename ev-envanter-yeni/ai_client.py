# ai_client.py - Gelişmiş AI Tarif Sistemi
import streamlit as st
from typing import List, Dict
import random

# Gemini AI'ı dene, yoksa gelişmiş mock kullan
try:
    import google.generativeai as genai

    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False


class GeminiClient:
    def __init__(self):
        """Gemini AI'ı başlat"""
        self.use_real_ai = False

        if GEMINI_AVAILABLE:
            try:
                api_key = st.secrets.get("GEMINI_API_KEY")
                if api_key and api_key != "your-gemini-api-key-here" and api_key != "test-mode":
                    genai.configure(api_key=api_key)
                    self.model = genai.GenerativeModel('gemini-2.0-flash-exp')
                    self.use_real_ai = True
                    st.success("🤖 Gemini AI bağlantısı başarılı!")
                else:
                    st.info("🤖 Gelişmiş Mock AI kullanılıyor (test modu)")
            except Exception as e:
                st.warning(f"⚠️ Gemini AI başlatma hatası: {str(e)}")
                st.info("Gelişmiş Mock AI kullanılıyor.")
        else:
            st.info("🤖 Gelişmiş Mock AI kullanılıyor")

    def get_recipe_suggestions(self, inventory_items: List[Dict], expiring_items: List[Dict]) -> str:
        """Tarif önerileri"""
        if self.use_real_ai:
            return self._get_real_ai_recipes(inventory_items, expiring_items)
        else:
            return self._get_smart_mock_recipes(inventory_items, expiring_items)

    def get_custom_recipe_suggestions(self, selected_items: List[str], cuisine_type: str = "Türk") -> str:
        """Seçilen malzemeler için özel tarif önerileri"""
        if self.use_real_ai:
            return self._get_real_custom_recipes(selected_items, cuisine_type)
        else:
            return self._get_smart_custom_recipes(selected_items, cuisine_type)

    def _get_real_ai_recipes(self, inventory_items: List[Dict], expiring_items: List[Dict]) -> str:
        """Gerçek AI'dan tarif al"""
        try:
            expiring_list = [
                f"- {item['name']} (SKT: {item['expiry_date']}, {item.get('quantity', 0)} {item.get('unit', 'adet')})"
                for item in expiring_items]
            all_items = [f"- {item['name']} ({item.get('quantity', 0)} {item.get('unit', 'adet')})" for item in
                         inventory_items]

            prompt = f"""
            Bir ev envanteri uygulamasında kullanıcıya yardım ediyorsun.

            YAKINDA SON KULLANMA TARİHİ GEÇECEKLERİ (ÖNCELİK):
            {chr(10).join(expiring_list)}

            TÜM MEVCUT MALZEMELER:
            {chr(10).join(all_items)}

            Lütfen:
            1. Öncelikle son kullanma tarihi yaklaşan malzemeleri kullanacak 3-4 tarif öner
            2. Türkçe tarif isimleri ver
            3. Her tarif için malzeme listesi ve detaylı yapım talimatı ekle
            4. Pratik ve kolay yapılabilir tarifler olsun
            5. Pişirme sürelerini belirt
            6. Kaç kişilik olduğunu yaz

            Format:
            ## 🍽️ [Tarif Adı] (X kişilik, Y dakika)
            **Malzemeler:**
            - [malzeme 1]
            - [malzeme 2]

            **Yapılışı:**
            1. [adım 1]
            2. [adım 2]

            **İpucu:** [özel ipucu]
            """

            response = self.model.generate_content(prompt)
            return response.text

        except Exception as e:
            st.error(f"❌ AI tarif hatası: {str(e)}")
            return self._get_smart_mock_recipes(inventory_items, expiring_items)

    def _get_real_custom_recipes(self, selected_items: List[str], cuisine_type: str) -> str:
        """Gerçek AI'dan özel tarif al"""
        try:
            items_text = ", ".join(selected_items)

            prompt = f"""
            Kullanıcı şu malzemeleri seçti: {items_text}
            Mutfak türü: {cuisine_type}

            Bu malzemelerle yapılabilecek 3-4 farklı {cuisine_type} tarifi öner.

            Kurallar:
            1. Sadece seçilen malzemeleri ana ingredient olarak kullan
            2. Temel baharat ve yağ gibi her evde bulunan malzemeler eklenebilir
            3. Detaylı yapım talimatı ver
            4. Pişirme süresi ve kişi sayısını belirt
            5. Türkçe yaz

            Format:
            ## 🍽️ [Tarif Adı] (X kişilik, Y dakika)
            **Ana Malzemeler:** {items_text}
            **Ek Malzemeler:** [temel malzemeler]
            **Yapılışı:**
            1. [detaylı adım]
            2. [detaylı adım]
            **İpucu:** [özel ipucu]
            """

            response = self.model.generate_content(prompt)
            return response.text

        except Exception as e:
            st.error(f"❌ Özel tarif hatası: {str(e)}")
            return self._get_smart_custom_recipes(selected_items, cuisine_type)

    def _get_smart_mock_recipes(self, inventory_items: List[Dict], expiring_items: List[Dict]) -> str:
        """Gelişmiş mock tarif önerileri"""
        if not expiring_items:
            return "✅ Şu anda son kullanma tarihi yaklaşan ürün bulunmuyor. Tüm ürünleriniz taze!"

        recipes = []
        recipe_database = self._get_recipe_database()

        for item in expiring_items[:3]:
            item_name = item.get('name', '').lower()
            quantity = item.get('quantity', 0)
            unit = item.get('unit', 'adet')

            # Malzeme bazlı tarif seçimi
            matching_recipes = []
            for ingredient, recipe_list in recipe_database.items():
                if ingredient in item_name:
                    matching_recipes.extend(recipe_list)

            if matching_recipes:
                recipe = random.choice(matching_recipes)
                recipe_text = recipe.format(
                    item_name=item.get('name', 'Malzeme'),
                    quantity=quantity,
                    unit=unit
                )
                recipes.append(recipe_text)

        if not recipes:
            # Genel tarif önerisi
            recipes.append(f"""
## 🍽️ {expiring_items[0].get('name', 'Malzeme')} ile Özel Tarif (2-3 kişilik, 30 dakika)

**Ana Malzemeler:**
- {expiring_items[0].get('name', 'Malzeme')} ({expiring_items[0].get('quantity', 0)} {expiring_items[0].get('unit', 'adet')})
- Soğan (1 adet)
- Zeytinyağı (2 yemek kaşığı)
- Tuz, karabiber

**Yapılışı:**
1. {expiring_items[0].get('name', 'Malzeme')}yi temizleyip hazırlayın
2. Soğanı doğrayıp zeytinyağında kavurun
3. Ana malzemeyi ekleyip pişirin
4. Baharatlarla tatlandırıp servis edin

**İpucu:** Bu malzemeyi hızlıca değerlendirmek için ideal bir tarif!
""")

        return "\n---\n".join(recipes)

    def _get_smart_custom_recipes(self, selected_items: List[str], cuisine_type: str) -> str:
        """Seçilen malzemeler için akıllı tarif önerileri"""
        if not selected_items:
            return "Lütfen en az bir malzeme seçin."

        items_text = ", ".join(selected_items)

        # Malzeme kombinasyonlarına göre tarif önerileri
        recipes = []

        if len(selected_items) == 1:
            item = selected_items[0].lower()
            if 'domates' in item:
                recipes.append(f"""
## 🍅 Domates Salatası (2 kişilik, 10 dakika)
**Ana Malzemeler:** {items_text}
**Ek Malzemeler:** Soğan, zeytinyağı, limon, tuz
**Yapılışı:**
1. Domatesleri dilimleyin
2. İnce doğranmış soğan ekleyin
3. Zeytinyağı, limon ve tuz ile karıştırın
**İpucu:** Taze ve sağlıklı bir seçenek!
""")
            elif 'yumurta' in item:
                recipes.append(f"""
## 🍳 Sahanda Yumurta (1 kişilik, 5 dakika)
**Ana Malzemeler:** {items_text}
**Ek Malzemeler:** Tereyağı, tuz, karabiber
**Yapılışı:**
1. Tavayı ısıtın ve tereyağı ekleyin
2. Yumurtayı kırıp tavaya alın
3. Tuz ve karabiber serpip pişirin
**İpucu:** Hızlı ve pratik bir kahvaltı!
""")
            elif 'tavuk' in item:
                recipes.append(f"""
## 🍗 Tavuk Izgara (2 kişilik, 20 dakika)
**Ana Malzemeler:** {items_text}
**Ek Malzemeler:** Zeytinyağı, tuz, karabiber, kekik
**Yapılışı:**
1. Tavuğu marine edin
2. Izgarada veya tavada pişirin
3. Baharatlarla lezzetlendirin
**İpucu:** Salata ile servis edin!
""")
            elif 'mayonez' in item:
                recipes.append(f"""
## 🥗 Mayonezli Patates Salatası (3-4 kişilik, 15 dakika)
**Ana Malzemeler:** {items_text}
**Ek Malzemeler:** Patates, havuç, bezelye, turşu
**Yapılışı:**
1. Patatesleri haşlayın
2. Sebzeleri doğrayın
3. Mayonez ile karıştırın
**İpucu:** Soğuk servis edin!
""")

        elif len(selected_items) >= 2:
            # Çoklu malzeme tarifleri
            if any('yumurta' in item.lower() for item in selected_items) and any(
                    'domates' in item.lower() for item in selected_items):
                recipes.append(f"""
## 🍳 Menemen (2-3 kişilik, 15 dakika)
**Ana Malzemeler:** {items_text}
**Ek Malzemeler:** Soğan, biber, zeytinyağı, tuz
**Yapılışı:**
1. Soğan ve biberi doğrayıp kavurun
2. Domatesleri ekleyip pişirin
3. Yumurtaları çırpıp ekleyin
4. Karıştırarak pişirin
**İpucu:** Türk mutfağının klasik lezzeti!
""")

            elif any('tavuk' in item.lower() for item in selected_items) and any(
                    'mayonez' in item.lower() for item in selected_items):
                recipes.append(f"""
## 🍗 Tavuklu Sandviç (2 kişilik, 10 dakika)
**Ana Malzemeler:** {items_text}
**Ek Malzemeler:** Ekmek, marul, domates
**Yapılışı:**
1. Tavuğu haşlayıp didikleyin
2. Mayonez ile karıştırın
3. Ekmek arasına koyun
4. Sebzelerle süsleyin
**İpucu:** Pratik ve doyurucu!
""")

            else:
                recipes.append(f"""
## 🍽️ {cuisine_type} Usulü Karışık Yemek (3-4 kişilik, 25 dakika)
**Ana Malzemeler:** {items_text}
**Ek Malzemeler:** Soğan, sarımsak, zeytinyağı, baharat
**Yapılışı:**
1. Tüm malzemeleri temizleyip hazırlayın
2. Soğan ve sarımsakları kavurun
3. Diğer malzemeleri sırasıyla ekleyin
4. Baharatlarla tatlandırıp pişirin
**İpucu:** Seçtiğiniz malzemelerle harika bir kombinasyon!
""")

        if not recipes:
            recipes.append(f"""
## 🍽️ Özel Karışım Tarifi (2-3 kişilik, 20 dakika)
**Seçilen Malzemeler:** {items_text}
**Ek Malzemeler:** Temel baharat ve yağ
**Yapılışı:**
1. Malzemeleri hazırlayın
2. Uygun şekilde pişirin
3. Lezzetlendirip servis edin
**İpucu:** Yaratıcılığınızı kullanın!
""")

        return "\n---\n".join(recipes)

    def _get_recipe_database(self):
        """Tarif veritabanı"""
        return {
            'domates': [
                """
## 🍅 Domates Soslu Makarna (3-4 kişilik, 25 dakika)
**Ana Malzemeler:** {item_name} ({quantity} {unit})
**Ek Malzemeler:** Makarna (300g), soğan, sarımsak, zeytinyağı
**Yapılışı:**
1. Makarnayı haşlayın
2. Soğan ve sarımsakları kavurun
3. Domatesleri ekleyip sos yapın
4. Makarna ile karıştırıp servis edin
**İpucu:** Taze fesleğen eklerseniz daha lezzetli olur!
""",
                """
## 🍅 Domates Çorbası (4 kişilik, 30 dakika)
**Ana Malzemeler:** {item_name} ({quantity} {unit})
**Ek Malzemeler:** Soğan, tereyağı, un, süt, baharat
**Yapılışı:**
1. Domatesleri haşlayıp geçirin
2. Soğanı kavurup un ekleyin
3. Domates püresini ve sıcak suyu ekleyin
4. Süt ile koyulaştırıp servis edin
**İpucu:** Üzerine krema damlatabilirsiniz!
"""
            ],
            'yumurta': [
                """
## 🍳 Omlet (1-2 kişilik, 10 dakika)
**Ana Malzemeler:** {item_name} ({quantity} {unit})
**Ek Malzemeler:** Süt, tuz, tereyağı, peynir (isteğe bağlı)
**Yapılışı:**
1. Yumurtaları çırpın, süt ve tuz ekleyin
2. Tavayı ısıtıp tereyağı ekleyin
3. Yumurta karışımını dökün
4. Peynir ekleyip katlayın
**İpucu:** Sebze ekleyerek çeşitlendirebilirsiniz!
"""
            ],
            'süt': [
                """
## 🥛 Sütlaç (4-5 kişilik, 45 dakika)
**Ana Malzemeler:** {item_name} ({quantity} {unit})
**Ek Malzemeler:** Pirinç (1/2 su bardağı), şeker, vanilya
**Yapılışı:**
1. Pirinci haşlayın
2. Sütü ekleyip kaynatın
3. Şeker ve vanilya ile tatlandırın
4. Koyulaşana kadar pişirin
**İpucu:** Üzerine tarçın serpebilirsiniz!
"""
            ],
            'tavuk': [
                """
## 🍗 Tavuk Sote (3-4 kişilik, 35 dakika)
**Ana Malzemeler:** {item_name} ({quantity} {unit})
**Ek Malzemeler:** Soğan, biber, domates, baharat
**Yapılışı:**
1. Tavuğu küp küp doğrayın
2. Sebzeleri kavurun
3. Tavuğu ekleyip pişirin
4. Baharatlarla lezzetlendirin
**İpucu:** Pilav ile servis edebilirsiniz!
"""
            ],
            'mayonez': [
                """
## 🥗 Rus Salatası (4-5 kişilik, 20 dakika)
**Ana Malzemeler:** {item_name} ({quantity} {unit})
**Ek Malzemeler:** Patates, havuç, bezelye, turşu, yumurta
**Yapılışı:**
1. Sebzeleri haşlayıp doğrayın
2. Yumurtaları haşlayın
3. Mayonez ile karıştırın
4. Soğuk servis edin
**İpucu:** Bir gece bekletirseniz daha lezzetli olur!
"""
            ]
        }


@st.cache_resource
def get_gemini():
    return GeminiClient()