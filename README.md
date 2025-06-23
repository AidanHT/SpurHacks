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

## 🧠 **AI Integration**

Promptly integrates with Google Gemini 2.5 as the primary AI service for prompt refinement and intelligent questioning.

### **Configuration**

Set the following environment variables in your `.env` file:

```bash
# Required - Get from Google AI Studio
GEMINI_API_KEY=your-gemini-api-key

# Optional - Custom API endpoint
GEMINI_BASE_URL=https://generativelanguage.googleapis.com/v1beta

# Optional - Model parameters
GEMINI_MODEL=gemini-2.0-flash-exp
GEMINI_MAX_TOKENS=4096
GEMINI_TEMPERATURE=0.7
```

### **Features**

- **Smart Input Processing**: Automatic prompt truncation at 2,000 characters with `…[truncated]` marker
- **Reliable Communication**: Exponential backoff retry (1s, 2s, 4s) on server errors with jitter
- **Context Injection**: System message automatically added: `"You are Gemini 2.5, respond concisely."`
- **Performance Optimized**: Shared HTTP client singleton for connection pooling
- **Security First**: API keys never logged; requests truncated to 100 chars in logs

### **Usage Example**

```python
from backend.services import ask_gemini, GeminiServiceError

# Basic usage
try:
    response = await ask_gemini({
        "prompt": "Help me create a marketing prompt for a SaaS product",
        "temperature": 0.7,
        "max_tokens": 1000
    })
    print(response["candidates"][0]["content"]["parts"][0]["text"])
except GeminiServiceError as e:
    print(f"AI service error {e.status}: {e.detail}")
```

### **Error Handling**

The AI service implements comprehensive error handling:

- **Validation Errors** (`ValueError`): Invalid input parameters
- **Configuration Errors** (`GeminiServiceError 500`): Missing API key
- **Client Errors** (`GeminiServiceError 4xx`): No retry, immediate failure
- **Server Errors** (`GeminiServiceError 5xx`): Automatic retry with exponential backoff
- **Timeout Errors** (`GeminiServiceError 408`): Retry on network timeouts

### **Character Limit Rule**

Prompts exceeding 2,000 characters are automatically truncated to prevent API errors:
- **Input**: `"x" * 2500`
- **Processed**: `"x" * 1985 + "…[truncated]"` (exactly 2,000 chars)

This ensures reliable API communication while preserving prompt intent.

## 🤝 **Contributing**

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 **License**

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details. 

## Key Features

### Core Functionality
- **Iterative Q&A Loop**: AI-guided refinement through targeted questions
- **Session Management**: Create, update, and track prompt crafting sessions
- **Multiple UI Modes**: Simple editor with live suggestions and D3.js decision-tree visualizer
- **User Profiles**: OAuth2 authentication with session sharing and version history
- **Multi-Model Support**: Target external models (GPT-4, Claude, Llama) with internal refinement on Google Gemini 2.5

### Advanced Features
- **Context Injection**: Import context from files, Jira, Notion
- **Sub-prompt Splitting**: Break down complex prompts into manageable parts
- **Mind-map Integration**: Import/export mind-maps for visual prompt planning
- **Collaboration Tools**: Role-based access control and GitHub issues import
- **Spec Generation**: Auto-generate prompt specifications

## Tech Stack

- **Frontend**: React, TypeScript, Vite, D3.js, Shadcn UI *(Coming Soon)*
- **Backend**: Python 3.11, FastAPI, Uvicorn, Docker
- **Database**: MongoDB (+ optional PostgreSQL)
- **Authentication**: OAuth2/JWT with Google and GitHub
- **AI Integration**: Google Gemini 2.5, OpenAI/GGML
- **DevOps**: Docker, GitHub Actions CI/CD

## Quick Start

