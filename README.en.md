# Distributed Electronic Health Record System

## 🌍 Language / Idioma

- **[Español](README.md)** - Versión en español
- **English** - You are here
- **[📚 Índice de Documentación](INDICE.md)** | **[📚 Documentation Index](INDEX.en.md)**

---

## 🏥 Overview

Complete distributed electronic health record system implementing horizontal data fragmentation over PostgreSQL, with a real-time web monitoring and management interface. The system simulates a distributed database environment using Docker containers and a Python middleware to coordinate distributed queries.

## 🏗️ System Architecture

### Main Components

- **3 PostgreSQL Nodes**: Independent containers with data fragmentation by `documento_id`
- **FastAPI API**: Backend for node management and distributed query execution
- **Web Frontend**: Real-time dashboard for monitoring and control
- **Python Middleware**: Distributed query coordination logic

### Fragmentation Schema

Data is distributed according to `documento_id` ranges:
- **Node 1** (Port 5433): `documento_id < 4,000,000,000`
- **Node 2** (Port 5434): `4,000,000,000 ≤ documento_id < 7,000,000,000`
- **Node 3** (Port 5435): `documento_id ≥ 7,000,000,000`

## 🛠️ Technology Stack

### Backend
- **Python 3.8+**: Primary language
- **FastAPI**: REST API framework
- **PostgreSQL 15**: Database system
- **Psycopg2**: PostgreSQL driver for Python
- **Docker SDK**: Container management
- **Uvicorn**: ASGI server

### Frontend
- **HTML5/CSS3/JavaScript**: Standard web technologies
- **Phosphor Icons**: Icon library
- **CSS Grid/Flexbox**: Responsive design
- **Fetch API**: Asynchronous communication

### Infrastructure
- **Docker**: Containerization
- **Docker Compose**: Service orchestration
- **Docker Volumes**: Data persistence

## 📊 Data Model

### Main Tables

1. **usuario**: Patient demographic information
2. **atencion**: Medical care event records
3. **tecnologia_salud**: Medications and procedures
4. **diagnostico**: Admission and discharge diagnoses
5. **egreso**: Medical discharge information
6. **profesional_salud**: Healthcare personnel data

### Relationships
- `usuario` ← `atencion` ← `tecnologia_salud`
- `atencion` ← `diagnostico`
- `atencion` ← `egreso`
- `profesional_salud` ← `tecnologia_salud`

## 🚀 Setup and Deployment

### Prerequisites
```bash
# Install Docker and Docker Compose
# Verify installation
docker --version
docker-compose --version

# Install Python 3.8+
python3 --version

# Clone repository
git clone https://github.com/jaiderreyes/historia-clinica-distribuida
cd historia-clinica-distribuida
```

### Dependency Installation
```bash
# Create virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate  # Windows

# Install Python dependencies
pip install fastapi uvicorn psycopg2-binary docker pydantic
```

### Infrastructure Deployment
```bash
# Start PostgreSQL nodes
docker-compose up -d

# Verify container status
docker-compose ps

# Load schema on each node
psql -h localhost -p 5433 -U admin -d historia_clinica -f nodo1.sql
psql -h localhost -p 5434 -U admin -d historia_clinica -f nodo2.sql
psql -h localhost -p 5435 -U admin -d historia_clinica -f nodo3.sql
```

### Start Application
```bash
# Start API server
python app.py
# Or with uvicorn directly
uvicorn app:app --host 0.0.0.0 --port 8000 --reload
```

### Application Access
- **Web Dashboard**: http://localhost:8000
- **API Endpoints**: http://localhost:8000/api
- **API Documentation**: http://localhost:8000/docs

## 🔧 Features

### Node Management
- **Real-time monitoring**: Status and availability of each node
- **Container control**: Start/Stop/Restart individual nodes
- **Port visualization**: Port mapping for each node

### Distributed Queries
- **Transparent execution**: SQL queries executed on all nodes
- **Result aggregation**: Automatic result combination
- **Failure handling**: Continues operating with failed nodes
- **Node status**: Availability reporting per query

### Web Interface
- **Responsive dashboard**: Adaptive design for different devices
- **Automatic updates**: Polling every 3 seconds
- **Visual feedback**: Status and progress indicators
- **SQL console**: Query editor with syntax highlighting

## 📁 Project Structure

```
historia-clinica-distribuida/
├── app.py                    # Main FastAPI API
├── middleware.py             # Distributed query logic
├── docker-compose.yml       # Container orchestration
├── requirements.txt          # Python dependencies
├── nodo1.sql                # Schema for node 1
├── nodo2.sql                # Schema for node 2
├── nodo3.sql                # Schema for node 3
├── backend/                 # FHIR backend application
│   └── fhir_app/
│       ├── models/          # FHIR data models
│       ├── services/        # FHIR services
│       └── transformers/    # FHIR transformers
├── templates/
│   ├── index.html          # Main web interface
│   ├── registro-paciente.html  # Patient registration
│   └── consulta-hc.html    # Medical record query
├── static/
│   ├── style.css           # CSS styles
│   └── script.js           # Frontend JavaScript logic
└── README.md               # Project documentation
```

