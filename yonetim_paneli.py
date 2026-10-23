import streamlit as st
import gspread
import json
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd

st.set_page_config(page_title="MİDES - Yönetici Paneli", layout="wide")

# Yöneticinin kullanacağı tek şifre
sifre = "Yönetici5307" 
girilen_sifre = st.text_input("Ana Panel Şifresini Girin:", type="password")

if girilen_sifre == sifre:
    st.title("🛡️ MİDES - Ana Yönetim ve Gözlem Paneli")
    st.markdown("Birlik bünyesindeki tüm depoların güncel durumları aşağıda sunulmuştur.")

    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    
    try:
        # Bağlantı kimliklerini Streamlit panelinden çeker
        # google_json içindeki metni alıp sisteme okutur
        creds_dict = json.loads(st.secrets["google_json"])
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        client = gspread.authorize(creds)

        # İki farklı deponun verilerini arka planda okur
        gida_veriler = client.open("MİDES - Gıda Deposu").get_worksheet(0).get_all_records()
        temizlik_veriler = client.open("MİDES - Temizlik Deposu").get_worksheet(0).get_all_records()

        # Sekmeli yapı ile gösterim
        sekme1, sekme2 = st.tabs(["📦 Gıda Deposu Envanteri", "🧹 Temizlik Deposu Envanteri"])

        with sekme1:
            st.dataframe(pd.DataFrame(gida_veriler), use_container_width=True)

        with sekme2:
            st.dataframe(pd.DataFrame(temizlik_veriler), use_container_width=True)

    except Exception as e:
        st.error(f"Veri çekme hatası: İzinleri veya tablo adlarını kontrol edin. Detay: {e}")
elif girilen_sifre != "":
    st.error("Hatalı şifre girdiniz.")
