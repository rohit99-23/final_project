import streamlit as st
import pymongo
from bson.objectid import ObjectId
from PIL import Image
import io

# -------------------- MongoDB Configuration --------------------
MONGO_URI = "mongodb://localhost:27017"
DB_NAME = "project_dashboard"
COLLECTION_NAME = "projects"
USER_COLLECTION = "users"

client = pymongo.MongoClient(MONGO_URI)
db = client[DB_NAME]
projects_collection = db[COLLECTION_NAME]
users_collection = db[USER_COLLECTION]

# -------------------- Helper Functions --------------------
def save_project(user_id, project):
    project["user_id"] = user_id
    projects_collection.insert_one(project)

def get_projects(user_id):
    return list(projects_collection.find({"user_id": user_id}))

def delete_project(project_id):
    projects_collection.delete_one({"_id": ObjectId(project_id)})

def update_project(project_id, updated_data):
    projects_collection.update_one({"_id": ObjectId(project_id)}, {"$set": updated_data})

def register_user(email, password, name, college, team_no, mode, profile_pic):
    if users_collection.find_one({"email": email}):
        return False, "Email already registered."
    user_data = {
        "email": email,
        "password": password,
        "name": name,
        "college": college,
        "team_no": team_no,
        "mode": mode,
        "profile_pic": profile_pic.read() if profile_pic else None
    }
    users_collection.insert_one(user_data)
    return True, "Registered successfully!"

def login_user(email, password):
    return users_collection.find_one({"email": email, "password": password})

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
    st.sidebar.image(Image.open(io.BytesIO(st.session_state.user['profile_pic'])), width=100)
    st.sidebar.markdown(f"**{st.session_state.user['name']}**")
    st.sidebar.markdown(f"📍 College: {st.session_state.user['college']}")
    st.sidebar.markdown(f"👥 Team No: {st.session_state.user['team_no']}")
    st.sidebar.selectbox("Mode", ["Online", "Offline"], index=0 if st.session_state.user['mode'] == "Online" else 1)

    page = st.sidebar.radio("Navigation", ["Add Project", "View Projects"])

    if page == "Add Project":
        st.header("Add New Project")
        category = st.selectbox("Category", ["DevOps", "Python Projects", "Linux Projects", "Machine Learning", "Web"])
        sub_category = st.text_input("Sub-category")
        name = st.text_input("Project Name")
        description = st.text_area("Project Description")
        if st.button("Save Project"):
            save_project(st.session_state.user['_id'], {
                "category": category,
                "sub_category": sub_category,
                "name": name,
                "description": description
            })
            st.success("Project saved!")
            st.rerun()

    elif page == "View Projects":
        st.header("Your Projects")
        projects = get_projects(st.session_state.user['_id'])

        if not projects:
            st.info("No projects found.")
            return

        for proj in projects:
            with st.expander(f"📁 {proj['name']} ({proj['category']} > {proj['sub_category']})"):
                st.write(proj['description'])

                col1, col2 = st.columns(2)

                with col1:
                    if st.button("🗑️ Delete", key=f"del_{proj['_id']}"):
                        delete_project(proj['_id'])
                        st.success("Project deleted")
                        st.rerun()

                with col2:
                    with st.form(f"edit_form_{proj['_id']}"):
                        new_name = st.text_input("Project Name", value=proj['name'], key=f"name_{proj['_id']}")
                        new_desc = st.text_area("Project Description", value=proj['description'], key=f"desc_{proj['_id']}")
                        if st.form_submit_button("✅ Update"):
                            update_project(proj['_id'], {"name": new_name, "description": new_desc})
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
