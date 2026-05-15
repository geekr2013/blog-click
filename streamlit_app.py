import streamlit as st
from app.poc_meeting_minutes import render_app

st.set_page_config(page_title="회의록 POC v2", layout="wide")
render_app()
