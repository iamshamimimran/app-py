from flask import Flask, request, jsonify
from flask_cors import CORS
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound
from youtube_transcript_api._utils import set_proxies
import re
import requests
import random
from time import sleep

app = Flask(__name__)
CORS(app)

# List of free proxies to rotate through
PROXY_LIST = [
    {'http': 'http://51.81.245.3:17981', 'https': 'https://51.81.245.3:17981'},
    {'http': 'http://45.136.25.60:8085', 'https': 'https://45.136.25.60:8085'},
    # Add more proxies as needed
]

# Extracts the YouTube video ID from a URL
def extract_video_id(url: str) -> str | None:
    match = re.search(r"(?:v=|\/)([0-9A-Za-z_-]{11})", url)
    return match.group(1) if match else None

# Fetches a random proxy from the list
def get_random_proxy() -> dict:
    return random.choice(PROXY_LIST)

@app.route("/api/get-transcript", methods=["POST"])
def get_transcript():
    data = request.get_json()
    video_url = data.get("videoUrl")

    if not video_url:
        return jsonify({"error": "videoUrl is required"}), 400

    video_id = extract_video_id(video_url)
    if not video_id:
        return jsonify({"error": "Invalid YouTube URL"}), 400

    # Attempt to fetch the transcript using a proxy
    for _ in range(3):  # Retry up to 3 times
        proxy = get_random_proxy()
        try:
            set_proxies(proxy)
            transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)

            try:
                transcript = transcript_list.find_transcript(['en', 'en-US'])
            except NoTranscriptFound:
                transcript = transcript_list.find_transcript(
                    [t.language_code for t in transcript_list.transcripts]
                )

            transcript_data = transcript.fetch()
            return jsonify(transcript_data)

        except (TranscriptsDisabled, NoTranscriptFound) as e:
            return jsonify({"error": str(e)}), 403
        except Exception as e:
            print(f"Error with proxy {proxy}: {e}")
            sleep(2)  # Wait before retrying with a different proxy

    return jsonify({"error": "Failed to fetch transcript after multiple attempts"}), 500

if __name__ == "__main__":
    app.run(debug=True)
