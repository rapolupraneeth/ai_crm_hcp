#!/usr/bin/env python3
"""
Test script to verify LLM database access functionality
"""
import requests
import time

BASE_URL = "http://localhost:8000"

def test_llm_memory():
    """Test if LLM can access database and remember previous interactions"""

    print("Testing LLM memory with conversation flow...")

    session_id = "test_memory_session_123"

    # First message - introduce an HCP and interaction
    message1 = "I met with Dr. Sarah Johnson, a cardiologist at City General Hospital in New York. We discussed hypertension treatment protocols."

    print(f"Sending message 1: {message1}")
    chat_data1 = {
        "message": message1,
        "session_id": session_id
    }

    response1 = requests.post(f"{BASE_URL}/api/v1/chat", json=chat_data1)
    if response1.status_code == 200:
        data1 = response1.json()
        print("Response 1:")
        print(data1.get("response", ""))
        print()
    else:
        print(f"Failed first message: {response1.text}")
        return

    time.sleep(2)  # Brief pause

    # Second message - reference the previous interaction
    message2 = "Today I met with Dr. Johnson again at 3 PM. We reviewed the patient outcomes from our last discussion about hypertension."

    print(f"Sending message 2: {message2}")
    chat_data2 = {
        "message": message2,
        "session_id": session_id
    }

    response2 = requests.post(f"{BASE_URL}/api/v1/chat", json=chat_data2)
    if response2.status_code == 200:
        data2 = response2.json()
        print("Response 2:")
        print(data2.get("response", ""))

        # Check if the response shows awareness of previous data
        response_text = data2.get("response", "").lower()
        awareness_indicators = [
            "sarah johnson", "dr. johnson", "cardiologist", "hypertension",
            "previous", "last", "earlier", "before", "city general"
        ]

        found_indicators = [indicator for indicator in awareness_indicators if indicator in response_text]
        if found_indicators:
            print(f"✅ LLM appears to be accessing database context! Found indicators: {found_indicators}")
        else:
            print("❌ LLM may not be accessing database context properly - no reference to previous data")

    else:
        print(f"Failed second message: {response2.text}")

if __name__ == "__main__":
    print("Testing LLM database access functionality...")
    test_llm_memory()