import streamlit as st
import pandas as pd
from database import get_rental_info_by_ids, search_rentals
from llm_service import LLMService
from user_service import UserService

# Initialize services
llm_service = LLMService()
user_service = UserService()

# Configure the Streamlit page
st.set_page_config(page_title="NCKU Rental System", layout="wide", page_icon="🏠")

# --- CSS Styles (Card Design) ---
st.markdown("""
<style>
    .rental-card {
        background-color: #ffffff;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        margin-bottom: 20px;
        border: 1px solid #e0e0e0;
    }
    .card-title { font-size: 1.2em; font-weight: bold; color: #333; }
    .card-info { margin-bottom: 5px; color: #555; }
    .label { font-weight: 600; color: #000; }
</style>
""", unsafe_allow_html=True)

# --- Initialize Session State ---
if 'user' not in st.session_state:
    st.session_state.user = None

# --- Helper: Render Rental Post ---
def render_post(post, collected_ids):
    """
    Render a single rental post card with a collection button.
    """
    # Check if the post is already in the user's collection
    is_collected = post["_id"] in collected_ids
    
    # Format Rental Price
    rental = post.get("租金", {})
    min_r = rental.get("minRental", 0)
    max_r = rental.get("maxRental", 0)
    rental_text = f"{min_r}元" if min_r == max_r else f"{min_r} ~ {max_r}元"
    
    # Format Layout
    layout = post.get("格局", {})
    layout_text = f"{layout.get('廳',0)}廳 {layout.get('衛',0)}衛 {layout.get('房',0)}房"
    
    # Format Contact Info
    contacts = post.get("聯絡方式", [{}])[0]
    
    # Generate HTML for the card content
    card_html = f"""
    <div class="rental-card">
        <div class="card-title">📍 {post.get("地址", "未知")}</div>
        <hr>
        <div class="card-info"><span class="label">💰 租金：</span>{rental_text}</div>
        <div class="card-info"><span class="label">🏠 格局：</span>{layout_text}</div>
        <div class="card-info"><span class="label">📐 坪數：</span>{post.get("坪數", ["未知"])[0]} 坪</div>
        <div class="card-info"><span class="label">📞 聯絡人：</span>{(contacts.get("手機") and contacts.get("手機")[0]) or "未知"}</div>
    </div>
    """
    st.markdown(card_html, unsafe_allow_html=True)
    
    # Action Button (Collect/Uncollect)
    col1, col2 = st.columns([0.8, 0.2])
    with col2:
        btn_label = "💔 取消收藏" if is_collected else "❤️ 收藏"
        if st.button(btn_label, key=f"btn_{post['_id']}"):
            if is_collected:
                user_service.remove_collection(st.session_state.user['email'], post['_id'])
                st.toast("Collection removed", icon="🗑️")
            else:
                user_service.add_collection(st.session_state.user['email'], post['_id'])
                st.toast("Added to collection", icon="✅")
            st.rerun()

# --- Page: Login ---
def login_page():
    st.title("Welcome to Rental System 🏠")
    with st.form("login_form"):
        st.write("### Login / Register")
        email = st.text_input("Email", "student@ncku.edu.tw")
        name = st.text_input("Name", "User")
        submitted = st.form_submit_button("Login")
        
        if submitted:
            # Simple authentication (get existing or create new user)
            user = user_service.get_or_create_user(email, name)
            st.session_state.user = user
            st.rerun()

# --- Page: Main Search ---
def main_page():
    st.title("🔍 Search Rentals")
    
    # Search Input
    col1, col2 = st.columns([0.85, 0.15])
    with col1:
        keyword = st.text_input("Enter your requirements (e.g., '我要一個三房一廳租金約 30000')", placeholder="Type here...")
    with col2:
        st.write("") # Spacer
        st.write("")
        search_btn = st.button("Search", type="primary")

    if search_btn and keyword:
        # 1. Record search history
        user_service.add_history(st.session_state.user['email'], keyword)
        
        # 2. Use LLM to convert natural language to MongoDB query
        with st.spinner("🤖 AI is analyzing your request..."):
            query_json = llm_service.generate_mongo_query(keyword)
        
        if query_json:
            st.success("Query generated successfully")
            with st.expander("View generated MongoDB Query"):
                st.json(query_json)
            
            # 3. Search in Database
            results = search_rentals(query_json)
            
            if not results:
                st.warning("⚠️ No rentals found matching your criteria.")
            else:
                st.write(f"Found {len(results)} results:")
                # Fetch user's current collection to update button states
                my_collections = user_service.get_collections(st.session_state.user['email'])
                
                for post in results:
                    render_post(post, my_collections)
        else:
            st.error("Could not understand your request. Please try again.")

# --- Page: My Collection ---
def collection_page():
    st.title("❤️ My Collection")
    email = st.session_state.user['email']
    collection_ids = user_service.get_collections(email)
    
    if not collection_ids:
        st.info("You haven't collected any rentals yet.")
        return

    posts = get_rental_info_by_ids(collection_ids)
    
    for post in posts:
        render_post(post, collection_ids)

# --- Page: Search History ---
def history_page():
    st.title("📜 Search History")
    email = st.session_state.user['email']
    history = user_service.get_history(email)
    
    if not history:
        st.info("No search history found.")
        return
        
    # Display history in a table
    df = pd.DataFrame(list(history.items()), columns=['Timestamp', 'Keyword'])
    st.table(df)

# --- Main App Routing ---
if st.session_state.user is None:
    login_page()
else:
    # Sidebar Navigation
    with st.sidebar:
        st.image("https://cdn-icons-png.flaticon.com/512/25/25694.png", width=50)
        st.write(f"Hi, **{st.session_state.user['name']}**")
        st.divider()
        page = st.radio("Navigation", ["Home", "Collection", "History"])
        st.divider()
        if st.button("Logout", type="secondary"):
            st.session_state.user = None
            st.rerun()

    if page == "Home":
        main_page()
    elif page == "Collection":
        collection_page()
    elif page == "History":
        history_page()