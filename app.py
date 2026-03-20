import streamlit as st
import pandas as pd
import plotly.express as px
import openai

# --- 1. CONFIGURATION & LOGIN ---
st.set_page_config(page_title="AI Data Analyst Pro", layout="wide")

def check_password():
    """Returns True if the user had the correct password."""
    def password_entered():
        if st.session_state["password"] == st.secrets["password"]:
            st.session_state["password_correct"] = True
            del st.session_state["password"] 
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        st.title("🔒 Company Data Portal")
        st.text_input("Enter Access Password", type="password", on_change=password_entered, key="password")
        return False
    elif not st.session_state["password_correct"]:
        st.title("🔒 Company Data Portal")
        st.text_input("Enter Access Password", type="password", on_change=password_entered, key="password")
        st.error("❌ Password incorrect")
        return False
    else:
        return True

# --- 2. START OF THE APP ---
if check_password():
    
    # Sidebar
    with st.sidebar:
        st.title("Settings")
        if st.button("Logout"):
            st.session_state["password_correct"] = False
            st.rerun()
        
        st.divider()
        st.header("Upload Center")
        uploaded_file = st.file_uploader("Choose CSV or Excel", type=["csv", "xlsx"])
        
        st.divider()
        # Optional: Allow user to override API key if not in secrets
        api_key_input = st.text_input("OpenAI API Key (optional)", type="password")
        final_api_key = api_key_input if api_key_input else st.secrets.get("OPENAI_API_KEY", "")

    st.title("📊 AI Dataset Analysis Dashboard")
    st.markdown("Automated insights and professional visualizations for your business data.")

    if uploaded_file:
        # Load Data
        try:
            if uploaded_file.name.endswith('.csv'):
                df = pd.read_csv(uploaded_file)
            else:
                df = pd.read_excel(uploaded_file)
            
            # --- TABS ---
            tab1, tab2, tab3, tab4 = st.tabs(["📋 Data Overview", "🛠️ Cleaning", "📈 Charts", "🤖 AI Analyst"])

            # TAB 1: OVERVIEW
            with tab1:
                st.subheader("Data Summary")
                col1, col2, col3 = st.columns(3)
                col1.metric("Rows", df.shape[0])
                col2.metric("Columns", df.shape[1])
                col3.metric("Empty Cells", df.isna().sum().sum())
                
                st.dataframe(df.head(10), use_container_width=True)
                st.write("### Descriptive Statistics")
                st.write(df.describe())

            # TAB 2: CLEANING
            with tab2:
                st.subheader("Data Processing")
                if st.button("Remove Duplicates & Fill Missing Values"):
                    df = df.drop_duplicates()
                    # Fill numeric with mean, objects with "Unknown"
                    for col in df.columns:
                        if df[col].dtype == "object":
                            df[col] = df[col].fillna("Unknown")
                        else:
                            df[col] = df[col].fillna(df[col].mean())
                    st.success("Data Cleaned Successfully!")
                    st.dataframe(df.head(5))

            # TAB 3: CHARTS
            with tab3:
                st.subheader("Visual Analysis")
                cols = df.columns.tolist()
                c1, c2, c3 = st.columns(3)
                chart_type = c1.selectbox("Type", ["Bar", "Line", "Scatter", "Histogram"])
                x_axis = c2.selectbox("X-Axis", cols)
                y_axis = c3.selectbox("Y-Axis", cols)

                if chart_type == "Bar":
                    fig = px.bar(df, x=x_axis, y=y_axis, color_discrete_sequence=['#00CC96'])
                elif chart_type == "Line":
                    fig = px.line(df, x=x_axis, y=y_axis)
                elif chart_type == "Scatter":
                    fig = px.scatter(df, x=x_axis, y=y_axis)
                else:
                    fig = px.histogram(df, x=x_axis)
                
                st.plotly_chart(fig, use_container_width=True)

            # TAB 4: AI ANALYST
            with tab4:
                st.subheader("Ask the AI Assistant")
                user_question = st.text_input("Ask a question about your data (e.g., 'What are the top 3 trends?')")
                
                if user_question:
                    if not final_api_key:
                        st.error("Please provide an OpenAI API Key to use this feature.")
                    else:
                        try:
                            openai.api_key = final_api_key
                            # Send column names and stats summary to save tokens/cost
                            data_context = f"Columns: {list(df.columns)}. Summary: {df.describe().to_dict()}"
                            
                            response = openai.ChatCompletion.create(
                                model="gpt-3.5-turbo",
                                messages=[
                                    {"role": "system", "content": "You are a professional business data analyst."},
                                    {"role": "user", "content": f"Based on this data context: {data_context}. Answer this: {user_question}"}
                                ]
                            )
                            st.info("### AI Analysis:")
                            st.write(response.choices[0].message.content)
                        except Exception as e:
                            st.error(f"AI Error: {e}")

        except Exception as e:
            st.error(f"Error loading file: {e}")
    else:
        st.info("💡 Please upload a CSV or Excel file via the sidebar to begin.")
