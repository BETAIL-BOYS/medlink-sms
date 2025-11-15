# MedLink SMS - Healthcare Communication Platform

[![Pipeline Status](https://img.shields.io/badge/pipeline-passing-success)](https://gitlab.com)
[![Docker](https://img.shields.io/badge/docker-ready-blue)](https://www.docker.com/)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)

> Automating healthcare communication across Africa—helping medical professionals deliver lab results instantly and reliably through SMS.

##  Features

-  **User Authentication** - Secure JWT-based login
-  **Patient Management** - Add and manage patient contacts
-  **SMS Delivery** - Automated SMS via Africa's Talking API
-  **Real-time Tracking** - Monitor delivery status
-  **Analytics Dashboard** - Delivery rates and insights
-  **Webhook Support** - Delivery confirmation callbacks

##  Tech Stack

### Backend
- **FastAPI** - Modern Python web framework
- **SQLAlchemy** - SQL ORM
- **SQLite/PostgreSQL** - Database
- **JWT** - Authentication
- **Africa's Talking API** - SMS delivery

### Frontend
- **React 18** - UI library
- **Tailwind CSS** - Styling
- **Axios** - HTTP client
- **Vite** - Build tool

### DevOps
- **Docker** - Containerization
- **GitLab CI/CD** - Automated deployment
- **Render.com** - Hosting

##  Quick Start

### Using Docker (Recommended)
```bash
# Clone repository
git clone https://gitlab.com/YOUR_USERNAME/medlink-sms.git
cd medlink-sms

# Create .env file
cp backend/.env.example backend/.env
# Edit backend/.env with your credentials

# Run with Docker Compose
docker-compose up -d

# Access API
curl http://localhost:8000
# API Docs: http://localhost:8000/docs
```

### Manual Setup

#### Backend
```bash
cd backend
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your credentials
uvicorn main:app --reload
```

#### Frontend
```bash
cd frontend
npm install
npm run dev
```

##  Docker Commands
```bash
# Build images
docker-compose build

# Start services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down

# Rebuild and restart
docker-compose up -d --build
```

##  API Documentation

Once running, visit:
- **Interactive Docs**: http://localhost:8000/docs
- **Alternative Docs**: http://localhost:8000/redoc

### Key Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/register` | Register new user |
| POST | `/login` | User login |
| POST | `/patients` | Add patient |
| GET | `/patients` | Get all patients |
| POST | `/send_sms` | Send SMS |
| GET | `/get_logs` | View message logs |
| GET | `/analytics` | Get statistics |

##  Configuration

### Environment Variables
```bash
SECRET_KEY=your-secret-key-here
AFRICASTALKING_USERNAME=sandbox
AFRICASTALKING_API_KEY=your-api-key-here
DATABASE_URL=sqlite:///./medlink.db
```

Get your Africa's Talking credentials at: https://account.africastalking.com/

##  Deployment

### Automated Deployment (GitLab CI/CD)

Every push to `main` branch:
1.  Runs tests
2.  Builds Docker images
3.  Deploys to production (manual trigger)

### Manual Deployment to Render.com

1. Connect GitLab repository to Render
2. Set environment variables
3. Deploy automatically on push

## Project Structure
```
medlink-sms/
├── backend/
│   ├── main.py              # FastAPI application
│   ├── requirements.txt     # Python dependencies
│   ├── Dockerfile          # Docker configuration
│   ├── .env.example        # Environment template
│   └── data/               # SQLite database
├── frontend/
│   ├── src/                # React source code
│   ├── package.json        # Node dependencies
│   └── Dockerfile          # Docker configuration
├── .gitlab-ci.yml          # CI/CD pipeline
├── docker-compose.yml      # Multi-container setup
└── README.md               # This file
```

##  Testing

### Backend Tests
```bash
cd backend
pytest  # Coming soon
```

### Frontend Tests
```bash
cd frontend
npm test  # Coming soon
```

## Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add AmazingFeature'`)
4. Push to branch (`git push origin feature/AmazingFeature`)
5. Open Merge Request

## License

MIT License - see LICENSE file for details

## Acknowledgments

- [Africa's Talking](https://africastalking.com/) - SMS API
- [FastAPI](https://fastapi.tiangolo.com/) - Web framework
- Healthcare workers across Africa who inspired this project

##  Contact

- **Project Link**: https://gitlab.com/AlAfiz/medlink-sms
- **Live Demo**: https://medlink-sms.onrender.com
- **API Docs**: https://medlink-api.onrender.com/docs

---

**Made with for African Healthcare**
