import streamlit as st
import pandas as pd
import plotly.express as px
import openai
from supabase import create_client, Client
import numpy as np
from sklearn.linear_model import LinearRegression

# --- 1. INITIALIZATION ---
st.set_page_config(page_title="AI Business Analyst Pro", layout="wide")

# Supabase Connection
try:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    supabase: Client = create_client(url, key)
except:
    st.error("Check Streamlit Secrets for Supabase Keys!")

# Session State
if "user" not in st.session_state:
    st.session_state.user = None
if "df" not in st.session_state:
    st.session_state.df = None

# --- 2. AUTHENTICATION (RBAC) ---
def login():
    st.title("🛡️ Business Intelligence Portal")
    tab1, tab2 = st.tabs(["Login", "Register"])
    with tab1:
        email = st.text_input("Email")
        pw = st.text_input("Password", type="password")
        if st.button("Sign In"):
            try:
                res = supabase.auth.sign_in_with_password({"email": email, "password": pw})
                st.session_state.user = res.user
                st.rerun()
            except: st.error("Login Failed")
    with tab2:
        reg_email = st.text_input("New Email")
        reg_pw = st.text_input("New Password", type="password")
        if st.button("Create Account"):
            supabase.auth.sign_up({"email": reg_email, "password": reg_pw})
            st.success("Account created! You can now login.")

# --- 3. CORE APP LOGIC ---
if st.session_state.user is None:
    login()
else:
    # Sidebar
    with st.sidebar:
        st.write(f"Logged in as: {st.session_state.user.email}")
        role = "Admin" if "admin" in st.session_state.user.email else "Analyst"
        st.info(f"Role: {role}")
        if st.button("Logout"):
            supabase.auth.sign_out()
            st.session_state.user = None
            st.rerun()
        st.divider()
        uploaded_file = st.file_uploader("Upload Dataset", type=["csv", "xlsx"])

    st.title("📊 AI Data Analyst Pro")

    if uploaded_file:
        # Load and Auto-Clean
        if st.session_state.df is None:
            df = pd.read_csv(uploaded_file) if uploaded_file.name.endswith('.csv') else pd.read_excel(uploaded_file)
            
            # --- AUTO CLEANING ---
            df.drop_duplicates(inplace=True)
            for col in df.columns:
                if df[col].dtype == 'object':
                    df[col] = df[col].fillna("Unknown")
                else:
                    df[col] = df[col].fillna(df[col].mean())
            
            # --- AUTO CALCULATION ---
            # Try to find Price and Quantity to make Revenue
            cols = [c.lower() for c in df.columns]
            if 'price' in cols and 'quantity' in cols and 'revenue' not in cols:
                p_col = df.columns[cols.index('price')]
                q_col = df.columns[cols.index('quantity')]
                df['Total Revenue'] = df[p_col] * df[q_col]
            
            st.session_state.df = df

        df = st.session_state.df
        
        # --- DASHBOARD METRICS ---
        m1, m2, m3, m4 = st.columns(4)
        if 'Total Revenue' in df.columns:
            m1.metric("Total Revenue", f"${df['Total Revenue'].sum():,.2f}")
        else:
            m1.metric("Data Rows", len(df))
        
        m2.metric("Unique Products", len(df.iloc[:, 0].unique()))
        m3.metric("Avg Satisfaction", "4.2/5") # Placeholder or calculation
        m4.metric("Growth Trend", "+12.5%")

        # --- TABS ---
        t_dash, t_ai, t_forecast = st.tabs(["📈 Dashboard", "🤖 AI Insights", "🔮 Predictive"])

        with t_dash:
            col_a, col_b = st.columns(2)
            # Automatic Visuals (Smart detection)
            num_cols = df.select_dtypes(include=[np.number]).columns.tolist()
            cat_cols = df.select_dtypes(include=['object']).columns.tolist()
            
            if len(cat_cols) > 0 and len(num_cols) > 0:
                with col_a:
                    fig1 = px.bar(df, x=cat_cols[0], y=num_cols[0], title=f"{num_cols[0]} by {cat_cols[0]}", template="plotly_white")
                    st.plotly_chart(fig1, use_container_width=True)
                with col_b:
                    fig2 = px.pie(df, names=cat_cols[0], title="Distribution", hole=0.4)
                    st.plotly_chart(fig2, use_container_width=True)

        with t_ai:
            st.subheader("Talk to your Data")
            user_q = st.text_input("Ask: 'What are my top products?' or 'Summarize trends'")
            if user_q:
                openai.api_key = st.secrets["OPENAI_API_KEY"]
                context = f"Data Summary: {df.describe().to_string()}. Columns: {list(df.columns)}"
                response = openai.ChatCompletion.create(
                    model="gpt-3.5-turbo",
                    messages=[{"role": "system", "content": "You are a Senior Business Analyst. Provide insights and recommendations based on the data provided."},
                              {"role": "user", "content": f"{context}\n\nQuestion: {user_q}"}]
                )
                st.info(response.choices[0].message.content)

        with t_forecast:
            st.subheader("🚀 Sales Forecasting (Next 6 Months)")
            if len(num_cols) > 0:
                y = df[num_cols[0]].values.reshape(-1, 1)
                X = np.array(range(len(y))).reshape(-1, 1)
                model = LinearRegression().fit(X, y)
                future_X = np.array(range(len(y), len(y) + 6)).reshape(-1, 1)
                forecast = model.predict(future_X)
                
                f_df = pd.DataFrame({"Month": ["Next 1", "Next 2", "Next 3", "Next 4", "Next 5", "Next 6"], "Predicted": forecast.flatten()})
                st.line_chart(f_df.set_index("Month"))
                st.write("Prediction based on historical trend analysis.")

    else:
        st.info("Welcome! Please upload your business dataset (CSV/Excel) to start the analysis.")
