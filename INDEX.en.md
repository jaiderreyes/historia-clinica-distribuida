# 📚 Documentation Index

## 🌍 Language / Idioma

- **English** - You are here
- **[Español](INDICE.md)** - Versión en español

---

## 📖 Main Documentation

### Getting Started
- **[README](README.en.md)** - Complete system overview
- **[FHIR Quick Start](FHIR_QUICKSTART.en.md)** - Quick start guide for FHIR implementation
- **[Docker Configuration](DOCKER.en.md)** - Docker setup and configuration guide

### FHIR Implementation
- **[FHIR MVP](FHIR_MVP.en.md)** - MVP implementation summary
- **[Work Plan](PLAN_TRABAJO_FHIR.md)** - Complete 5-week work plan (Spanish only)
- **[EHR Query Module](MODULO_CONSULTA_HC.md)** - Medical record query module (Spanish only)

### Technical Documentation
- **[57 EHR Fields](57_CAMPOS_HC.md)** - Complete field specification (Spanish only)
- **[Implementation Summary](RESUMEN_IMPLEMENTACION.md)** - Implementation summary (Spanish only)
- **[Troubleshooting](SOLUCION_PROBLEMAS.md)** - Common issues and solutions (Spanish only)
- **[Running Guide](EJECUTANDO.md)** - How to run the system (Spanish only)

---

## 🏗️ System Architecture

### Components
```
┌─────────────────────────────────────────────────────────┐
│                    Web Frontend                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │  Dashboard   │  │   Patient    │  │  EHR Query   │  │
│  │              │  │ Registration │  │              │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
└────────────────────────┬────────────────────────────────┘
                         │
                         ↓
┌─────────────────────────────────────────────────────────┐
│                  FastAPI Backend                        │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │   Node API   │  │  FHIR API    │  │ Distributed  │  │
│  │              │  │              │  │   Queries    │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
└────────────────────────┬────────────────────────────────┘
                         │
          ┌──────────────┼──────────────┐
          │              │              │
          ↓              ↓              ↓
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│ PostgreSQL   │  │ PostgreSQL   │  │ PostgreSQL   │
│   Node 1     │  │   Node 2     │  │   Node 3     │
│  Port 5433   │  │  Port 5434   │  │  Port 5435   │
└──────────────┘  └──────────────┘  └──────────────┘
                         │
                         ↓
                  ┌──────────────┐
                  │  HAPI FHIR   │
                  │   Server     │
                  │  Port 8080   │
                  └──────────────┘
```

---

## 🚀 Quick Start

### 1. Prerequisites
```bash
# Install Docker and Docker Compose
docker --version
docker-compose --version

# Install Python 3.8+
python3 --version
```

### 2. Clone and Setup
```bash
# Clone repository
git clone https://github.com/jaiderreyes/historia-clinica-distribuida
cd historia-clinica-distribuida

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements.txt
```

### 3. Start Services
```bash
# Start all Docker services
docker compose up -d

# Verify services are running
docker compose ps

# Initialize databases
./init-databases.sh
```

### 4. Start Application
```bash
# Start FastAPI application
python app.py

# Access the application
# Dashboard: http://localhost:8001
# Patient Registration: http://localhost:8001/registro-paciente
# API Docs: http://localhost:8001/docs
# HAPI FHIR: http://localhost:8080
```

---

## 📂 Project Structure

```
historia-clinica-distribuida/
├── README.md                    # Main documentation (Spanish)
├── README.en.md                 # Main documentation (English)
├── INDICE.md                    # Documentation index (Spanish)
├── INDEX.en.md                  # Documentation index (English)
│
├── app.py                       # Main FastAPI application
├── middleware.py                # Distributed query middleware
├── requirements.txt             # Python dependencies
├── docker-compose.yml          # Docker orchestration
│
├── backend/                     # Backend application
│   └── fhir_app/               # FHIR implementation
│       ├── models/             # Data models
│       ├── services/           # FHIR services
│       └── transformers/       # FHIR transformers
│
├── templates/                   # HTML templates
│   ├── index.html              # Main dashboard
│   ├── registro-paciente.html  # Patient registration
│   └── consulta-hc.html        # EHR query
│
├── static/                      # Static files
│   ├── style.css               # Styles
│   └── script.js               # Frontend logic
│
├── nodo1.sql                   # Node 1 schema
├── nodo2.sql                   # Node 2 schema
├── nodo3.sql                   # Node 3 schema
│
└── docs/                        # Additional documentation
    ├── DOCKER.en.md            # Docker guide (English)
    ├── FHIR_QUICKSTART.en.md   # FHIR quick start (English)
    └── FHIR_MVP.en.md          # FHIR MVP summary (English)
```

