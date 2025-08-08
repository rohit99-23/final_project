import streamlit as st
import pymongo
import uuid
import base64
import io
from PIL import Image
import os

# MongoDB Connection
client = pymongo.MongoClient("mongodb://localhost:27017/")
db = client["mess_menu_app"]
users_collection = db["users"]

# Session state initialization
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "username" not in st.session_state:
    st.session_state.username = None
if "profile_pic" not in st.session_state:
    st.session_state.profile_pic = None

# Save image to DB
def save_profile_pic(image_data, username):
    users_collection.update_one(
        {"username": username},
        {"$set": {"profile_pic": image_data}}
    )

# Sign up function
def sign_up():
    st.subheader("Sign Up")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    uploaded_file = st.file_uploader("Upload a Profile Picture", type=["jpg", "png", "jpeg"])

    # Camera capture button (JS)
    st.markdown("""
        <style>
        .camera-container { margin-top: 10px; }
        video, canvas { max-width: 100%; border-radius: 8px; }
        </style>
        <div class="camera-container">
            <button id="start-camera">📷 Open Camera</button>
            <video id="video" autoplay playsinline style="display:none;"></video>
            <button id="click-photo" style="display:none;">Capture Photo</button>
            <canvas id="canvas" style="display:none;"></canvas>
            <p id="camera-output"></p>
        </div>
        <script>
        const startCameraBtn = document.getElementById('start-camera');
        const video = document.getElementById('video');
        const clickPhotoBtn = document.getElementById('click-photo');
        const canvas = document.getElementById('canvas');
        const output = document.getElementById('camera-output');

        startCameraBtn.addEventListener('click', async function() {
            const stream = await navigator.mediaDevices.getUserMedia({ video: true });
            video.srcObject = stream;
            video.style.display = 'block';
            clickPhotoBtn.style.display = 'inline-block';
        });

        clickPhotoBtn.addEventListener('click', function() {
            canvas.getContext('2d').drawImage(video, 0, 0, canvas.width, canvas.height);
            const imageData = canvas.toDataURL('image/png');
            output.innerHTML = '<img src="'+imageData+'" width="200"/>';
        });
        </script>
    """, unsafe_allow_html=True)

    if st.button("Sign Up"):
        if username and password:
            if users_collection.find_one({"username": username}):
                st.error("Username already exists")
            else:
                profile_pic_data = None
                if uploaded_file:
                    profile_pic_data = uploaded_file.read()
                users_collection.insert_one({
                    "username": username,
                    "password": password,
                    "profile_pic": profile_pic_data
                })
                st.success("Account created successfully!")
        else:
            st.error("Please fill all fields")

# Login function
def login():
    st.subheader("Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        user = users_collection.find_one({"username": username, "password": password})
        if user:
            st.session_state.logged_in = True
            st.session_state.username = username
            st.session_state.profile_pic = user.get("profile_pic", None)
            st.success(f"Welcome {username}!")
        else:
            st.error("Invalid username or password")

# Dashboard
def dashboard():
    st.subheader("Dashboard")

    # Top-right video record button
    st.markdown("""
        <div style="position: absolute; top: 10px; right: 10px;">
            <button id="start-record">🎥 Start Recording</button>
            <button id="stop-record" style="display:none;">⏹ Stop Recording</button>
            <video id="recorded-video" controls style="display:none; width:300px; margin-top:10px;"></video>
        </div>
        <script>
        let mediaRecorder;
        let recordedChunks = [];

        document.getElementById('start-record').addEventListener('click', async function() {
            const stream = await navigator.mediaDevices.getUserMedia({ video: true, audio: true });
            mediaRecorder = new MediaRecorder(stream);
            recordedChunks = [];
            mediaRecorder.ondataavailable = e => {
                if (e.data.size > 0) recordedChunks.push(e.data);
            };
            mediaRecorder.onstop = () => {
                const blob = new Blob(recordedChunks, { type: 'video/webm' });
                const url = URL.createObjectURL(blob);
                const video = document.getElementById('recorded-video');
                video.src = url;
                video.style.display = 'block';
            };
            mediaRecorder.start();
            document.getElementById('start-record').style.display = 'none';
            document.getElementById('stop-record').style.display = 'inline-block';
        });

        document.getElementById('stop-record').addEventListener('click', function() {
            mediaRecorder.stop();
            document.getElementById('stop-record').style.display = 'none';
            document.getElementById('start-record').style.display = 'inline-block';
        });
        </script>
    """, unsafe_allow_html=True)

    st.write(f"Welcome, {st.session_state.username}")
    if st.session_state.profile_pic:
        image = Image.open(io.BytesIO(st.session_state.profile_pic))
        st.image(image, caption="Profile Picture", width=150)

# Main app
menu = ["Login", "Sign Up", "Dashboard"]
choice = st.sidebar.selectbox("Menu", menu)

if choice == "Sign Up":
    sign_up()
elif choice == "Login":
    login()
elif choice == "Dashboard":
    if st.session_state.logged_in:
        dashboard()
    else:
        st.error("Please login first")
