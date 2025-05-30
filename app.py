from flask import Flask, render_template, request, jsonify, send_file
from yandex_music import Client
import os
import tempfile
import aiohttp
import asyncio
import json
from datetime import datetime

app = Flask(__name__)
client = Client("y0__xCilY3fBhje-AYgwbeW3xLNQxtQ57SkjB0qV1XLS7Sil8Sy4A")

# 🔹 Утилиты
def clean_filename(name: str) -> str:
    return re.sub(r'[\\/:*?"<>|]', '', name).strip()

def extract_track_id(url: str) -> str | None:
    match = re.search(r'/track/(\d+)', url)
    return match.group(1) if match else None

async def download_music_mp3(track_id: str) -> str | None:
    try:
        tracks = client.tracks(track_id)
        if not tracks:
            return None
        track = tracks[0]
        download_info = track.get_download_info()
        if not download_info:
            return None
        best_quality_url = download_info[0].get_direct_link()
        
        async with aiohttp.ClientSession() as session:
            async with session.get(best_quality_url) as response:
                if response.status != 200:
                    return None
                content = await response.read()
                
                file_name = clean_filename(f"{track.title} - {track.artists[0].name}.mp3")
                file_path = os.path.join(tempfile.gettempdir(), file_name)
                
                with open(file_path, 'wb') as f:
                    f.write(content)
                return file_path
    except Exception as e:
        print(f"Ошибка при скачивании MP3: {e}")
        return None

# 🔹 Маршруты
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/search')
def search():
    query = request.args.get('q', '')
    if not query:
        return jsonify({'error': 'No query provided'}), 400
    
    try:
        search_results = client.search(query)
        if not search_results or not search_results.tracks:
            return jsonify({'tracks': []})
        
        tracks = search_results.tracks.results[:5]
        results = []
        for track in tracks:
            results.append({
                'id': track.id,
                'title': track.title,
                'artist': track.artists[0].name if track.artists else 'Неизвестно',
                'album': track.albums[0].title if track.albums else 'Неизвестно',
                'cover': track.cover_uri.replace("%%", "400x400") if track.cover_uri else None
            })
        return jsonify({'tracks': results})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/download/<track_id>')
async def download(track_id):
    try:
        file_path = await download_music_mp3(track_id)
        if not file_path:
            return jsonify({'error': 'Failed to download track'}), 404
        
        return send_file(
            file_path,
            as_attachment=True,
            download_name=os.path.basename(file_path)
        )
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/charts')
def charts():
    try:
        chart = client.chart()
        if not chart or not chart.chart:
            return jsonify({'tracks': []})
        
        tracks = chart.chart.tracks[:10]
        results = []
        for track in tracks:
            results.append({
                'id': track.id,
                'title': track.title,
                'artist': track.artists[0].name if track.artists else 'Неизвестно',
                'album': track.albums[0].title if track.albums else 'Неизвестно',
                'cover': track.cover_uri.replace("%%", "400x400") if track.cover_uri else None
            })
        return jsonify({'tracks': results})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000))) 