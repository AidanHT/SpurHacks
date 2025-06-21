# Promptly - Interactive AI Prompting Platform

> **Transform your ideas into perfect AI prompts through guided iteration and visual exploration.**

Promptly is an interactive web application that guides users through an iterative decision-tree of clarifying questions to craft and refine AI prompts for any large language model. Whether you're a beginner or expert, Promptly helps you create more effective prompts through intelligent questioning and visual prompt evolution.

## 🎯 **Value Proposition**

- **Guided Iteration**: AI-powered questions help refine your prompts step-by-step
- **Visual Exploration**: D3.js decision-tree visualizer shows your prompt's evolution
- **Multi-Model Support**: Target GPT-4, Claude, Llama, and other LLMs
- **Collaborative**: Share sessions, track versions, and work with teams
- **Context-Aware**: Inject files, Jira tickets, and Notion pages into prompts

## 🏗️ **Architecture Overview**

```
┌─────────────────┐    ┌──────────────┐    ┌─────────────────┐
│   Frontend      │    │   Backend    │    │   Services      │
│  (React + D3)   │◄──►│  (FastAPI)   │◄──►│ MongoDB + Redis │
│                 │    │              │    │     + MinIO     │
│ • Simple Editor │    │ • Session    │    │                 │
│ • Tree Visual   │    │   Management │    │ • Data Storage  │
│ • Collab UI     │    │ • AI Service │    │ • Caching       │
│                 │    │ • Auth       │    │ • File Storage  │
└─────────────────┘    └──────────────┘    └─────────────────┘
```

## 🛠️ **Tech Stack**

### **Frontend**
- **Framework**: React 18 + TypeScript
- **Build Tool**: Vite
- **UI Library**: Shadcn UI
- **Visualization**: D3.js for decision trees
- **Editor**: Monaco Editor / CodeMirror

### **Backend**
- **Framework**: FastAPI (Python 3.11)
- **Server**: Uvicorn
- **Authentication**: OAuth2 + JWT
- **AI Integration**: Google Gemini 3.5 (internal), OpenAI/GGML (external)

### **Infrastructure**
- **Database**: MongoDB (primary), PostgreSQL (optional)
- **Cache**: Redis
- **Storage**: MinIO (S3-compatible)
- **Containerization**: Docker + Docker Compose
- **CI/CD**: GitHub Actions

## 🚀 **Quick Start**

### **Prerequisites**
- Docker & Docker Compose
- Node.js 18+ (for development)
- Python 3.11+ (for development)

### **Development Setup**
```bash
# Clone the repository
git clone <repository-url>
cd promptly

# Copy environment template
cp .env.example .env

# Start all services
docker compose -f infra/docker-compose.yml up -d

# Verify services are running
curl http://localhost:8000/docs  # FastAPI Swagger UI
curl http://localhost:5173       # Vite dev server
```

### **Service Endpoints**
- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **MongoDB**: mongodb://localhost:27017
- **Redis**: redis://localhost:6379
- **MinIO Console**: http://localhost:9001

## 🏢 **Core Features**

### **Session Management**
- Create and update prompt sessions
- Store decision nodes and layouts in MongoDB
- Version history and branching

### **Iterative Q&A Loop**
- Single-question iterations with intelligent follow-ups
- Predefined and custom answer options
- Loop until final prompt is crafted

### **Dual UI Modes**
1. **Simple Editor**: Side-by-side draft and history with inline autocomplete
2. **Tree Visualizer**: Zoomable D3.js graph with branching and manual layout

### **Collaboration**
- OAuth2 login with role-based access
- JWT-secured session sharing
- GitHub issues import for context

### **Advanced Integrations**
- Sub-prompt splitting and merging
- Context injection from files, Jira, and Notion
- Mind-map import/export
- Specification generation

## 📁 **Project Structure**

```
promptly/
├── backend/          # FastAPI application
├── frontend/         # React + Vite application  
├── infra/           # Docker Compose & infrastructure
├── .devcontainer/   # VS Code dev container config
├── .env.example     # Environment variables template
└── README.md        # This file
```

## 🤝 **Contributing**

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 **License**

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details. 