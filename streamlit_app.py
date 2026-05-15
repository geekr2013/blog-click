import streamlit as st
from app.poc_meeting_minutes import render_app

st.set_page_config(page_title="지시사항 추적관리", layout="wide")
render_app()
