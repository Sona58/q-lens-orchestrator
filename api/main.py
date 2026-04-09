# -*- coding: utf-8 -*-

from prometheus_client import Counter, Histogram, generate_latest
from fastapi import FastAPI, HTTPException, Response
from pydantic import BaseModel
from celery.result import AsyncResult
import os

# Import our Celery app instance
# Note: In production, we'd package this properly, 
# but for K8s simplicity, we point to the worker's task name.
from celery import Celery

CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", "redis://redis-service:6379/0")
CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", "redis://redis-service:6379/0")

# Defining the metrics we want to track
REQUEST_COUNT = Counter("api_requests_total", "Total requests to API", ["method", "endpoint"])
LATENCY = Histogram("api_request_duration_seconds", "Time taken for API requests")

celery_app = Celery("quantum_tasks", broker=CELERY_BROKER_URL, backend=CELERY_RESULT_BACKEND)

app = FastAPI(title="Q-Lens Gateway", root_path="/api/v1")

class JobResponse(BaseModel):
    job_id: str
    status: str

@app.get("/")
def read_root():
    return {"service": "Q-Lens API", "status": "Online"}

@app.get("/metrics")
def metrics():
    # This sends the data in a format Prometheus understands
    return Response(generate_latest(), media_type="text/plain")

@app.post("/run-simulation")
def run_simulation(qubits: int = 2):
    """
    Submits a Quantum task to the background queue.
    """
    REQUEST_COUNT.labels(method="POST", endpoint="/run-simulation").inc()
    with LATENCY.time():
        
        if qubits > 24:
            raise HTTPException(status_code=400, detail="Qubit count too high for standard workers.")
    
        # .delay() sends the task to Redis immediately
        task = celery_app.send_task("execute_quantum_circuit", args=[qubits])
        
        return {"job_id": task.id, "status": "QUEUED"}

@app.get("/results/{job_id}")
def get_results(job_id: str):
    """
    Checks the status or retrieves the result of a specific job.
    """
    res = AsyncResult(job_id, app=celery_app)
    
    if res.state == 'PENDING':
        return {"job_id": job_id, "state": res.state, "status": "Waiting for worker..."}
    
    elif res.state == 'PROGRESS':
        return {"job_id": job_id, "state": res.state, "info": res.info}
    
    elif res.state == 'SUCCESS':
        return {"job_id": job_id, "state": res.state, "result": res.result}
    
    elif res.state == 'FAILURE':
        return {"job_id": job_id, "state": res.state, "error": str(res.info)}
    
    return {"job_id": job_id, "state": res.state}