from flask import Flask, request, jsonify
from flask_cors import CORS
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled
import re

app = Flask(__name__)
CORS(app)

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

    try:
        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
        try:
            transcript = transcript_list.find_transcript(['en', 'en-US'])
        except Exception:
            transcript = transcript_list.find_transcript(
                list(transcript_list._manually_created_transcripts.keys()) or
                list(transcript_list._generated_transcripts.keys())
            )
        transcript_data = transcript.fetch()
        return jsonify(transcript_data)

    except TranscriptsDisabled:
        return jsonify({"error": "Transcripts are disabled for this video"}), 403
    except Exception as e:
        return jsonify({"error": str(e)}), 500
