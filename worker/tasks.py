# -*- coding: utf-8 -*-

import os
import time
import threading
from celery import Celery
from prometheus_client import start_http_server

# Start Metrics IMMEDIATELY (Before heavy imports)
def start_metrics():
    try:
        start_http_server(8000)
        print("✅ Global Metrics Server listener active on port 8000")
    except Exception as e:
        print(f"⚠️ Metrics already running or failed: {e}")

# Run in a background thread so it doesn't block the worker startup
threading.Thread(target=start_metrics, daemon=True).start()

# Now do the heavy lifting
try:
    from qiskit_aer import AerSimulator
    from qiskit import QuantumCircuit
    HAS_QISKIT = True
except ImportError:
    HAS_QISKIT = False
    
# Configure Celery to use Redis as the Broker and Result Backend
# In K8s, 'redis-service' will be the internal DNS name for our Redis pod
CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", "redis://redis-service:6379/0")
CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", "redis://redis-service:6379/0")

app = Celery("quantum_tasks", broker=CELERY_BROKER_URL, backend=CELERY_RESULT_BACKEND)

@app.task(name="execute_quantum_circuit", bind=True)
def execute_quantum_circuit(self, num_qubits: int):
    """
    Simulates a GHZ State (Entanglement) circuit.
    This is the 'Heavy Lifting' that runs asynchronously.
    """
    try:
        
        # Fallback for Task ID if running locally/testing
        tid = self.request.id if self.request.id else "test-id"
        
        if not HAS_QISKIT:
            return {"status": "FAILED", "error": "Qiskit/Aer not installed in environment", "task_id": tid}
        
        if num_qubits < 1:
            return {"status": "FAILED", "error": "Qubit count must be at least 1", "task_id": tid}
        
        # 1. Update status for the user to see
        if self.request.id:
            self.update_state(state='PROGRESS', meta={'status': 'Initializing Simulator'})
        
        # 2. Build the Circuit (The Physics Logic)
        qc = QuantumCircuit(num_qubits)
        qc.h(0)
        for i in range(num_qubits - 1):
            qc.cx(i, i + 1)
        qc.measure_all()

        # 3. Simulate execution time (to mimic real QPU latency)
        # As an architect, we add this to test how our queue handles 'busy' workers
        if self.request.id:
            self.update_state(state='PROGRESS', meta={'status': 'Running Simulation...'})
            time.sleep(5) 

        # 4. Run the simulation
        simulator = AerSimulator()
        job = simulator.run(qc, shots=1024)
        result = job.result()
        counts = result.get_counts()

        # 5. Return the final result to the Redis Backend
        return {
            "num_qubits": num_qubits,
            "counts": counts,
            "status": "COMPLETED",
            "engine": "AerSimulator-V1",
            "task_id": tid
        }

    except Exception as e:
        # Handle failures gracefully so the worker doesn't die
        return {"status": "FAILED", "error": str(e), "task_id":tid}