### Prerequisites
- Python 3.11+
- MongoDB
- Redis
- Google Gemini API key

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd SpurHacks
   ```

2. **Set up environment**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

3. **Install dependencies**
   ```bash
   cd backend
   poetry install
   ```

4. **Start services**
   ```bash
   # Using Docker Compose (recommended)
   docker-compose -f infra/docker-compose.yml up -d
   
   # Or manually start MongoDB and Redis
   ```

5. **Run the application**
   ```bash
   cd backend
   poetry run uvicorn main:app --reload --host 0.0.0.0 --port 8000
   ```

## API Documentation

### Authentication

All API endpoints (except health checks) require authentication via JWT bearer tokens.

```bash
# Register a new user
POST /auth/register
{
  "email": "user@example.com", 
  "password": "secure_password",
  "username": "username"
}

# Login
POST /auth/jwt/login
{
  "username": "user@example.com",
  "password": "secure_password"
}
```

### Session Management

#### Create a Session
```bash
POST /sessions
Authorization: Bearer <token>
Content-Type: application/json

{
  "title": "My Creative Writing Session",
  "starterPrompt": "Help me write a compelling story",
  "maxQuestions": 5,
  "targetModel": "gpt-4",
  "settings": {
    "tone": "creative",
    "wordLimit": 500
  }
}
```

**Response:**
```json
{
  "id": "507f1f77bcf86cd799439011",
  "userId": "507f1f77bcf86cd799439012",
  "title": "My Creative Writing Session",
  "starterPrompt": "Help me write a compelling story",
  "maxQuestions": 5,
  "targetModel": "gpt-4",
  "settings": {"tone": "creative", "wordLimit": 500},
  "status": "active",
  "createdAt": "2024-01-15T10:30:00Z",
  "updatedAt": "2024-01-15T10:30:00Z"
}
```

#### List Sessions
```bash
GET /sessions?limit=20&skip=0
Authorization: Bearer <token>
```

#### Get Session Details
```bash
GET /sessions/{session_id}
Authorization: Bearer <token>
```

### File Uploads

Promptly supports secure file uploads for context injection into AI prompting sessions.

#### Upload a File
```bash
POST /api/files
Authorization: Bearer <token>
Content-Type: multipart/form-data

# Upload with optional session linking
curl -X POST "http://localhost:8000/api/files?session_id=507f1f77bcf86cd799439011" \
  -H "Authorization: Bearer <token>" \
  -F "file=@document.pdf"
```

**Response:**
```json
{
  "fileId": "550e8400-e29b-41d4-a716-446655440000",
  "url": "https://minio:9000/promptly-files/session-id/file-id-filename.pdf?X-Amz-Algorithm=...",
  "size": 12345,
  "mime": "application/pdf"
}
```

#### File Upload Features
- **Size Limit**: Maximum 20 MB per file
- **Security**: Dangerous file types automatically rejected (`.exe`, `.bat`, `.js`, etc.)
- **Storage**: Files stored in MinIO with S3-compatible interface
- **Access Control**: 24-hour presigned URLs for secure access
- **Session Integration**: Files automatically linked to sessions as context sources

#### Get File Information
```bash
GET /api/files/{file_id}
Authorization: Bearer <token>
```

#### Supported File Types
✅ Documents (PDF, DOC, TXT), Images (JPG, PNG, GIF), Data (JSON, CSV, XML)
❌ Executables, Scripts, Dangerous MIME types

### Iterative Q&A Loop

The core feature of Promptly is the iterative Q&A loop that refines prompts through AI-generated questions.

#### Submit an Answer
```bash
POST /sessions/{session_id}/answer
Authorization: Bearer <token>
Content-Type: application/json

