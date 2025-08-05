import streamlit as st
import pymongo
import uuid
import base64
import io
from PIL import Image
import os

# ------------------ MongoDB Setup ------------------
MONGO_URI = st.secrets["MONGO_URI"]  # Stored in Streamlit secrets
client = pymongo.MongoClient(MONGO_URI)
db = client["project_dashboard"]
users_col = db["users"]
projects_col = db["projects"]

# ------------------ User & Project Functions ------------------

def register_user(email, password, name, college, team_no, mode, profile_pic):
    if users_col.find_one({"email": email}):
        return False, "Email already registered."

    pic_data = base64.b64encode(profile_pic.read()).decode() if profile_pic else None

    user = {
        "id": str(uuid.uuid4()),
        "email": email,
        "password": password,
        "name": name,
        "college": college,
        "team_no": team_no,
        "mode": mode,
        "profile_pic": pic_data
    }

    users_col.insert_one(user)
    return True, "Registered successfully!"

def login_user(email, password):
    return users_col.find_one({"email": email, "password": password})

def save_project(user_id, project):
    project["id"] = str(uuid.uuid4())
    project["user_id"] = user_id
    projects_col.insert_one(project)

def get_projects(user_id):
    return list(projects_col.find({"user_id": user_id}))

def delete_project(project_id):
    projects_col.delete_one({"id": project_id})

def update_project(project_id, updated_data):
    projects_col.update_one({"id": project_id}, {"$set": updated_data})

# -------------------- UI Pages --------------------

def signup():
    st.subheader("Sign Up")
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")
    name = st.text_input("Name")
    college = st.text_input("College")
    team_no = st.text_input("Team Number")
    mode = st.selectbox("Mode", ["Online", "Offline"])
    profile_pic = st.file_uploader("Upload Profile Picture", type=["png", "jpg", "jpeg"])
    if st.button("Sign Up"):
        success, msg = register_user(email, password, name, college, team_no, mode, profile_pic)
        st.success(msg) if success else st.error(msg)

def login():
    st.subheader("Login")
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        user = login_user(email, password)
        if user:
            st.session_state.user = user
            st.success("Login successful")
            st.rerun()
        else:
            st.error("Invalid credentials")

def dashboard():
    user = st.session_state.user

    if user.get("profile_pic"):
        image_data = base64.b64decode(user["profile_pic"])
        st.sidebar.image(Image.open(io.BytesIO(image_data)), width=100)

    st.sidebar.markdown(f"**{user['name']}**")
    st.sidebar.markdown(f"📍 College: {user['college']}")
    st.sidebar.markdown(f"👥 Team No: {user['team_no']}")
    st.sidebar.selectbox("Mode", ["Online", "Offline"], index=0 if user["mode"] == "Online" else 1)

    page = st.sidebar.radio("Navigation", ["Add Project", "View Projects"])

    if page == "Add Project":
        st.header("Add New Project")
        category = st.selectbox("Category", ["DevOps", "Git & Github" , "Kubernetes" ,"Python Projects", "Linux Projects", "Machine Learning", "Web"])
        sub_category = st.text_input("Sub-category")
        name = st.text_input("Project Name")
        description = st.text_area("Project Description")
        project_link = st.text_input("Project Link (https://...)")
        if st.button("Save Project"):
            save_project(user["id"], {
                "category": category,
                "sub_category": sub_category,
                "name": name,
                "description": description,
                "link": project_link
            })
            st.success("Project saved!")
            st.rerun()

    elif page == "View Projects":
        st.header("Your Projects")
        projects = get_projects(user["id"])

        if not projects:
            st.info("No projects found.")
            return

        for proj in projects:
            with st.expander(f"📁 {proj['name']} ({proj['category']} > {proj['sub_category']})"):
                st.write(proj['description'])
                if proj.get("link"):
                    st.markdown(f"🔗 [Project Link]({proj['link']})", unsafe_allow_html=True)

                col1, col2 = st.columns(2)

                with col1:
                    if st.button("🗑️ Delete", key=f"del_{proj['id']}"):
                        delete_project(proj['id'])
                        st.success("Project deleted")
                        st.rerun()

                with col2:
                    with st.form(f"edit_form_{proj['id']}"):
                        new_name = st.text_input("Project Name", value=proj['name'], key=f"name_{proj['id']}")
                        new_desc = st.text_area("Project Description", value=proj['description'], key=f"desc_{proj['id']}")
                        new_link = st.text_input("Project Link", value=proj.get("link", ""), key=f"link_{proj['id']}")
                        if st.form_submit_button("✅ Update"):
                            update_project(proj['id'], {
                                "name": new_name,
                                "description": new_desc,
                                "link": new_link
                            })
                            st.success("Project updated")
                            st.rerun()

# -------------------- App Entry Point --------------------

st.set_page_config(page_title="📌 Project Dashboard", layout="wide")

if "user" not in st.session_state:
    st.title("👤 Personal Project Dashboard")
    auth_page = st.radio("Choose Page", ["Login", "Sign Up"])
    if auth_page == "Login":
        login()
    else:
        signup()
else:
    dashboard()