## 🔌 API Endpoints

### Node Management
- `GET /api/nodes` - List status of all nodes
- `POST /api/nodes/{node_id}/{action}` - Node control (start/stop/restart)

### Distributed Queries
- `POST /api/execute-query` - Execute query on all nodes

### Web Interface
- `GET /` - Main dashboard
- `GET /static/*` - Static resources

## 🧪 Usage Examples

### Sample SQL Queries
```sql
-- Basic user query
SELECT documento_id, nombre_completo, edad FROM usuario;

-- Query with JOINs
SELECT u.nombre_completo, a.entidad_salud, a.fecha_ingreso
FROM usuario u 
JOIN atencion a ON u.documento_id = a.documento_id;

-- Diagnosis query
SELECT d.diagnostico_ingreso, d.diagnostico_egreso
FROM diagnostico d
JOIN atencion a ON d.atencion_id = a.atencion_id;
```

### CRUD Operations
```sql
-- Insert user (automatically routed to correct node)
INSERT INTO usuario (documento_id, nombre_completo, edad, sexo)
VALUES (123456789, 'Juan Pérez', 35, 'M');

-- Update data
UPDATE usuario SET edad = 36 WHERE documento_id = 123456789;

-- Delete record
DELETE FROM usuario WHERE documento_id = 123456789;
```

## 🔍 Monitoring and Diagnostics

### Status Verification
```bash
# Container status
docker-compose ps

# Container logs
docker-compose logs pg_nodo1
docker-compose logs pg_nodo2
docker-compose logs pg_nodo3

# Direct node connection
psql -h localhost -p 5433 -U admin -d historia_clinica
psql -h localhost -p 5434 -U admin -d historia_clinica
psql -h localhost -p 5435 -U admin -d historia_clinica
```

### Performance Metrics
- **Query latency**: Distributed response time
- **Availability**: Percentage of operational nodes
- **Data distribution**: Load balance across nodes

## 🛡️ Security Considerations

### Default Configuration
- **Credentials**: admin/admin (development only)
- **Internal network**: Communication between Docker containers
- **CORS**: Allowed from any origin (development only)

### Production Recommendations
- Change default credentials
- Implement SSL/TLS
- Configure firewall and private networks
- Access auditing and logs

## 🔄 Maintenance

### Regular Tasks
```bash
# Clean unused containers and images
docker system prune -a

# Backup volumes
docker run --rm -v pg_data_nodo1:/data -v $(pwd):/backup alpine tar czf /backup/nodo1_backup.tar.gz -C /data .

# Update images
docker-compose pull
docker-compose up -d
```

### Scaling
- **Horizontal**: Add new nodes by modifying `docker-compose.yml`
- **Vertical**: Increase resources for existing containers
- **Rebalancing**: Redistribute data according to new partitions

## 🐛 Troubleshooting

### Docker Compose
If PostgreSQL nodes don't start or the app doesn't connect:

1. **Check Docker and Compose**
   - Docker: `docker --version`
   - Compose v2: `docker compose version` → use `docker compose up -d`
   - Compose v1: `docker-compose --version` → use `docker-compose up -d`

2. **Verification script** (recommended)
   ```bash
   ./verificar-docker.sh
   ```
   Checks Docker, ports 5433–5435, starts containers and optionally tests connection.

3. **Occupied ports**  
   If 5433, 5434 or 5435 are in use, stop the process or change ports in `docker-compose.yml` (and in `middleware.py` if changed).

4. **Status and health**
   ```bash
   docker compose ps   # or docker-compose ps
   ```
   All three nodes should be `Up` and `healthy` (healthcheck with `pg_isready`).

5. **Logs**
   ```bash
   docker compose logs pg_nodo1
   docker compose logs -f pg_nodo2   # follow in real-time
   ```

### Common Issues
1. **Nodes don't start**: Verify port availability 5433-5435; run `./verificar-docker.sh`.
2. **Connection refused**: Confirm containers are running and `healthy`; wait a few seconds after `up -d`.
3. **Query without results**: Verify data exists in correct range; load schema with `nodo1.sql`, `nodo2.sql`, `nodo3.sql`.

### Debugging
```bash
# Verify connectivity
telnet localhost 5433
telnet localhost 5434
telnet localhost 5435

# Test PostgreSQL connection
python -c "import psycopg2; print('Driver OK')"

# Verify application logs
python app.py  # Run in verbose mode
```

## 📈 Future Improvements

### Planned
- [ ] User authentication and authorization
- [ ] Advanced administration interface
- [ ] Performance metrics and charts
- [ ] Automatic backup system
- [ ] Load-based automatic sharding

### Optional
- [ ] Migration to Kubernetes
- [ ] Redis implementation for caching
- [ ] Real-time notification system
- [ ] Alternative GraphQL API

## 📄 License

This project is for educational and demonstration purposes. See specific license for terms of use.

## 👥 Contributions

Contributions are welcome. Please:
1. Fork the repository
2. Create feature branch
3. Submit Pull Request with detailed description

---

**Author**: Distributed Electronic Health Record System  
**Version**: 2.0.0  
**Last update**: 2026-02-17
