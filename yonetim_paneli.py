import streamlit as st
import gspread
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
        creds_dict = {
            "type": st.secrets["type"],
            "project_id": st.secrets["project_id"],
            "private_key_id": st.secrets["private_key_id"],
            "private_key": st.secrets["private_key"],
            "client_email": st.secrets["client_email"],
            "client_id": st.secrets["client_id"],
            "auth_uri": st.secrets["auth_uri"],
            "token_uri": st.secrets["token_uri"],
            "auth_provider_x509_cert_url": st.secrets["auth_provider_x509_cert_url"],
            "client_x509_cert_url": st.secrets["client_x509_cert_url"]
        }
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        client = gspread.authorize(creds)

        # İki farklı deponun verilerini arka planda okur
        gida_veriler = client.open("MİDES - Gıda Deposu").sheet1.get_all_records()
        temizlik_veriler = client.open("MİDES - Temizlik Deposu").sheet1.get_all_records()

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
