# test_enrichment.py
import requests
import json
from datetime import datetime

# API base URL
BASE_URL = "http://localhost:8000"

def test_health():
    """Test health endpoint"""
    response = requests.get(f"{BASE_URL}/health")
    print("Health Check:")
    print(json.dumps(response.json(), indent=2))
    print("\n" + "="*50 + "\n")

def test_single_enrichment():
    """Test single message enrichment"""
    
    # Test cases with different types of content
    test_messages = [
        {
            "message_id": "test_001",
            "user_id": "user_123",
            "organization_id": "org_456",
            "content": "Can you help me write a business proposal for our Q4 strategy meeting? I need to present to the board next week.",
            "priority": "high"
        },
        {
            "message_id": "test_002",
            "user_id": "user_123",
            "organization_id": "org_456",
            "content": "What's the weather like today?",
            "priority": "normal"
        },
        {
            "message_id": "test_003",
            "user_id": "user_123",
            "organization_id": "org_456",
            "content": """
            You are a senior data analyst. Given the following sales data:
            Q1: $1.2M, Q2: $1.5M, Q3: $1.3M
            
            Please analyze the trend and provide recommendations for Q4.
            Include:
            1. Trend analysis
            2. Risk factors
            3. Growth opportunities
            """,
            "priority": "high"
        },
        {
            "message_id": "test_004",
            "user_id": "user_123",
            "organization_id": "org_456",
            "content": "My email is john.doe@example.com and my phone is 555-123-4567",
            "priority": "normal"
        }
    ]
    
    for test_msg in test_messages:
        print(f"Testing message {test_msg['message_id']}:")
        print(f"Content: {test_msg['content'][:100]}...")
        
        response = requests.post(
            f"{BASE_URL}/enrichment/enrich",
            json=test_msg
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"Status: {result.get('status')}")
            print(f"Job ID: {result.get('job_id')}")
            
            if result.get('result'):
                print("Enrichment Results:")
                print(json.dumps(result['result'], indent=2))
        else:
            print(f"Error: {response.status_code}")
            print(response.text)
        
        print("\n" + "="*50 + "\n")

def test_batch_enrichment():
    """Test batch message enrichment"""
    
    batch_request = {
        "organization_id": "org_456",
        "messages": [
            {
                "message_id": "batch_001",
                "user_id": "user_123",
                "organization_id": "org_456",
                "content": "Draft an email to the team about the new project timeline"
            },
            {
                "message_id": "batch_002",
                "user_id": "user_123",
                "organization_id": "org_456",
                "content": "What's your favorite color?"
            },
            {
                "message_id": "batch_003",
                "user_id": "user_124",
                "organization_id": "org_456",
                "content": "Analyze the customer churn data from last quarter"
            }
        ],
        "priority": "normal",
        "parallel_processing": True
    }
    
    print("Testing Batch Enrichment:")
    print(f"Sending {len(batch_request['messages'])} messages")
    
    response = requests.post(
        f"{BASE_URL}/enrichment/enrich/batch",
        json=batch_request
    )
    
    if response.status_code == 200:
        result = response.json()
        print(f"Batch ID: {result.get('batch_id')}")
        print(f"Status: {result.get('status')}")
        print(f"Total Messages: {result.get('total_messages')}")
        print(f"Processed: {result.get('processed_messages')}")
        print(f"Successful: {result.get('successful_messages')}")
        print(f"Failed: {result.get('failed_messages')}")
        
        # If processing is complete, show results
        if result.get('results'):
            print("\nResults:")
            for msg_result in result['results']:
                print(f"  - Message {msg_result.get('message_id')}: {msg_result.get('status')}")
    else:
        print(f"Error: {response.status_code}")
        print(response.text)
    
    print("\n" + "="*50 + "\n")

def test_enrichment_with_assistant_response():
    """Test enrichment with assistant response context"""
    
    request = {
        "message_id": "test_005",
        "user_id": "user_123",
        "organization_id": "org_456",
        "content": "Can you help me with this?",
        "assistant_response": "I'd be happy to help! However, I need more specific information about what you're trying to accomplish. Are you looking for help with a technical issue, writing task, analysis, or something else? Please provide more details so I can give you the most relevant assistance.",
        "priority": "high"
    }
    
    print("Testing with Assistant Response:")
    print(f"User: {request['content']}")
    print(f"Assistant: {request['assistant_response'][:100]}...")
    
    response = requests.post(
        f"{BASE_URL}/enrichment/enrich",
        json=request
    )
    
    if response.status_code == 200:
        result = response.json()
        if result.get('result'):
            quality = result['result'].get('quality_analysis', {})
            print(f"Quality Score: {quality.get('overall_score')}")
            print(f"Needs Clarification: {quality.get('needs_clarification')}")
            print(f"Suggestions: {quality.get('improvement_suggestions')}")
    else:
        print(f"Error: {response.status_code}")
        print(response.text)
    
    print("\n" + "="*50 + "\n")

if __name__ == "__main__":
    print("="*50)
    print("TESTING ENRICHMENT SERVICE")
    print("="*50 + "\n")
    
    # Run tests
    test_health()
    test_single_enrichment()
    test_batch_enrichment()
    test_enrichment_with_assistant_response()
    
    print("Testing complete!")