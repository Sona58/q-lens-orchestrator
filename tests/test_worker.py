# -*- coding: utf-8 -*-

import pytest
from worker.tasks import execute_quantum_circuit

def test_quantum_circuit_logic():
    # Test with 3 qubits
    num_qubits = 3
    result = execute_quantum_circuit.run(num_qubits) # .run() calls it locally, bypassing Celery
    
    # Debug: If it fails, print the error stored in the result
    if result["status"] == "FAILED":
        print(f"Worker Error: {result.get('error')}")
    
    assert result["status"] == "COMPLETED"
    assert result["num_qubits"] == 3
    # A 3-qubit GHZ state should have '000' and '111' as primary outcomes
    assert "000" in result["counts"]
    assert "111" in result["counts"]

def test_invalid_qubit_count():
    # Qiskit will fail with 0 qubits; we check if our error handling works
    result = execute_quantum_circuit.run(0)
    assert result["status"] == "FAILED"
    assert "error" in result