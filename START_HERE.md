# 🚀 Promptly - Quick Start Guide

## ✅ Prerequisites Installed
- [x] Python 3.11+ virtual environment (`venv`)
- [x] Node.js 18+ and npm
- [x] All Python dependencies from `requirements.txt`
- [x] Frontend dependencies from `package.json`

## 🎯 Project Overview

**Promptly** is an interactive AI prompting platform that helps users craft better AI prompts through:
- **Guided Iteration**: AI asks clarifying questions to refine prompts
- **Visual Decision Trees**: Track conversation history and branching
- **Multi-Model Support**: Target different AI models (GPT, Claude, Gemini, etc.)
- **File Upload**: Context injection from documents
- **User Management**: JWT authentication with OAuth support

## 🏃‍♂️ Quick Start (3 Options)

### Option 1: Using Custom Scripts (Recommended)
```bash
# Terminal 1 - Backend
python run_backend.py

# Terminal 2 - Frontend  
python run_frontend.py
```

### Option 2: Manual Startup
```bash
# Terminal 1 - Backend
cd backend
uvicorn main:app --host 0.0.0.0 --port 8000 --reload

# Terminal 2 - Frontend
cd frontend
npm run dev
```

### Option 3: Docker (if Docker Desktop is running)
```bash
# Start infrastructure services
docker-compose -f infra/docker-compose.yml up -d mongo redis minio

# Then run Option 1 or 2 for the app servers
```

## 🌐 Access Points

| Service | URL | Purpose |
|---------|-----|---------|
| **Frontend** | http://localhost:5173 | React App (Main UI) |
| **Backend API** | http://localhost:8000 | FastAPI Server |
| **API Docs** | http://localhost:8000/docs | Interactive API Documentation |
| **Health Check** | http://localhost:8000/ping | Server Status |

## 🗂️ Project Structure

```
SpurHacks/
├── backend/              # FastAPI Python backend
│   ├── main.py          # FastAPI app entry point
│   ├── api/             # API route handlers
│   ├── auth/            # Authentication & JWT
│   ├── core/            # Database, cache, rate limiting
│   ├── models/          # Pydantic data models
│   ├── services/        # Business logic (AI, storage, Q&A)
│   └── tests/           # Backend tests
├── frontend/            # React TypeScript frontend
│   ├── src/
│   │   ├── components/  # Reusable UI components
│   │   ├── pages/       # Route pages (Home, Login, etc.)
│   │   ├── services/    # API client and calls
│   │   ├── slices/      # Redux state management
│   │   └── hooks/       # Custom React hooks
│   └── public/          # Static assets
├── infra/               # Docker infrastructure
├── requirements.txt     # Python dependencies
├── .env                 # Environment variables
└── venv/               # Python virtual environment
```

## 🔧 Configuration

### Environment Variables (`.env`)
```bash
# Core Settings
ENVIRONMENT=development
DEBUG=true

# Database & Services (if using external)
MONGODB_URL=mongodb://localhost:27017/promptly
REDIS_URL=redis://localhost:6379/0

# Authentication
JWT_SECRET_KEY=development-secret-key

# AI Service (Optional)
GEMINI_API_KEY=your-api-key-here

# CORS
CORS_ORIGINS=http://localhost:5173,http://localhost:3000
```

## 🧪 Testing the Application

1. **Backend Health Check**:
   ```bash
   curl http://localhost:8000/ping
   # Should return: {"ok": true}
   ```

2. **Frontend Access**:
   - Open http://localhost:5173
   - Should see the Promptly landing page

3. **API Documentation**:
   - Open http://localhost:8000/docs
   - Interactive Swagger UI for all endpoints

## 📋 Key Features to Test

### 1. User Authentication
- Sign up at `/signup`
- Login at `/login`
- View profile in protected routes

### 2. Session Management
- Create new AI prompting session
- Answer iterative questions
- View session history

### 3. File Upload (if MinIO running)
- Upload files for context injection
- Link files to sessions

### 4. AI Integration (if Gemini API key set)
- Get AI-generated clarifying questions
- Refine prompts through conversation

## 🛠️ Development Commands

### Backend
```bash
cd backend

# Run with reload
uvicorn main:app --reload

# Run tests
pytest

# Code formatting
ruff format .
ruff check .
```

### Frontend  
```bash
cd frontend

# Development server
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview

# Linting
npm run lint
npm run lint:fix
```

## 🚨 Common Issues & Solutions

### Backend Won't Start
- **Import Errors**: Run `pip install -r requirements.txt`
- **Port 8000 in use**: Kill process or change port in startup command
- **Database connection**: Backend will run without MongoDB/Redis (some features disabled)

### Frontend Won't Start
- **Node modules missing**: Run `npm install` in frontend directory
- **Port 5173 in use**: Vite will automatically try next available port
- **Build errors**: Check TypeScript errors with `npm run type-check`

### Docker Issues
- **Docker not running**: Start Docker Desktop first
- **Port conflicts**: Ensure ports 27017 (MongoDB), 6379 (Redis), 9000 (MinIO) are free

## 🎮 Next Steps

1. **Basic Testing**: Verify both servers start and are accessible
2. **Create Account**: Sign up and test authentication
3. **Create Session**: Test the core prompting workflow
4. **Add AI Key**: Set `GEMINI_API_KEY` for full AI features
5. **Upload Files**: Test file upload functionality
6. **Explore API**: Use the interactive docs at `/docs`

## 📞 Need Help?

- Check server logs in the terminal for error messages
- API documentation: http://localhost:8000/docs
- Frontend console (F12) for React errors
- Both servers support hot reload for development

---

**Status**: ✅ Ready to run locally with development features! 