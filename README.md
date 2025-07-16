# idance-backend

A Python backend project using FastAPI.

## Setup

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Run the server

```bash
uvicorn main:app --reload
```

## Health Check

Visit [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health) to check the health endpoint. 