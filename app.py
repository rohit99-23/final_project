import streamlit as st
import base64
import os
from io import BytesIO
from PIL import Image
import pymongo
import uuid

st.set_page_config(page_title="Camera & Profile", layout="wide")

# MongoDB Connection (example)
client = pymongo.MongoClient("mongodb://localhost:27017/")
db = client["test_db"]
users_collection = db["users"]

# Function to save image to MongoDB
def save_image_to_db(username, image_bytes):
    users_collection.update_one(
        {"username": username},
        {"$set": {"profile_pic": image_bytes}},
        upsert=True
    )

# Camera Capture HTML
camera_html = """
<script>
let videoStream;
async function startCamera() {
    const video = document.getElementById('video');
    videoStream = await navigator.mediaDevices.getUserMedia({ video: true, audio: false });
    video.srcObject = videoStream;
}

function capturePhoto() {
    const video = document.getElementById('video');
    const canvas = document.createElement('canvas');
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    canvas.getContext('2d').drawImage(video, 0, 0);
    const dataUrl = canvas.toDataURL('image/png');
    window.parent.postMessage({type: 'photo', data: dataUrl}, '*');
}

window.addEventListener('message', function(event) {
    if (event.data.type === 'start') {
        startCamera();
    }
});

</script>
<video id="video" autoplay style="width:100%;border-radius:10px;"></video>
<button onclick="capturePhoto()">📸 Capture</button>
"""

# Video Recording HTML
video_record_html = """
<script>
let recorder, recordedChunks = [];

async function startRecording() {
    const stream = await navigator.mediaDevices.getUserMedia({ video: true, audio: true });
    document.getElementById('preview').srcObject = stream;
    recordedChunks = [];
    recorder = new MediaRecorder(stream);
    recorder.ondataavailable = e => {
        if (e.data.size > 0) recordedChunks.push(e.data);
    };
    recorder.onstop = () => {
        const blob = new Blob(recordedChunks, { type: 'video/webm' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'recording.webm';
        a.click();
    };
    recorder.start();
}

function stopRecording() {
    recorder.stop();
}
</script>
<video id="preview" autoplay muted style="width:100%;border-radius:10px;"></video><br>
<button onclick="startRecording()">🎥 Start Recording</button>
<button onclick="stopRecording()">⏹ Stop Recording</button>
"""

# Sidebar/Profile section
st.sidebar.header("Profile Setup")
username = st.sidebar.text_input("Username")
uploaded_file = st.sidebar.file_uploader("Upload Profile Picture", type=["jpg", "png", "jpeg"])

if st.sidebar.button("📷 Use Camera"):
    st.components.v1.html(camera_html, height=300)

if uploaded_file:
    img = Image.open(uploaded_file)
    buf = BytesIO()
    img.save(buf, format="PNG")
    byte_im = buf.getvalue()
    save_image_to_db(username, byte_im)
    st.sidebar.image(img, caption="Profile Picture", use_container_width=True)
    st.success("Profile picture saved!")

# Main Page Layout
col1, col2 = st.columns([8, 2])

with col1:
    st.title("Welcome to Camera App")

with col2:
    if st.button("🎥 Open Camera Recorder"):
        st.components.v1.html(video_record_html, height=400)