---

## 🔌 API Endpoints

### Node Management
- `GET /api/nodes` - List all nodes status
- `POST /api/nodes/{node_id}/{action}` - Control nodes (start/stop/restart)

### Distributed Queries
- `POST /api/execute-query` - Execute query on all nodes

### FHIR API
- `POST /api/v1/fhir/patient` - Create patient
- `GET /api/v1/fhir/patient/{id}` - Get patient by ID
- `GET /api/v1/fhir/patient/search/{identifier}` - Search by document
- `GET /api/v1/fhir/health` - FHIR server health check

### Web Interface
- `GET /` - Main dashboard
- `GET /registro-paciente` - Patient registration form
- `GET /consulta-hc` - EHR query interface

---

## 🧪 Testing

### Manual Testing
```bash
# Test HAPI FHIR
curl http://localhost:8080/fhir/metadata

# Test API health
curl http://localhost:8001/api/health

# Create test patient
curl -X POST http://localhost:8001/api/v1/fhir/patient \
  -H "Content-Type: application/json" \
  -d @test-patient.json
```

### Automated Testing
```bash
# Run FHIR MVP tests
./test-mvp-fhir.sh

# Verify Docker setup
./verificar-docker.sh
```

---

## 🛠️ Development

### Adding New Features
1. Create feature branch
2. Implement changes
3. Test locally
4. Submit pull request

### Code Style
- Python: Follow PEP 8
- JavaScript: Use ES6+ features
- HTML/CSS: Semantic markup

### Database Migrations
```bash
# Connect to specific node
psql -h localhost -p 5433 -U admin -d historia_clinica

# Run migration
psql -h localhost -p 5433 -U admin -d historia_clinica -f migration.sql
```

---

## 📊 Monitoring

### View Logs
```bash
# Application logs
docker compose logs -f historia_clinica_app

# Database logs
docker compose logs -f pg_nodo1

# HAPI FHIR logs
docker compose logs -f hapi-fhir
```

### Performance Metrics
- Query response time
- Node availability
- Resource utilization

---

## 🐛 Troubleshooting

### Common Issues

1. **Ports already in use**
   - Check ports 5433-5435, 8080, 8001
   - Run: `./verificar-docker.sh`

2. **Containers not starting**
   - Check Docker daemon
   - View logs: `docker compose logs`

3. **Database connection errors**
   - Verify containers are healthy
   - Check network connectivity

See **[Troubleshooting Guide](SOLUCION_PROBLEMAS.md)** for detailed solutions.

---

## 📈 Roadmap

### Version 2.0 (Current)
- ✅ Distributed database system
- ✅ HAPI FHIR integration
- ✅ Patient registration
- ✅ EHR query module

### Version 2.1 (Planned)
- [ ] Advanced search
- [ ] Statistics dashboard
- [ ] Data export (PDF, HL7)
- [ ] User authentication

### Version 3.0 (Future)
- [ ] Complete 57 fields
- [ ] Additional FHIR resources
- [ ] Real-time notifications
- [ ] Mobile application

---

## 👥 Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

---

## 📄 License

This project is for educational and demonstration purposes.

---

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/jaiderreyes/historia-clinica-distribuida/issues)
- **Documentation**: See files above
- **Email**: Contact repository owner

---

**Version**: 2.0.0  
**Last Updated**: 2026-02-17  
**Author**: Distributed Electronic Health Record System
