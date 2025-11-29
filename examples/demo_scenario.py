"""
RCD² End-to-End Demo Scenario
=============================

This script simulates a complete lifecycle of the RCD² platform:
1. Checks system health
2. Makes initial predictions (stable data)
3. Injects drifting data (concept drift)
4. Monitors drift detection
5. Triggers auto-retraining
6. Verifies model promotion

Usage:
    python examples/demo_scenario.py
"""

import time
import requests
import random
import sys
import json
from typing import Dict, Any, List

import os

# Configuration
API_URL = "http://localhost:8000"
API_KEY = os.getenv("RCD2_API_KEY", "dev-key-123")  # Default dev key
HEADERS = {
    "Content-Type": "application/json",
    "X-API-Key": API_KEY
}

def print_step(step: str):
    print(f"\n{'='*60}")
    print(f"🚀 {step}")
    print(f"{'='*60}")

def check_health():
    """Check if API is running."""
    try:
        resp = requests.get(f"{API_URL}/health", headers=HEADERS)
        if resp.status_code == 200:
            print("✅ System is HEALTHY")
            return True
    except requests.exceptions.ConnectionError:
        print("❌ System is OFFLINE. Please start the server first.")
        return False
    return False

def make_prediction(features: List[float]) -> Dict[str, Any]:
    """Make a single prediction."""
    resp = requests.post(
        f"{API_URL}/api/predict",
        json={"features": features},
        headers=HEADERS
    )
    return resp.json()

def ingest_data(features: List[float], label: int):
    """Ingest a data point."""
    requests.post(
        f"{API_URL}/api/ingest",
        json={"features": features, "label": label},
        headers=HEADERS
    )

def get_drift_status() -> Dict[str, Any]:
    """Get current drift status."""
    resp = requests.get(f"{API_URL}/api/drift", headers=HEADERS)
    return resp.json()

def run_scenario():
    if not check_health():
        sys.exit(1)

    # 1. Baseline Phase (Stable Data)
    print_step("PHASE 1: Baseline Operation (Stable Data)")
    print("Ingesting 50 stable samples...")
    
    for i in range(50):
        # Generate data from distribution N(0, 1)
        features = [random.gauss(0, 1) for _ in range(3)]
        # Label logic: simple linear boundary
        label = 1 if sum(features) > 0 else 0
        
        ingest_data(features, label)
        
        if i % 10 == 0:
            pred = make_prediction(features)
            print(f"Sample {i}: Pred={pred['prediction']}, Conf={pred['probability']}")
            
    drift = get_drift_status()
    print(f"\nStatus: Drift Score={drift['drift_score']:.2f}, Severity={drift['severity']}")

    # 2. Drift Injection Phase
    print_step("PHASE 2: Injecting Concept Drift")
    print("Simulating sudden shift in data distribution (Mean 0 -> 3)...")
    
    drift_detected = False
    
    for i in range(100):
        # Generate data from shifted distribution N(3, 1)
        features = [random.gauss(3, 1) for _ in range(3)]
        label = 1 if sum(features) > 0 else 0  # Logic stays same, but input shifts
        
        ingest_data(features, label)
        
        if i % 10 == 0:
            drift = get_drift_status()
            print(f"Sample {i}: Drift Score={drift['drift_score']:.2f} ({drift['severity']})")
            
            if drift['severity'] == 'high':
                print("\n🚨 HIGH DRIFT DETECTED! Auto-retraining should trigger soon.")
                drift_detected = True
                break
        
        time.sleep(0.05)  # Slight delay for realism

    if not drift_detected:
        print("\n⚠️ Drift not automatically detected in this batch. Forcing trigger...")
        requests.post(
            f"{API_URL}/api/force_retrain",
            json={"drift_score": 85.0, "reason": "demo_forced_trigger"},
            headers=HEADERS
        )

    # 3. Retraining & Recovery
    print_step("PHASE 3: Recovery & Verification")
    print("Waiting for retraining to complete...")
    time.sleep(5)  # Wait for background task
    
    # Check latest model
    resp = requests.get(f"{API_URL}/api/model/champion", headers=HEADERS)
    champion = resp.json()
    
    print(f"👑 Current Champion Model: {champion['version']}")
    print(f"📊 Accuracy: {champion['accuracy']:.2%}")
    print(f"📅 Created: {champion['created_at']}")
    
    print("\n✅ Demo Scenario Complete!")

if __name__ == "__main__":
    run_scenario()