{
  "nodeId": "507f1f77bcf86cd799439013",
  "selected": "Fantasy",
  "cancel": false
}
```

**Question Response:**
```json
{
  "question": "What type of fantasy setting would you prefer?",
  "options": [
    "Medieval fantasy with dragons and magic",
    "Urban fantasy in modern world",
    "High fantasy with elves and orcs",
    "Dark fantasy with horror elements"
  ],
  "nodeId": "507f1f77bcf86cd799439014"
}
```

**Final Prompt Response:**
```json
{
  "finalPrompt": "Write a medieval fantasy story about a young blacksmith who discovers they can forge magical weapons. The story should be creative and engaging, with rich world-building and compelling characters. Target length: approximately 500 words. Include elements of adventure and personal growth.",
  "nodeId": "507f1f77bcf86cd799439015"
}
```

### Q&A Loop Flow

1. **Session Creation**: User creates a session with initial prompt and preferences
2. **Initial Question**: AI generates first clarifying question based on starter prompt
3. **Iterative Refinement**: 
   - User selects from provided options
   - AI generates next question or final prompt
   - Process continues until completion
4. **Completion**: Session marked as "completed" with final refined prompt

### Stop Conditions

The Q&A loop stops when:
- **Maximum questions reached**: Configured via `maxQuestions` (1-20)
- **Final prompt generated**: AI determines enough information has been gathered
- **User cancellation**: Setting `"cancel": true` in answer request
- **Session completed/cancelled**: Session status prevents further questions

### Error Handling

**Common Error Responses:**
```json
// Invalid input
{
  "detail": "Invalid session or node ID format",
  "status_code": 422
}

// Access denied
{
  "detail": "Access denied: You can only access your own sessions",
  "status_code": 403
}

// Resource not found
{
  "detail": "Session not found",
  "status_code": 404
}

// Rate limiting
{
  "detail": "Rate limit exceeded",
  "status_code": 429
}

// AI service error
{
  "detail": "AI service error: Request timeout",
  "status_code": 502
}
```

## Example Usage Flow

Here's a complete example of using the Q&A loop:

```python
import requests

# 1. Create session
session_response = requests.post("http://localhost:8000/sessions", 
    headers={"Authorization": f"Bearer {token}"},
    json={
        "title": "Story Writing Assistant",
        "starterPrompt": "Help me write an engaging short story",
        "maxQuestions": 3,
        "targetModel": "gpt-4",
        "settings": {"tone": "creative", "wordLimit": 800}
    }
)
session_id = session_response.json()["id"]

# 2. Start with initial question node (you'll need to create this first)
# In practice, this would be done by your frontend/application logic

# 3. First Q&A iteration
answer_response = requests.post(f"http://localhost:8000/sessions/{session_id}/answer",
    headers={"Authorization": f"Bearer {token}"},
    json={
        "nodeId": "initial_question_node_id",
        "selected": "Science Fiction"
    }
)

if "question" in answer_response.json():
    # AI asked another question
    question_data = answer_response.json()
    print(f"Question: {question_data['question']}")
    print(f"Options: {question_data['options']}")
    
    # 4. Second Q&A iteration
    answer_response = requests.post(f"http://localhost:8000/sessions/{session_id}/answer",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "nodeId": question_data["nodeId"],
            "selected": "Space exploration and alien contact"
        }
    )

if "finalPrompt" in answer_response.json():
    # AI provided final refined prompt
    final_data = answer_response.json()
    print(f"Final Prompt: {final_data['finalPrompt']}")
```

## Development

### Running Tests
```bash
cd backend
poetry run pytest -v
```

### Code Quality
```bash
# Linting
poetry run flake8 .

# Type checking
poetry run mypy .
```

### API Documentation
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Configuration

Key environment variables:

```env
# Database
MONGODB_URL=mongodb://localhost:27017/promptly
REDIS_URL=redis://localhost:6379

# Authentication
JWT_SECRET_KEY=your-secret-key-here
GOOGLE_CLIENT_ID=your-google-oauth-client-id
GITHUB_CLIENT_ID=your-github-oauth-client-id

# AI Services
GEMINI_API_KEY=your-gemini-api-key

# File Storage (MinIO)
MINIO_ENDPOINT=minio:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=change-this-minio-password
MINIO_BUCKET=promptly-files
MINIO_SECURE=false
MINIO_URL_EXPIRY_HOURS=24

