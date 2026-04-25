# RAG System Setup Guide (Django + Streamlit)

This project is a Retrieval-Augmented Generation (RAG) system with a Django backend, a Streamlit frontend, and a PostgreSQL database (with `pgvector` extension). The system uses a local LLM via Ollama.

## 1. Prerequisites

Before getting started, make sure you have the following installed on your machine:

* **Docker & Docker Compose:** To build and run the services (Backend, Frontend, Database).
* **Ollama:** To run the local LLM.

## 2. Install Ollama & Download the Model

Since the project is configured to connect to the LLM via `http://host.docker.internal:11434`, you need to install and run Ollama directly on your Host Machine, **not** inside a Docker container.

1. Download and install Ollama from the official website: [https://ollama.com/](https://ollama.com/)
2. Open your Terminal (or Command Prompt/PowerShell) and run the following command to download and run the Qwen2.5 model (choose the 3B or 7B version depending on your machine's RAM/VRAM):

**For the 3B version (lighter, recommended for machines with less RAM):**
```bash
ollama run qwen2.5:3b
```

**For the 7B version (smarter, requires better hardware):**
```bash
ollama run qwen2.5:7b
```
*(Note: Ensure the Ollama application is running in the background while using the system).*

## 3. Build and Start the Project

Open a new Terminal, navigate to the root directory of the project (where the `docker-compose.yml` file is located), and run the following command to build and start all containers:

```bash
docker-compose up -d --build
```
*(The `-d` flag runs the containers in the background, and `--build` ensures the latest Docker images are built).*

## 4. Database Migration

Once the containers are running successfully (especially the database and backend), you need to create the necessary tables in PostgreSQL. 

Run these two commands in your terminal to apply the migrations inside the backend container:

**Create migration files (if there are changes in your models):**
```bash
docker exec -it django_backend python manage.py makemigrations
```

**Apply migrations to the database:**
```bash
docker exec -it django_backend python manage.py migrate
```

## 5. Access the Application

After completing the setup, you can access the system via your web browser:

* **Frontend (Streamlit UI):** http://localhost:8501
* **Backend API / Admin (Django):** http://localhost:8000
* **Database (PostgreSQL):** `localhost:5433` (Username: `postgres` | Password: `123`)

---

### Useful Docker Commands
* **View Backend logs:** `docker logs -f django_backend`
* **View Frontend logs:** `docker logs -f streamlit_frontend`
* **Stop and remove all containers:** `docker-compose down`

> **Note:** In the `docker-compose.yml` file, the `frontend` service uses a volume mount (`./frontend:/app`). This allows for hot-reloading; any changes you make to the Streamlit code on your host machine will automatically reflect in the app without needing to rebuild the Docker container.
