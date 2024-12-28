import os
import openai
from flask import Flask, render_template, request, send_file
from youtube_transcript_api import YouTubeTranscriptApi
from fpdf import FPDF

# Set your OpenAI API key from environment variable
openai.api_key = os.getenv('OPENAI_API_KEY')

app = Flask(__name__)

def get_video_id(youtube_url):
    if "youtube.com/watch?v=" in youtube_url:
        return youtube_url.split("v=")[1]
    elif "youtu.be/" in youtube_url:
        return youtube_url.split("/")[-1]
    else:
        raise ValueError("Invalid YouTube URL")

def fetch_transcript(video_id):
    try:
        transcript_list = YouTubeTranscriptApi.get_transcript(video_id)
        transcript = " ".join([entry['text'] for entry in transcript_list])
        return transcript
    except Exception as e:
        print(f"Error fetching transcript: {e}")
        return None

def summarize_transcript(transcript):
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": f"Please summarize the following transcript into notes:\n\n{transcript}"}
        ]
    )
    notes = response['choices'][0]['message']['content'].strip()
    return notes

def save_notes_to_pdf(notes, filename="notes.pdf"):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.set_font("Arial", size=12)

    for line in notes.split('\n'):
        pdf.multi_cell(0, 10, line)

    pdf.output(filename)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        youtube_url = request.form['youtube_url']
        video_id = get_video_id(youtube_url)
        transcript = fetch_transcript(video_id)
        
        if transcript:
            notes = summarize_transcript(transcript)
            save_notes_to_pdf(notes, filename="notes.pdf")
            return send_file("notes.pdf", as_attachment=True)
        else:
            return "Failed to fetch transcript."
    return render_template('index.html')

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)), debug=True)