# Application
CORS_ORIGINS=http://localhost:5173,http://localhost:5174
ENVIRONMENT=development
DEBUG=true
```

### MinIO Configuration Reference

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `MINIO_ENDPOINT` | MinIO server endpoint | `minio:9000` | ✅ |
| `MINIO_ACCESS_KEY` | MinIO access key | `minioadmin` | ✅ |
| `MINIO_SECRET_KEY` | MinIO secret key | `minioadmin` | ✅ |
| `MINIO_BUCKET` | Storage bucket name | `promptly-files` | ✅ |
| `MINIO_SECURE` | Use HTTPS connection | `false` | ❌ |
| `MINIO_URL_EXPIRY_HOURS` | Presigned URL expiry | `24` | ❌ |

## Architecture

### Backend Structure
```
backend/
├── api/           # FastAPI route handlers
├── auth/          # Authentication & authorization
├── core/          # Database, caching, rate limiting
├── models/        # Pydantic models & MongoDB schemas
├── services/      # Business logic & external integrations
└── tests/         # Test suite
```

### Data Models

**Session**: Represents a prompt crafting session
- User ownership and permissions
- Configuration (max questions, target model, settings)
- Status tracking (active, completed, cancelled)

**Node**: Represents a step in the decision tree
- Hierarchical structure (parent-child relationships)
- Role-based content (user answers, AI questions/responses)
- Type classification (question, answer, final prompt)
- Raw AI response storage for debugging

**User**: Authentication and user management
- OAuth2 integration
- JWT token handling
- Session ownership

## 🎨 **Frontend**

The Promptly frontend is a modern React application built with TypeScript, Vite, and Tailwind CSS.

### **Tech Stack**
- **Framework**: React 18 + TypeScript
- **Build Tool**: Vite for fast development and optimized builds
- **Styling**: Tailwind CSS with dark mode support
- **State Management**: Redux Toolkit with RTK Query
- **Routing**: React Router DOM v6
- **Icons**: Heroicons
- **Development**: ESLint, Prettier, Hot Module Replacement

### **Getting Started**

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview
```

### **Development Scripts**

| Command | Description |
|---------|-------------|
| `npm run dev` | Start Vite dev server at http://localhost:5173 |
| `npm run build` | Build for production |
| `npm run preview` | Preview production build |
| `npm run lint` | Run ESLint checks |
| `npm run lint:fix` | Fix ESLint issues automatically |
| `npm run format` | Format code with Prettier |
| `npm run type-check` | Run TypeScript type checking |

### **Project Structure**

```
frontend/
├── public/
│   └── logo.png              # Brand logo asset
├── src/
│   ├── assets/               # Static assets (images, fonts)
│   ├── hooks/                # Custom React hooks
│   │   └── redux.ts          # Typed Redux hooks
│   ├── layouts/              # Page layout components
│   │   └── AppLayout.tsx     # Main authenticated app layout
│   ├── pages/                # Page components
│   │   ├── HomePage.tsx      # Landing page
│   │   ├── LoginPage.tsx     # Authentication page
│   │   └── SignUpPage.tsx    # Registration page
│   ├── providers/            # React context providers
│   │   └── ThemeProvider.tsx # Dark/light mode provider
│   ├── routes/               # Route protection
│   │   └── ProtectedRoute.tsx# Auth-protected routes
│   ├── services/             # API integration
│   │   └── api.ts            # RTK Query API definitions
│   ├── slices/               # Redux slices
│   │   ├── authSlice.ts      # Authentication state
│   │   ├── sessionsSlice.ts  # Session management
│   │   └── nodesSlice.ts     # Node/tree management
│   ├── utils/                # Utility functions
│   ├── App.tsx               # Main app component
│   ├── main.tsx              # React entry point
│   ├── store.ts              # Redux store configuration
│   └── index.css             # Global styles & Tailwind
├── .env                      # Environment variables
├── package.json              # Dependencies & scripts
├── tailwind.config.js        # Tailwind configuration
├── tsconfig.json             # TypeScript configuration
└── vite.config.ts            # Vite configuration
```

