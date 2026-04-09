# -*- coding: utf-8 -*-

import asyncio
import httpx
import random
import time

# Configuration
API_URL = "http://localhost:8000/run-simulation"
CONCURRENT_USERS = 5  # Number of simultaneous requests
TOTAL_REQUESTS = 50   # Total jobs to submit

async def submit_job(client, user_id):
    """Submits a random quantum simulation job."""
    qubits = random.randint(2, 24)  # Vary the intensity
    try:
        start_time = time.perf_counter()
        response = await client.post(f"{API_URL}?qubits={qubits}", timeout=20.0)
        end_time = time.perf_counter()
        
        if response.status_code == 200:
            print(f"[User {user_id}] Success: {qubits} qubits submitted ({end_time - start_time:.2f}s)")
        else:
            print(f"[User {user_id}] Failed: {response.text}")
    except Exception as e:
        print(f"[User {user_id}] Connection Error: {e}")

async def main():
    async with httpx.AsyncClient() as client:
        tasks = []
        print(f"🚀 Starting Stress Test: {TOTAL_REQUESTS} jobs across {CONCURRENT_USERS} users...")
        
        for i in range(TOTAL_REQUESTS):
            tasks.append(submit_job(client, i % CONCURRENT_USERS))
            
            # Control the rate of fire so we don't overwhelm the local CPU immediately
            if len(tasks) >= CONCURRENT_USERS:
                await asyncio.gather(*tasks)
                tasks = []
                await asyncio.sleep(0.5) # Small pause between batches

if __name__ == "__main__":
    asyncio.run(main())