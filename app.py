import streamlit as st
import pandas as pd
import plotly.express as px
import openai
from supabase import create_client, Client

# --- 1. INITIALIZE DATABASE & API ---
# These will be pulled from your Streamlit Secrets
try:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    supabase: Client = create_client(url, key)
except Exception as e:
    st.error("Database connection missing. Check your Streamlit Secrets.")

# --- 2. SESSION STATE (To keep user logged in) ---
if "user" not in st.session_state:
    st.session_state.user = None

# --- 3. AUTHENTICATION UI ---
if st.session_state.user is None:
    st.title("🔐 Company Data Portal")
    auth_mode = st.tabs(["Login", "Register"])

    # LOGIN TAB
    with auth_mode[0]:
        login_email = st.text_input("Email", key="login_email")
        login_password = st.text_input("Password", type="password", key="login_pw")
        if st.button("Login"):
            try:
                res = supabase.auth.sign_in_with_password({"email": login_email, "password": login_password})
                st.session_state.user = res.user
                st.success("Login successful!")
                st.rerun()
            except Exception as e:
                st.error("Invalid email or password.")

    # REGISTRATION TAB
    with auth_mode[1]:
        st.subheader("Create a New Account")
        reg_email = st.text_input("Email", key="reg_email")
        reg_password = st.text_input("Password", type="password", key="reg_pw")
        if st.button("Register"):
            try:
                # This creates the user in Supabase
                res = supabase.auth.sign_up({"email": reg_email, "password": reg_password})
                st.success("Registration successful! You can now login.")
                st.info("Note: Check your email for a confirmation link if required by your settings.")
            except Exception as e:
                st.error(f"Registration failed: {e}")

# --- 4. THE MAIN APP (Only visible if logged in) ---
else:
    with st.sidebar:
        st.write(f"Logged in as: **{st.session_state.user.email}**")
        if st.button("Logout"):
            supabase.auth.sign_out()
            st.session_state.user = None
            st.rerun()
        
        st.divider()
        uploaded_file = st.file_uploader("Upload Business Data", type=["csv", "xlsx"])

    st.title("📊 AI Dataset Analysis Dashboard")

    if uploaded_file:
        df = pd.read_csv(uploaded_file) if uploaded_file.name.endswith('.csv') else pd.read_excel(uploaded_file)
        
        tab1, tab2, tab3 = st.tabs(["Overview", "Visualization", "AI Assistant"])
        
        with tab1:
            st.dataframe(df.head())
            st.metric("Total Rows", len(df))
            
        with tab2:
            cols = df.columns.tolist()
            x = st.selectbox("Select X Axis", cols)
            y = st.selectbox("Select Y Axis", cols)
            st.plotly_chart(px.bar(df, x=x, y=y))
            
        with tab3:
            user_q = st.text_input("Ask AI about this data")
            if user_q:
                openai.api_key = st.secrets["OPENAI_API_KEY"]
                st.info("AI is analyzing...")
                response = openai.ChatCompletion.create(
                    model="gpt-3.5-turbo",
                    messages=[{"role": "user", "content": f"Columns: {df.columns.tolist()}. Question: {user_q}"}]
                )
                st.write(response.choices[0].message.content)
    else:
        st.info("Welcome! Please upload a file to start.")
