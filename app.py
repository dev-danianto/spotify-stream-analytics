import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import warnings
warnings.filterwarnings('ignore')

# Konfigurasi halaman
st.set_page_config(
    page_title="🎵 Analisis Spotify Saya",
    page_icon="🎵",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS untuk styling yang lebih menarik
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1DB954;
        text-align: center;
        margin-bottom: 2rem;
        font-weight: bold;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1DB954;
    }
    .insight-box {
        background-color: #e8f5e8;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

@st.cache_data
def load_and_clean_data(uploaded_file):
    """Memuat dan membersihkan data Spotify."""
    try:
        # Membaca file CSV
        data = pd.read_csv(uploaded_file)
        
        # Konversi timestamp
        data['ts'] = pd.to_datetime(data['ts'])
        data['tanggal'] = data['ts'].dt.date
        data['jam'] = data['ts'].dt.hour
        data['hari'] = data['ts'].dt.day_name()
        data['bulan'] = data['ts'].dt.month_name()
        data['tahun'] = data['ts'].dt.year
        
        # Konversi durasi
        data['menit_diputar'] = data['ms_played'] / (1000 * 60)
        data['detik_diputar'] = data['ms_played'] / 1000
        
        # Menangani missing values
        data['track_name'].fillna('Lagu Tidak Diketahui', inplace=True)
        data['artist_name'].fillna('Artis Tidak Diketahui', inplace=True)
        data['album_name'].fillna('Album Tidak Diketahui', inplace=True)
        
        # Menambahkan fitur kategori waktu
        data['periode_waktu'] = pd.cut(
            data['jam'],
            bins=[0, 6, 12, 18, 24],
            labels=['Malam (0-6)', 'Pagi (6-12)', 'Siang (12-18)', 'Sore (18-24)'],
            include_lowest=True
        )
        
        # Indikator akhir pekan
        data['akhir_pekan'] = data['hari'].isin(['Saturday', 'Sunday'])
        
        # Kategori durasi
        data['kategori_durasi'] = pd.cut(
            data['menit_diputar'],
            bins=[0, 0.5, 2, 5, float('inf')],
            labels=['Sangat Pendek (<30s)', 'Pendek (30s-2m)', 'Sedang (2-5m)', 'Panjang (>5m)']
        )
        
        return data
    except Exception as e:
        st.error(f"Error loading file: {str(e)}")
        return None

def create_artist_analysis(data):
    """Analisis artis favorit"""
    st.subheader("🎤 Artis Favorit Saya")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Top artis berdasarkan jumlah pemutaran
        top_artists = data['artist_name'].value_counts().head(15)
        
        fig = px.bar(
            x=top_artists.values,
            y=top_artists.index,
            orientation='h',
            title="Top 15 Artis Berdasarkan Jumlah Pemutaran",
            labels={'x': 'Jumlah Pemutaran', 'y': 'Artis'},
            color=top_artists.values,
            color_continuous_scale='Viridis'
        )
        fig.update_layout(height=600, yaxis={'categoryorder':'total ascending'})
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Top artis berdasarkan waktu mendengarkan
        artist_time = data.groupby('artist_name')['menit_diputar'].sum().sort_values(ascending=False).head(10)
        
        fig = px.pie(
            values=artist_time.values,
            names=artist_time.index,
            title="Top 10 Artis Berdasarkan Waktu Mendengarkan"
        )
        fig.update_traces(textposition='inside', textinfo='percent+label')
        st.plotly_chart(fig, use_container_width=True)
    
    # Insight
    top_artist = top_artists.index[0]
    top_plays = top_artists.iloc[0]
    st.markdown(f"""
    <div class="insight-box">
        <h4>✨ Insight: Artis favorit Anda adalah <strong>{top_artist}</strong> dengan <strong>{top_plays}</strong> kali pemutaran!</h4>
    </div>
    """, unsafe_allow_html=True)

def create_song_analysis(data):
    """Analisis lagu favorit"""
    st.subheader("🎵 Lagu Favorit Saya")
    
    # Top lagu
    top_songs = data.groupby(['track_name', 'artist_name']).size().sort_values(ascending=False).head(15)
    
    # Prepare data for visualization
    song_data = []
    for (song, artist), count in top_songs.items():
        song_display = f"{song[:30]}..." if len(song) > 30 else song
        song_data.append({
            'song': f"{song_display} - {artist}",
            'plays': count,
            'full_name': f"{song} - {artist}"
        })
    
    song_df = pd.DataFrame(song_data)
    
    fig = px.bar(
        song_df,
        x='plays',
        y='song',
        orientation='h',
        title="Top 15 Lagu Paling Sering Diputar",
        labels={'plays': 'Jumlah Pemutaran', 'song': 'Lagu'},
        color='plays',
        color_continuous_scale='Blues'
    )
    fig.update_layout(height=600, yaxis={'categoryorder':'total ascending'})
    st.plotly_chart(fig, use_container_width=True)
    
    # Detail tabel
    with st.expander("📊 Detail Lagu Favorit"):
        detail_data = []
        for i, ((song, artist), count) in enumerate(top_songs.head(10).items(), 1):
            song_sessions = data[(data['track_name'] == song) & (data['artist_name'] == artist)]
            total_minutes = song_sessions['menit_diputar'].sum()
            detail_data.append({
                'Ranking': i,
                'Lagu': song,
                'Artis': artist,
                'Jumlah Pemutaran': count,
                'Total Waktu (menit)': f"{total_minutes:.1f}"
            })
        
        st.dataframe(pd.DataFrame(detail_data), use_container_width=True)
    
    # Insight
    top_song, top_artist = top_songs.index[0]
    top_song_plays = top_songs.iloc[0]
    st.markdown(f"""
    <div class="insight-box">
        <h4>✨ Insight: Lagu favorit Anda adalah <strong>"{top_song}"</strong> oleh <strong>{top_artist}</strong> dengan <strong>{top_song_plays}</strong> kali pemutaran!</h4>
    </div>
    """, unsafe_allow_html=True)

def create_time_analysis(data):
    """Analisis pola waktu mendengarkan"""
    st.subheader("⏰ Kapan Saya Paling Aktif Mendengarkan Musik?")
    
    # Mapping hari ke bahasa Indonesia
    hari_indonesia = {
        'Monday': 'Senin', 'Tuesday': 'Selasa', 'Wednesday': 'Rabu',
        'Thursday': 'Kamis', 'Friday': 'Jumat', 'Saturday': 'Sabtu', 'Sunday': 'Minggu'
    }
    day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Pola per jam
        hourly_listening = data['jam'].value_counts().sort_index()
        
        fig = px.line(
            x=hourly_listening.index,
            y=hourly_listening.values,
            title="Aktivitas Mendengarkan per Jam",
            labels={'x': 'Jam dalam Sehari', 'y': 'Jumlah Sesi'},
            markers=True
        )
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Pola per hari
        daily_listening = data['hari'].value_counts().reindex(day_order)
        day_labels = [hari_indonesia[day] for day in day_order]
        colors = ['orange' if day in ['Saturday', 'Sunday'] else 'steelblue' for day in day_order]
        
        fig = px.bar(
            x=day_labels,
            y=daily_listening.values,
            title="Aktivitas Mendengarkan per Hari",
            labels={'x': 'Hari', 'y': 'Jumlah Sesi'},
            color=colors,
            color_discrete_map='identity'
        )
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)
    
    # Heatmap
    heatmap_data = data.groupby(['hari', 'jam']).size().unstack(fill_value=0)
    heatmap_data = heatmap_data.reindex(day_order)
    heatmap_data.index = day_labels
    
    fig = px.imshow(
        heatmap_data.values,
        x=heatmap_data.columns,
        y=heatmap_data.index,
        title="Heatmap: Pola Mendengarkan Hari vs Jam",
        labels={'x': 'Jam', 'y': 'Hari', 'color': 'Jumlah Sesi'},
        color_continuous_scale='YlOrRd'
    )
    st.plotly_chart(fig, use_container_width=True)
    
    # Periode waktu
    periode_listening = data['periode_waktu'].value_counts()
    
    fig = px.pie(
        values=periode_listening.values,
        names=periode_listening.index,
        title="Distribusi Mendengarkan per Periode Waktu"
    )
    st.plotly_chart(fig, use_container_width=True)
    
    # Insights
    peak_hour = hourly_listening.idxmax()
    peak_day = hari_indonesia[daily_listening.idxmax()]
    peak_period = periode_listening.idxmax()
    
    weekend_sessions = len(data[data['akhir_pekan']])
    weekday_sessions = len(data[~data['akhir_pekan']])
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("🕐 Jam Tersibuk", f"{peak_hour}:00", f"{hourly_listening[peak_hour]} sesi")
    with col2:
        st.metric("📅 Hari Tersibuk", peak_day, f"{daily_listening.max()} sesi")
    with col3:
        st.metric("⏰ Periode Tersibuk", peak_period, f"{periode_listening.max()} sesi")
    
    st.markdown(f"""
    <div class="insight-box">
        <h4>✨ Insight: Anda paling aktif mendengarkan musik pada jam <strong>{peak_hour}:00</strong> di hari <strong>{peak_day}</strong>!</h4>
        <p><strong>Akhir pekan:</strong> {weekend_sessions:,} sesi ({weekend_sessions/len(data)*100:.1f}%) | 
           <strong>Hari kerja:</strong> {weekday_sessions:,} sesi ({weekday_sessions/len(data)*100:.1f}%)</p>
    </div>
    """, unsafe_allow_html=True)

