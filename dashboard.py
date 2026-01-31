import streamlit as st
import asyncio
import pandas as pd
import plotly.express as px
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text
from app.core.config import settings

# Database Connection (Reusing for Streamlit)
engine = create_async_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(bind=engine, class_=AsyncSession)

st.set_page_config(page_title="TrustLayer AI Dashboard", layout="wide")

st.title("🛡️ TrustLayer AI - Governance Dashboard")

async def load_data():
    async with SessionLocal() as session:
        result = await session.execute(text("SELECT entity_type, count, timestamp FROM audit_logs"))
        data = result.fetchall()
        return data

from app.core.database import init_db # Import init_db

# Load Data
try:
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    # Initialize DB (Create tables if they don't exist)
    loop.run_until_complete(init_db())
    
    data = loop.run_until_complete(load_data())
    
    if data:
        df = pd.DataFrame(data, columns=["Entity Type", "Count", "Timestamp"])
        
        # Metrics
        total_redactions = df["Count"].sum()
        unique_entities = df["Entity Type"].nunique()
        
        col1, col2 = st.columns(2)
        col1.metric("Total PII Tokens Redacted", total_redactions)
        col2.metric("Unique Entity Types Detected", unique_entities)
        
        # Charts
        st.subheader("Redaction Activity by Entity Type")
        grouped = df.groupby("Entity Type")["Count"].sum().reset_index()
        fig = px.bar(grouped, x="Entity Type", y="Count", color="Entity Type")
        st.plotly_chart(fig, use_container_width=True)
        
        st.subheader("Recent Logs")
        st.dataframe(df.sort_values("Timestamp", ascending=False).head(50))
        
    else:
        st.info("No audit logs found yet. Send some requests!")

except Exception as e:
    st.error(f"Error connecting to database: {e}")
    st.write("Make sure the FastAPI app has been passed at least once to create the DB.")

st.sidebar.markdown("### Controls")
if st.sidebar.button("Refresh Data"):
    st.rerun()
