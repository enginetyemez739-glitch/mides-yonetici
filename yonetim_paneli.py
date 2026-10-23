import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
import json
from datetime import datetime

st.set_page_config(page_title="MİDES - Yönetici Paneli", layout="wide")
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]

if "giris_basarili" not in st.session_state: st.session_state.giris_basarili = False
if "kullanici_adi" not in st.session_state: st.session_state.kullanici_adi = ""
if "sifre_degistirme_modu" not in st.session_state: st.session_state.sifre_degistirme_modu = False

try:
    creds_dict = json.loads(st.secrets["google_json"])
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    client = gspread.authorize(creds)
    kullanici_tablosu = client.open("MİDES - Kullanıcılar").get_worksheet(0)
    df_kullanicilar = pd.DataFrame(kullanici_tablosu.get_all_records())
except Exception as e:
    st.error("Veritabanı bağlantı hatası.")
    st.stop()

if st.session_state.sifre_degistirme_modu:
    st.warning("⚠️ Şifrenizin kullanım süresi dolmuş veya değişiklik talep ettiniz.")
    yeni_sifre = st.text_input("Yeni Şifre:", type="password")
    yeni_sifre_tekrar = st.text_input("Yeni Şifre (Tekrar):", type="password")
    if st.button("Şifreyi Güncelle"):
        if yeni_sifre == yeni_sifre_tekrar and len(yeni_sifre) >= 4:
            satir_no = df_kullanicilar[df_kullanicilar['Kullanıcı Adı'] == st.session_state.kullanici_adi].index[0] + 2
            kullanici_tablosu.update_cell(satir_no, 2, yeni_sifre)
            kullanici_tablosu.update_cell(satir_no, 3, datetime.today().strftime('%Y-%m-%d'))
            st.success("Şifreniz güncellendi! Sayfayı yenileyerek giriş yapın.")
            st.session_state.sifre_degistirme_modu = False
        else:
            st.error("Şifreler uyuşmuyor veya çok kısa.")
    st.stop()

if not st.session_state.giris_basarili:
    st.title("🔐 MİDES Yönetici Girişi")
    kadi_input = st.text_input("Kullanıcı Adı:")
    sifre_input = st.text_input("Şifre:", type="password")
    if st.button("Giriş Yap"):
        kullanici = df_kullanicilar[(df_kullanicilar['Kullanıcı Adı'] == kadi_input) & (df_kullanicilar['Şifre'] == str(sifre_input))]
        if not kullanici.empty and kullanici['Yetki'].values[0] == "Yonetici":
            st.session_state.kullanici_adi = kadi_input
            son_guncelleme = pd.to_datetime(kullanici['Son Güncelleme'].values[0], errors='coerce')
            if (datetime.today() - son_guncelleme).days >= 30:
                st.session_state.sifre_degistirme_modu = True
                st.rerun()
            else:
                st.session_state.giris_basarili = True
                st.rerun()
        else:
            st.error("Hatalı giriş veya yetkisiz erişim!")
    st.stop()

col1, col2 = st.columns([8, 2])
with col1: st.title(f"🛡️ Ana Yönetim Paneli")
with col2:
    if st.button("🔄 Şifremi Değiştir"):
        st.session_state.sifre_degistirme_modu = True
        st.rerun()

# --- VERİ ÇEKME VE UYARI EKRANI BURADAN İTİBAREN BAŞLAR ---
try:
    df_gida = pd.DataFrame(client.open("MİDES - Gıda Deposu").get_worksheet(0).get_all_records())
    df_temizlik = pd.DataFrame(client.open("MİDES - Temizlik Deposu").get_worksheet(0).get_all_records())

    def uyarilari_goster(df, depo_adi):
        if df.empty: return
        bugun = pd.to_datetime(datetime.today().strftime('%Y-%m-%d'))
        if 'Miktar' in df.columns:
            df['Miktar'] = pd.to_numeric(df['Miktar'], errors='coerce').fillna(0)
            kritik = df[df['Miktar'] < 50]
            if not kritik.empty: st.warning(f"⚠️ {depo_adi} Kritik Stok"); st.dataframe(kritik[['Ürün Adı', 'Miktar', 'Birim']], hide_index=True)
        if 'SKT' in df.columns:
            df['SKT_Tarih'] = pd.to_datetime(df['SKT'], errors='coerce')
            df['Kalan'] = (df['SKT_Tarih'] - bugun).dt.days
            gecen = df[df['Kalan'] < 0]
            yaklasan = df[(df['Kalan'] >= 0) & (df['Kalan'] <= 60)]
            if not gecen.empty: st.error(f"🚨 {depo_adi} SKT İhlali"); st.dataframe(gecen[['Ürün Adı', 'SKT', 'Miktar']], hide_index=True)
            if not yaklasan.empty: st.warning(f"⏳ {depo_adi} SKT Yaklaşan"); st.dataframe(yaklasan[['Ürün Adı', 'SKT', 'Miktar']], hide_index=True)

    sekme1, sekme2 = st.tabs(["📦 Gıda", "🧹 Temizlik"])
    with sekme1: uyarilari_goster(df_gida, "Gıda"); st.dataframe(df_gida, use_container_width=True)
    with sekme2: uyarilari_goster(df_temizlik, "Temizlik"); st.dataframe(df_temizlik, use_container_width=True)
except Exception as e: st.error(f"Bağlantı hatası: {e}")
