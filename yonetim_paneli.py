import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
import json
from datetime import datetime

st.set_page_config(page_title="MİDES - Yönetici Paneli", layout="wide")

# Yöneticinin kullanacağı tek şifre
sifre = "Yonetici5307" 
girilen_sifre = st.text_input("Ana Panel Şifresini Girin:", type="password")

if girilen_sifre == sifre:
    st.title("🛡️ MİDES - Ana Yönetim ve Gözlem Paneli")
    st.markdown("Birlik bünyesindeki tüm depoların güncel durumları ve kritik uyarılar aşağıda sunulmuştur.")

    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    
    try:
        # Google Tablolar bağlantısı
        creds_dict = json.loads(st.secrets["google_json"])
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        client = gspread.authorize(creds)

        # Verileri çekme (sekme ismine bakmaksızın ilk sekmeyi okur)
        gida_veriler = client.open("MİDES - Gıda Deposu").get_worksheet(0).get_all_records()
        temizlik_veriler = client.open("MİDES - Temizlik Deposu").get_worksheet(0).get_all_records()

        df_gida = pd.DataFrame(gida_veriler)
        df_temizlik = pd.DataFrame(temizlik_veriler)

        # Otomatik Uyarı Fonksiyonu
        def uyarilari_goster(df, depo_adi):
            if df.empty:
                return
                
            bugun = pd.to_datetime(datetime.today().strftime('%Y-%m-%d'))
            kritik_stok_siniri = 50  # Stok bu sayının altına düşerse uyarı verir
            yaklasan_skt_gun = 60    # SKT'ye bu kadar gün kalırsa uyarı verir

            # Kritik Stok Kontrolü
            if 'Miktar' in df.columns:
                df['Miktar'] = pd.to_numeric(df['Miktar'], errors='coerce').fillna(0)
                kritik_urunler = df[df['Miktar'] < kritik_stok_siniri]
                if not kritik_urunler.empty:
                    st.warning(f"⚠️ *{depo_adi} Kritik Stok Uyarısı:* Aşağıdaki ürünlerin stoğu tükenmek üzere!")
                    st.dataframe(kritik_urunler[['Ürün Adı', 'Miktar', 'Birim']], hide_index=True)

            # SKT Kontrolü
            if 'SKT' in df.columns:
                df_skt = df.copy()
                df_skt['SKT_Tarih'] = pd.to_datetime(df_skt['SKT'], errors='coerce')
                df_skt['Kalan_Gun'] = (df_skt['SKT_Tarih'] - bugun).dt.days
                
                skt_gecenler = df_skt[df_skt['Kalan_Gun'] < 0]
                skt_yaklasanlar = df_skt[(df_skt['Kalan_Gun'] >= 0) & (df_skt['Kalan_Gun'] <= yaklasan_skt_gun)]

                if not skt_gecenler.empty:
                    st.error(f"🚨 *{depo_adi} SKT Uyarısı:* Aşağıdaki ürünlerin kullanım tarihi GEÇMİŞTİR!")
                    st.dataframe(skt_gecenler[['Ürün Adı', 'SKT', 'Miktar', 'Birim']], hide_index=True)
                    
                if not skt_yaklasanlar.empty:
                    st.warning(f"⏳ *{depo_adi} SKT Yaklaşanlar:* Aşağıdaki ürünlerin kullanım tarihine {yaklasan_skt_gun} günden az kaldı!")
                    st.dataframe(skt_yaklasanlar[['Ürün Adı', 'SKT', 'Miktar', 'Birim']], hide_index=True)

        # Sekmeli yapı ve ekran yerleşimi
        sekme1, sekme2 = st.tabs(["📦 Gıda Deposu", "🧹 Temizlik Deposu"])

        with sekme1:
            uyarilari_goster(df_gida, "Gıda Deposu")
            st.markdown("### Tüm Gıda Envanteri")
            st.dataframe(df_gida, use_container_width=True)

        with sekme2:
            uyarilari_goster(df_temizlik, "Temizlik Deposu")
            st.markdown("### Tüm Temizlik Envanteri")
            st.dataframe(df_temizlik, use_container_width=True)

    except Exception as e:
        st.error(f"Bağlantı hatası: {e}")
elif girilen_sifre != "":
    st.error("Hatalı şifre girdiniz.")