def create_duration_analysis(data):
    """Analisis durasi mendengarkan"""
    st.subheader("⏱️ Berapa Lama Durasi Rata-rata Saya Mendengarkan Lagu?")
    
    # Statistik durasi
    rata_rata_menit = data['menit_diputar'].mean()
    median_menit = data['menit_diputar'].median()
    total_jam = data['menit_diputar'].sum() / 60
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("📊 Rata-rata", f"{rata_rata_menit:.2f} menit")
    with col2:
        st.metric("📈 Median", f"{median_menit:.2f} menit")
    with col3:
        st.metric("⏰ Total Waktu", f"{total_jam:.1f} jam")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Histogram durasi
        fig = px.histogram(
            data[data['menit_diputar'] <= 10],  # Fokus pada 0-10 menit
            x='menit_diputar',
            nbins=50,
            title="Distribusi Durasi Mendengarkan (0-10 menit)",
            labels={'x': 'Menit', 'y': 'Frekuensi'}
        )
        # Tambahkan garis rata-rata dan median
        fig.add_vline(x=rata_rata_menit, line_dash="dash", line_color="red", 
                     annotation_text=f"Rata-rata: {rata_rata_menit:.2f}")
        fig.add_vline(x=median_menit, line_dash="dash", line_color="green",
                     annotation_text=f"Median: {median_menit:.2f}")
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Kategori durasi
        duration_dist = data['kategori_durasi'].value_counts()
        
        fig = px.pie(
            values=duration_dist.values,
            names=duration_dist.index,
            title="Distribusi Kategori Durasi"
        )
        st.plotly_chart(fig, use_container_width=True)
    
    # Durasi per jam dan hari
    col1, col2 = st.columns(2)
    
    with col1:
        hourly_duration = data.groupby('jam')['menit_diputar'].mean()
        fig = px.line(
            x=hourly_duration.index,
            y=hourly_duration.values,
            title="Durasi Rata-rata per Jam",
            labels={'x': 'Jam', 'y': 'Durasi Rata-rata (menit)'},
            markers=True
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Mapping hari
        hari_indonesia = {
            'Monday': 'Senin', 'Tuesday': 'Selasa', 'Wednesday': 'Rabu',
            'Thursday': 'Kamis', 'Friday': 'Jumat', 'Saturday': 'Sabtu', 'Sunday': 'Minggu'
        }
        day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        
        daily_duration = data.groupby('hari')['menit_diputar'].mean().reindex(day_order)
        day_labels = [hari_indonesia[day] for day in day_order]
        
        fig = px.bar(
            x=day_labels,
            y=daily_duration.values,
            title="Durasi Rata-rata per Hari",
            labels={'x': 'Hari', 'y': 'Durasi Rata-rata (menit)'}
        )
        st.plotly_chart(fig, use_container_width=True)
    
    # Detail kategori durasi
    with st.expander("📊 Detail Kategori Durasi"):
        detail_data = []
        for kategori, jumlah in duration_dist.items():
            persentase = (jumlah / len(data)) * 100
            detail_data.append({
                'Kategori': kategori,
                'Jumlah Sesi': f"{jumlah:,}",
                'Persentase': f"{persentase:.1f}%"
            })
        st.dataframe(pd.DataFrame(detail_data), use_container_width=True)
    
    # Sesi terpanjang
    with st.expander("🎵 Sesi Mendengarkan Terpanjang"):
        longest_sessions = data.nlargest(10, 'menit_diputar')[['track_name', 'artist_name', 'menit_diputar']]
        longest_sessions['Durasi'] = longest_sessions['menit_diputar'].apply(lambda x: f"{x:.2f} menit")
        longest_sessions = longest_sessions[['track_name', 'artist_name', 'Durasi']].reset_index(drop=True)
        longest_sessions.index = longest_sessions.index + 1
        st.dataframe(longest_sessions, use_container_width=True)
    
    st.markdown(f"""
    <div class="insight-box">
        <h4>✨ Insight: Durasi rata-rata mendengarkan lagu Anda adalah <strong>{rata_rata_menit:.2f} menit</strong>!</h4>
    </div>
    """, unsafe_allow_html=True)

def create_pattern_analysis(data):
    """Analisis pola dan tren khusus"""
    st.subheader("🎭 Tren dan Pola Khusus dalam Kebiasaan Mendengarkan")
    
    # Statistik konsistensi
    days_with_music = data['tanggal'].nunique()
    total_days = (data['ts'].max() - data['ts'].min()).days + 1
    consistency = (days_with_music / total_days) * 100
    
    artist_diversity = data['artist_name'].nunique()
    total_sessions = len(data)
    diversity_ratio = artist_diversity / total_sessions
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("🎯 Konsistensi", f"{consistency:.1f}%", f"{days_with_music}/{total_days} hari")
    with col2:
        st.metric("🎨 Keragaman Artis", f"{artist_diversity}", f"dari {total_sessions:,} sesi")
    with col3:
        st.metric("🔄 Rasio Keragaman", f"{diversity_ratio:.3f}")
    
    # Tren aktivitas harian
    daily_activity = data.groupby('tanggal').size()
    
    fig = px.line(
        x=daily_activity.index,
        y=daily_activity.values,
        title="Tren Aktivitas Harian",
        labels={'x': 'Tanggal', 'y': 'Jumlah Sesi'}
    )
    fig.update_layout(height=400)
    st.plotly_chart(fig, use_container_width=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Distribusi sesi per hari
        sessions_per_day = daily_activity.value_counts().sort_index()
        
        fig = px.bar(
            x=sessions_per_day.index,
            y=sessions_per_day.values,
            title="Distribusi Sesi per Hari",
            labels={'x': 'Jumlah Sesi per Hari', 'y': 'Frekuensi Hari'}
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Pola weekday vs weekend
        weekend_hourly = data[data['akhir_pekan']].groupby('jam').size()
        weekday_hourly = data[~data['akhir_pekan']].groupby('jam').size()
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=weekday_hourly.index, y=weekday_hourly.values,
                                mode='lines+markers', name='Hari Kerja'))
        fig.add_trace(go.Scatter(x=weekend_hourly.index, y=weekend_hourly.values,
                                mode='lines+markers', name='Akhir Pekan'))
        
        fig.update_layout(
            title="Pola Mendengarkan: Hari Kerja vs Akhir Pekan",
            xaxis_title="Jam",
            yaxis_title="Jumlah Sesi"
        )
        st.plotly_chart(fig, use_container_width=True)
    
    # Analisis mendalam
    weekday_peak = weekday_hourly.idxmax() if len(weekday_hourly) > 0 else 0
    weekend_peak = weekend_hourly.idxmax() if len(weekend_hourly) > 0 else 0
    avg_sessions_per_day = len(data) / days_with_music
    most_active_day = daily_activity.idxmax()
    max_sessions = daily_activity.max()
    
    st.markdown(f"""
    <div class="insight-box">
        <h4>📈 Analisis Mendalam:</h4>
        <ul>
            <li><strong>Jam tersibuk hari kerja:</strong> {weekday_peak}:00</li>
            <li><strong>Jam tersibuk akhir pekan:</strong> {weekend_peak}:00</li>
            <li><strong>Rata-rata sesi per hari:</strong> {avg_sessions_per_day:.1f}</li>
            <li><strong>Hari paling aktif:</strong> {most_active_day} dengan {max_sessions} sesi</li>
        </ul>
        <h4>✨ Insight: Anda memiliki pola mendengarkan yang konsisten <strong>{consistency:.1f}%</strong> dengan keragaman <strong>{artist_diversity}</strong> artis!</h4>
    </div>
    """, unsafe_allow_html=True)

def main():
    """Fungsi utama aplikasi"""
    
    # Header
    st.markdown('<h1 class="main-header">🎵 Analisis Data Spotify Saya</h1>', unsafe_allow_html=True)
    
    st.markdown("""
    <div style="text-align: center; margin-bottom: 2rem;">
        <p style="font-size: 1.2rem; color: #666;">
            Uncover insights about your music listening habits! 🎧
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Sidebar untuk upload file
    st.sidebar.header("📁 Upload Data Spotify")
    st.sidebar.markdown("""
    **Cara mendapatkan data Spotify:**
    1. Masuk ke akun Spotify Anda
    2. Pergi ke Privacy Settings
    3. Request data Anda
    4. Download file JSON/CSV yang diberikan
    5. Upload file 'spotify_extended_streaming_history.csv' di sini
    """)
    
    uploaded_file = st.sidebar.file_uploader(
        "Choose your Spotify data file",
        type=['csv'],
        help="Upload file CSV dari data Spotify Anda"
    )
    
    if uploaded_file is not None:
        # Load dan clean data
        with st.spinner('🔄 Memproses data Spotify Anda...'):
            data = load_and_clean_data(uploaded_file)
        
        if data is not None:
            # Overview metrics
            st.subheader("📊 Overview Data Anda")
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("🎵 Total Sesi", f"{len(data):,}")
            with col2:
                st.metric("🎤 Lagu Unik", f"{data['track_name'].nunique():,}")
            with col3:
                st.metric("🎨 Artis Unik", f"{data['artist_name'].nunique():,}")
            with col4:
                total_hours = data['menit_diputar'].sum() / 60
                st.metric("⏰ Total Waktu", f"{total_hours:.1f} jam")
            
            # Tab navigation
            tab1, tab2, tab3, tab4, tab5 = st.tabs([
                "🎤 Artis Favorit",
                "🎵 Lagu Favorit", 
                "⏰ Pola Waktu",
                "⏱️ Durasi",
                "🎭 Tren & Pola"
            ])
            
            with tab1:
                create_artist_analysis(data)
            
            with tab2:
                create_song_analysis(data)
            
            with tab3:
                create_time_analysis(data)
            
            with tab4:
                create_duration_analysis(data)
            
            with tab5:
                create_pattern_analysis(data)
            
            # Footer
            st.markdown("---")
            st.markdown("""
            <div style="text-align: center; color: #666; margin-top: 2rem;">
                <p>🎵 Made with ❤️ using Streamlit | Data from your Spotify account</p>
            </div>
            """, unsafe_allow_html=True)
    
    else:
        # Halaman instruksi
        st.info("👆 Upload file data Spotify Anda di sidebar untuk memulai analisis!")
        
        st.markdown("""
        ## 🎯 Apa yang bisa Anda temukan?
        
        ### 🎤 **Artis Favorit**
        - Siapa artis yang paling sering Anda dengarkan?
        - Berapa total waktu yang Anda habiskan untuk setiap artis?
        
        ### 🎵 **Lagu Favorit**
        - Lagu mana yang paling sering diputar?
        - Berapa kali Anda memutar lagu favorit?
        
        ### ⏰ **Pola Waktu**
        - Kapan waktu favorit Anda mendengarkan musik?
        - Apakah kebiasaan weekend berbeda dengan hari kerja?
        
        ### ⏱️ **Durasi Mendengarkan**
        - Berapa lama rata-rata Anda mendengarkan setiap lagu?
        - Apakah Anda sering skip lagu atau mendengarkan sampai habis?
        
        ### 🎭 **Tren & Pola Khusus**
        - Bagaimana konsistensi mendengarkan musik Anda?
        - Seberapa beragam selera musik Anda?
        
        ---
        
        ### 📥 **Cara Mendapatkan Data Spotify:**
        
        1. **Login** ke akun Spotify Anda di web browser
        2. Pergi ke **Account Overview** → **Privacy Settings**
        3. Scroll ke bawah dan klik **"Request Data"**
        4. Pilih **"Extended streaming history"** dan **"Account data"**
        5. Tunggu email dari Spotify (biasanya 1-30 hari)
        6. Download file ZIP yang dikirim Spotify
        7. Extract dan upload file **"endsong_X.json"** atau CSV yang sudah dikonversi
        
        ### 📋 **Format Data yang Didukung:**
        - File CSV dengan kolom: `ts`, `ms_played`, `track_name`, `artist_name`, `album_name`
        - File harus dalam format UTF-8
        - Ukuran file maksimal 200MB
        """)

if __name__ == "__main__":
    main()