import streamlit as st
import requests

st.title("Access Resolver AI")

user_id = st.text_input("User ID")
query = st.text_input("Enter your issue")

if st.button("Resolve"):
    res = requests.post(
        "http://localhost:8000/resolve",
        json={"user_id": user_id, "query": query}
    )

    st.json(res.json())