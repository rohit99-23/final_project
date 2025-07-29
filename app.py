import streamlit as st
import json
import uuid
from PIL import Image
import io
import base64

# ------------------ JSON File Helpers ------------------

def load_json(file):
    with open(file, "r") as f:
        return json.load(f)

def save_json(file, data):
    with open(file, "w") as f:
        json.dump(data, f, indent=4)

# ------------------ User & Project Functions ------------------

def register_user(email, password, name, college, team_no, mode, profile_pic):
    users = load_json("users.json")
    if any(u["email"] == email for u in users):
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

    users.append(user)
    save_json("users.json", users)
    return True, "Registered successfully!"

def login_user(email, password):
    users = load_json("users.json")
    for user in users:
        if user["email"] == email and user["password"] == password:
            return user
    return None

def save_project(user_id, project):
    projects = load_json("projects.json")
    project["id"] = str(uuid.uuid4())
    project["user_id"] = user_id
    projects.append(project)
    save_json("projects.json", projects)

def get_projects(user_id):
    projects = load_json("projects.json")
    return [p for p in projects if p["user_id"] == user_id]

def delete_project(project_id):
    projects = load_json("projects.json")
    projects = [p for p in projects if p["id"] != project_id]
    save_json("projects.json", projects)

def update_project(project_id, updated_data):
    projects = load_json("projects.json")
    for p in projects:
        if p["id"] == project_id:
            p.update(updated_data)
    save_json("projects.json", projects)

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
        category = st.selectbox("Category", ["DevOps", "Python Projects", "Linux Projects", "Machine Learning", "Web"])
        sub_category = st.text_input("Sub-category")
        name = st.text_input("Project Name")
        description = st.text_area("Project Description")
        if st.button("Save Project"):
            save_project(user["id"], {
                "category": category,
                "sub_category": sub_category,
                "name": name,
                "description": description
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
                        if st.form_submit_button("✅ Update"):
                            update_project(proj['id'], {"name": new_name, "description": new_desc})
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
