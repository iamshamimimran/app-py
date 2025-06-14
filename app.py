from flask import Flask, request, jsonify
from flask_cors import CORS
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled
import re

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": ["*"]}})

PROXIES = [
    {"http": "http://103.158.253.162:8199", "https": "http://103.158.253.162:8199"},
    {"http": "http://5.106.6.235:80", "https": "http://5.106.6.235:80"},
    {"http": "http://27.189.133.66:8089", "https": "http://27.189.133.66:8089"},
    {"http": "http://117.5.27.147:1001", "https": "http://117.5.27.147:1001"},
    {"http": "http://45.39.18.189:6625", "https": "http://45.39.18.189:6625"},
]

def extract_video_id(url):
    match = re.search(r"(?:v=|\/)([0-9A-Za-z_-]{11})", url)
    return match.group(1) if match else None

@app.route("/api/get-transcript", methods=["POST"])
def get_transcript():
    data = request.get_json()
    video_url = data.get("videoUrl")

    if not video_url:
        return jsonify({"error": "videoUrl is required"}), 400

    video_id = extract_video_id(video_url)
    if not video_id:
        return jsonify({"error": "Invalid YouTube URL"}), 400

    last_error = None

    for proxy in PROXIES:
        try:
            transcript_list = YouTubeTranscriptApi.list_transcripts(video_id, proxies=proxy)
            try:
                transcript = transcript_list.find_transcript(['en', 'en-US'])
            except Exception:
                transcript = transcript_list.find_transcript(
                    transcript_list._manually_created_transcripts.keys() or
                    transcript_list._generated_transcripts.keys()
                )
            transcript_data = transcript.fetch()
            return jsonify(transcript_data)
        except TranscriptsDisabled:
            return jsonify({"error": "Transcripts are disabled for this video"}), 403
        except Exception as e:
            last_error = str(e)

    return jsonify({"error": f"All proxies failed. Last error: {last_error}"}), 500