### **Features**

#### **🏠 Landing Page**
- Beautiful, responsive homepage with project overview
- Dark/light/system theme support
- Call-to-action buttons for signup and login
- Feature highlights and value proposition

#### **🔐 Authentication**
- Login and registration forms
- Validation and error handling
- JWT token management with localStorage persistence
- Automatic token refresh handling
- Protected route redirection

#### **📱 Responsive Layout**
- Mobile-first responsive design
- Sidebar navigation with hamburger menu
- Profile dropdown with user management
- Theme toggle in header
- Consistent branding across all pages

#### **🎨 Design System**
- Consistent color palette based on brand colors
- Dark mode support throughout
- Accessible components with proper ARIA labels
- Tailwind CSS utility classes
- Custom CSS variables for theming

### **Environment Configuration**

Create a `.env` file in the frontend directory:

```env
# API Configuration
VITE_API_URL=http://localhost:8000
VITE_APP_NAME=Promptly

# Development
VITE_DEV_MODE=true

# Authentication
VITE_JWT_STORAGE_KEY=jwt-token

# Theme
VITE_THEME_STORAGE_KEY=promptly-ui-theme
```

### **Theme Configuration**

The application supports three theme modes:
- **Light**: Traditional light theme
- **Dark**: Dark theme for low-light environments  
- **System**: Automatically follows system preference

Theme state is persisted in localStorage and applied via CSS classes.

### **API Integration**

The frontend uses RTK Query for efficient API communication:

```typescript
// Example API usage
import { useGetSessionsQuery } from '../services/api';

function SessionsList() {
  const { data: sessions, isLoading, error } = useGetSessionsQuery();
  
  // Component logic
}
```

### **State Management**

Redux Toolkit manages application state:

```typescript
// Example state usage
import { useAppSelector, useAppDispatch } from '../hooks/redux';
import { loginAsync } from '../slices/authSlice';

function LoginForm() {
  const dispatch = useAppDispatch();
  const { status, error } = useAppSelector(state => state.auth);
  
  const handleLogin = async (credentials) => {
    await dispatch(loginAsync(credentials));
  };
}
```

### **Development Guidelines**

#### **Code Style**
- Use TypeScript for all components and utilities
- Follow ESLint and Prettier configurations
- Use functional components with hooks
- Implement proper error boundaries
- Add comprehensive TypeScript types

#### **Component Structure**
```typescript
// Example component structure
import { useState } from 'react';
import { useAppSelector } from '../hooks/redux';

interface ComponentProps {
  title: string;
  onAction?: () => void;
}

export default function Component({ title, onAction }: ComponentProps) {
  const [loading, setLoading] = useState(false);
  const user = useAppSelector(state => state.auth.profile);

  return (
    <div className="p-4">
      <h1 className="text-xl font-bold">{title}</h1>
      {/* Component JSX */}
    </div>
  );
}
```

#### **Styling Guidelines**
- Use Tailwind CSS utility classes
- Implement responsive design with mobile-first approach
- Support both light and dark themes
- Use semantic color classes (primary, secondary, etc.)
- Follow consistent spacing and typography scales

### **Deployment**

The frontend builds to static files that can be served by any web server:

```bash
# Build for production
npm run build

# Files will be in the dist/ directory
# Deploy dist/ contents to your web server
```

### **Next Steps**

The current frontend implementation provides:
- ✅ Complete authentication flow
- ✅ Responsive layout with dark mode
- ✅ Redux state management setup
- ✅ API integration foundation
- ✅ TypeScript configuration
- ✅ Development tooling

**Ready for Extension:**
- Session management interface
- Visual prompt tree editor (D3.js integration)
- Real-time collaboration features
- Advanced prompt editing tools
- File upload and context injection

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For questions, issues, or contributions:
- Open an issue on GitHub
- Contact the development team
- Check the API documentation at `/docs` 