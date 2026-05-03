## Get LLM and models
ollama pull nomic-embed-text   # embedding model for RAG
ollama pull qwen2.5:7b         # reasoning model

## Run the agent
### LLM	
ollama serve

### Backend
uvicorn app.main:app --reload

### UI
streamlit run ui/streamlit_app.py

### Full system
docker-compose up