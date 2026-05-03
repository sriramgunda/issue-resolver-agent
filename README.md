## Run the agent
### LLM	
ollama serve

### Backend
uvicorn app.main:app --reload

### UI
streamlit run ui/streamlit_app.py

### Full system
docker-compose up