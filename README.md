# Legal Document Search and Analysis System

An intelligent legal document search and analysis system powered by RAG (Retrieval-Augmented Generation), AutoGen agents, and vector search capabilities. The system processes legal documents, enables semantic search, and provides intelligent responses using advanced language models. 

UseCase: 
You are a tax lawyer and you need to search for a specific law or a section of a law.

## 🚀 Features

- **RAG-based Search Engine**: Utilizes Pinecone for efficient vector search
- **Intelligent Agents**: Powered by AutoGen for advanced document analysis
- **Document Processing**: Automated extraction and vectorization of PDF documents
- **Legal Domain Focus**: Specialized in company law with expansion to other legal domains
- **REST API**: FastAPI-based backend for seamless integration

## 🛠️ Tech Stack

### Backend
- FastAPI - Modern web framework
- Pinecone - Vector database for semantic search
- AutoGen - Multi-agent framework
- spaCy - NLP processing
- Python Poetry/uv - Dependency management

### Document Processing
- PDF text extraction
- Text chunking and vectorization
- Semantic embedding generation

## 📁 Project Structure 

```
project_root/
├── app/
│   ├── api/
│   │   └── routes/
│   ├── core/
│   │   ├── config.py
│   │   └── settings.py
│   ├── services/
│   │   ├── document_processor/
│   │   ├── vector_store/
│   │   └── agents/
│   └── main.py
├── tests/
├── docker/
└── docs/
```

## 🗺️ Roadmap

- [x] Initial project setup
- [x] FastAPI integration
- [ ] AutoGen integration
- [ ] Poetry/uv package management
- [ ] Pinecone search implementation
- [ ] PDF processing automation
- [ ] Company law search integration
- [ ] Additional legal domains
- [ ] Docker optimization
- [ ] Docker Hub deployment

## 📝 API Documentation

Once the server is running, access the API documentation at:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## 🧪 Testing
```bash:README.md
# Run tests
pytest
```

## 🐳 Docker

The project includes Docker support for both development and production environments:

```bash
# Development
docker compose -f docker-compose.dev.yml up

# Production
docker compose up
```
