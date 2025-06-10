import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(layout="wide", page_title="Spotify Listening Dashboard")

spotify_history_df = pd.read_csv("spotify_history.csv")

spotify_history_df['ts'] = pd.to_datetime(spotify_history_df['ts'])
spotify_history_df['play_duration_minutes'] = spotify_history_df['ms_played'] / (1000 * 60)
spotify_history_df['date'] = spotify_history_df['ts'].dt.date
spotify_history_df['hour'] = spotify_history_df['ts'].dt.hour
spotify_history_df['day_of_week'] = spotify_history_df['ts'].dt.day_name()

min_date = spotify_history_df['date'].min()
max_date = spotify_history_df['date'].max()

st.title("🎧 Spotify Listening Dashboard")


st.sidebar.header("Dashboard Filters")

start_date, end_date = st.sidebar.date_input(
    "Select a date range:",
    value=(min_date, max_date),
    min_value=min_date,
    max_value=max_date
)

all_platforms = spotify_history_df['platform'].unique().tolist()
selected_platforms = st.sidebar.multiselect(
    "Filter by Platform:",
    options=all_platforms,
    default=all_platforms
)

filtered_df = spotify_history_df[
    (spotify_history_df['date'] >= start_date) &
    (spotify_history_df['date'] <= end_date) &
    (spotify_history_df['platform'].isin(selected_platforms))
]

total_listening_time_hours = filtered_df['play_duration_minutes'].sum() / 60
unique_tracks = filtered_df['spotify_track_uri'].nunique()
unique_artists = filtered_df['artist_name'].nunique()
unique_albums = filtered_df['album_name'].nunique()
skipped_tracks_count = filtered_df['skipped'].sum()
total_plays = len(filtered_df)
skipped_rate = (skipped_tracks_count / total_plays * 100) if total_plays > 0 else 0

col1, col2, col3, col4, col5 = st.columns(5)
with col1:
    st.metric("Total Listening Time", f"{total_listening_time_hours:.2f} Hours")
with col2:
    st.metric("Unique Tracks", unique_tracks)
with col3:
    st.metric("Unique Artists", unique_artists)
with col4:
    st.metric("Unique Albums", unique_albums)
with col5:
    st.metric("Skipped Rate", f"{skipped_rate:.2f}%")

st.header("Listening Activity Over Time")
daily_listening = filtered_df.groupby('date')['play_duration_minutes'].sum().reset_index()
daily_listening['date'] = pd.to_datetime(daily_listening['date'])
fig_daily_listening = px.line(
    daily_listening,
    x='date',
    y='play_duration_minutes',
    title='Daily Listening Time',
    labels={'play_duration_minutes': 'Listening Time (minutes)', 'date': 'Date'}
)
fig_daily_listening.update_layout(hovermode="x unified")
st.plotly_chart(fig_daily_listening, use_container_width=True)

st.subheader("Hourly Listening Pattern")
hourly_listening = filtered_df.groupby('hour')['play_duration_minutes'].sum().reset_index()
fig_hourly_listening = px.bar(
    hourly_listening,
    x='hour',
    y='play_duration_minutes',
    title='Listening Time by Hour of Day',
    labels={'play_duration_minutes': 'Listening Time (minutes)', 'hour': 'Hour of Day (24-hour)'}
)
fig_hourly_listening.update_layout(xaxis_tickangle=-45)
st.plotly_chart(fig_hourly_listening, use_container_width=True)


st.header("Top Insights")

col_top1, col_top2, col_top3 = st.columns(3)

with col_top1:
    st.subheader("Top 10 Tracks (by listening time)")
    top_tracks = filtered_df.groupby(['track_name', 'artist_name'])['play_duration_minutes'].sum().nlargest(10).reset_index()
    top_tracks['Play Duration (Minutes)'] = top_tracks['play_duration_minutes'].round(2)
    fig_top_tracks = px.bar(
        top_tracks,
        y='track_name',
        x='play_duration_minutes',
        color='artist_name',
        orientation='h',
        labels={'play_duration_minutes': 'Total Listening Time (minutes)', 'track_name': 'Track Name'}
    )
    fig_top_tracks.update_layout(yaxis={'categoryorder':'total ascending'})
    st.plotly_chart(fig_top_tracks, use_container_width=True)

with col_top2:
    st.subheader("Top 10 Artists (by listening time)")
    top_artists = filtered_df.groupby('artist_name')['play_duration_minutes'].sum().nlargest(10).reset_index()
    top_artists['Play Duration (Minutes)'] = top_artists['play_duration_minutes'].round(2)
    fig_top_artists = px.bar(
        top_artists,
        y='artist_name',
        x='play_duration_minutes',
        orientation='h',
        labels={'play_duration_minutes': 'Total Listening Time (minutes)', 'artist_name': 'Artist Name'}
    )
    fig_top_artists.update_layout(yaxis={'categoryorder':'total ascending'})
    st.plotly_chart(fig_top_artists, use_container_width=True)

with col_top3:
    st.subheader("Top 10 Albums (by listening time)")
    top_albums = filtered_df.groupby(['album_name', 'artist_name'])['play_duration_minutes'].sum().nlargest(10).reset_index()
    top_albums['Play Duration (Minutes)'] = top_albums['play_duration_minutes'].round(2)
    fig_top_albums = px.bar(
        top_albums,
        y='album_name',
        x='play_duration_minutes',
        color='artist_name',
        orientation='h',
        labels={'play_duration_minutes': 'Total Listening Time (minutes)', 'album_name': 'Album Name'}
    )
    fig_top_albums.update_layout(yaxis={'categoryorder':'total ascending'})
    st.plotly_chart(fig_top_albums, use_container_width=True)

st.header("Platform Distribution")
platform_counts = filtered_df['platform'].value_counts().reset_index()
platform_counts.columns = ['Platform', 'Count']
fig_platform = px.pie(
    platform_counts,
    values='Count',
    names='Platform',
    title='Listening by Platform',
    hole=0.3
)
st.plotly_chart(fig_platform, use_container_width=True)

st.header("Skipped Tracks Analysis")
skipped_distribution = filtered_df['skipped'].value_counts(normalize=True).reset_index()
skipped_distribution.columns = ['Skipped', 'Percentage']
skipped_distribution['Skipped'] = skipped_distribution['Skipped'].map({True: 'Skipped', False: 'Played'})
fig_skipped = px.bar(
    skipped_distribution,
    x='Skipped',
    y='Percentage',
    title='Skipped vs. Played Tracks',
    labels={'Percentage': 'Percentage of Tracks'},
    text_auto=True
)
fig_skipped.update_layout(yaxis_tickformat=".0%")
st.plotly_chart(fig_skipped, use_container_width=True)

st.subheader("Skipped Tracks by Artist")
skipped_by_artist = filtered_df[filtered_df['skipped'] == True].groupby('artist_name')['spotify_track_uri'].count().nlargest(10).reset_index()
skipped_by_artist.columns = ['Artist Name', 'Skipped Count']
fig_skipped_artist = px.bar(
    skipped_by_artist,
    x='Skipped Count',
    y='Artist Name',
    orientation='h',
    title='Top 10 Artists with Most Skipped Tracks',
    labels={'Skipped Count': 'Number of Skipped Tracks'}
)
fig_skipped_artist.update_layout(yaxis={'categoryorder':'total ascending'})
st.plotly_chart(fig_skipped_artist, use_container_width=True)