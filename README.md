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
- **AI Integration**: Google Gemini 2.5 (internal), OpenAI/GGML (external)

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

## 📊 **Data Models**

The application uses MongoDB for data persistence with the following core entities:

### **Entity Relationship Overview**
```
User (1) ──────► (N) Session ──────► (N) Node
     │                   │                   │
     └─ _id              └─ user_id          └─ session_id
                             _id                 parent_id (self-ref)
                             title               role
                             created_at          content
                             updated_at          created_at
                             metadata
```

### **Collections & Indexes**

#### **Sessions Collection**
- **Purpose**: Store AI prompt crafting sessions
- **Indexes**: 
  - `user_id + created_at (desc)` - Latest sessions per user
  - `user_id` - User session queries
  - `created_at/updated_at` - Time-based queries

#### **Nodes Collection**
- **Purpose**: Store decision tree nodes for prompt evolution
- **Indexes**:
  - `session_id + parent_id` - Threaded tree queries  
  - `session_id + created_at` - Session nodes by time
  - `session_id` - Session node queries

### **Model Features**
- **Type Safety**: Pydantic models with MongoDB ObjectId support
- **Timestamps**: Automatic `created_at`/`updated_at` with UTC timezone
- **Validation**: Field length limits and required field enforcement
- **Foreign Keys**: Application-level relationship validation

## 🔐 **Authentication**

The application uses JWT-based authentication with OAuth2 social login support.

### **Available Endpoints**
- `POST /auth/register` - User registration
- `POST /auth/jwt/login` - JWT login
- `GET /auth/jwt/logout` - JWT logout  
- `GET /auth/google/login` - Google OAuth login
- `GET /auth/github/login` - GitHub OAuth login
- `GET /users/me` - Get current user profile

### **Usage Example**
```bash
# Register a new user
curl -X POST "http://localhost:8000/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "securepassword123",
    "first_name": "John",
    "last_name": "Doe"
  }'

# Login to get JWT token
curl -X POST "http://localhost:8000/auth/jwt/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=user@example.com&password=securepassword123"
```

## 📝 **Session API**

The Session API provides endpoints for creating and managing AI prompt crafting sessions.

### **Available Endpoints**
- `POST /sessions` - Create a new session
- `GET /sessions/{id}` - Get session by ID  
- `GET /sessions` - List user sessions (with pagination)

### **Usage Examples**

#### **Create a Session**
```bash
# Create a new prompt crafting session
curl -X POST "http://localhost:8000/sessions" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -d '{
    "title": "Marketing Campaign Prompt",
    "starter_prompt": "Create a comprehensive marketing plan for a new SaaS product",
    "max_questions": 15,
    "target_model": "gpt-4",
    "settings": {
      "tone": "professional",
      "wordLimit": 1000
    },
    "metadata": {
      "category": "marketing",
      "priority": "high"
    }
  }'

# Response: 201 Created with Location header
# {
#   "id": "60f7b1c8e4b0c63f4c8b4567",
#   "user_id": "60f7b1c8e4b0c63f4c8b4566",
#   "title": "Marketing Campaign Prompt",
#   "starter_prompt": "Create a comprehensive marketing plan...",
#   "max_questions": 15,
#   "target_model": "gpt-4",
#   "settings": {"tone": "professional", "wordLimit": 1000},
#   "created_at": "2023-12-01T12:00:00Z",
#   "updated_at": "2023-12-01T12:00:00Z"
# }
```

#### **Retrieve a Session**
```bash
# Get a specific session by ID
curl -X GET "http://localhost:8000/sessions/60f7b1c8e4b0c63f4c8b4567" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"

# Response: 200 OK with session data
```

#### **List User Sessions**
```bash
# Get all sessions for the authenticated user
curl -X GET "http://localhost:8000/sessions?limit=10&skip=0" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"

# Response: 200 OK with array of sessions (latest first)
```

### **Session Creation Fields**
- **starter_prompt** (required): Initial prompt text (1-5000 characters)
- **max_questions** (required): Maximum questions allowed (1-20)
- **target_model** (required): AI model to use (supported: gpt-4, claude-3-opus, etc.)
- **settings** (required): Configuration object with optional tone and wordLimit
- **title** (optional): Session title (max 200 characters)
- **metadata** (optional): Additional metadata dictionary

### **Error Responses**
- **400**: Invalid request data
- **401**: Authentication required
- **403**: Access denied (not session owner)
- **404**: Session not found
- **422**: Validation error (invalid fields)
- **429**: Rate limit exceeded

## 🤝 **Contributing**

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 **License**

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details. 