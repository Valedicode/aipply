"""
API Test Script

Simple script to test the JobWriterAI API endpoints.
Run this after starting the FastAPI server.
"""

import requests
import json
from pathlib import Path

# Configuration
BASE_URL = "http://localhost:8000"
TEST_CV_PATH = str(Path(__file__).parent.parent / "data" / "CV.pdf")  # Adjust as needed


def print_section(title):
    """Print a formatted section header."""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def test_health_check():
    """Test basic health check."""
    print_section("Health Check")
    
    response = requests.get(f"{BASE_URL}/health")
    print(f"Status Code: {response.status_code}")
    print(json.dumps(response.json(), indent=2))
    
    return response.status_code == 200


def test_cv_extraction():
    """Test CV extraction endpoint."""
    print_section("CV Extraction Test")
    
    # Check if test CV exists
    if not Path(TEST_CV_PATH).exists():
        print(f"⚠️  Test CV not found at: {TEST_CV_PATH}")
        print("Please update TEST_CV_PATH in this script or create a test CV.")
        return None
    
    print(f"Extracting CV from: {TEST_CV_PATH}")
    
    response = requests.post(
        f"{BASE_URL}/api/cv/extract",
        json={"pdf_path": TEST_CV_PATH}
    )
    
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"Success: {data['success']}")
        print(f"Needs Clarification: {data['needs_clarification']}")
        
        if data['cv_data']:
            print("\nCV Data:")
            print(f"  Name: {data['cv_data']['name']}")
            print(f"  Email: {data['cv_data']['email']}")
            print(f"  Skills: {len(data['cv_data']['skills'])} skills")
            
        if data['questions']:
            print("\nClarification Questions:")
            for q in data['questions']:
                print(f"  - {q}")
        
        return data['cv_data']
    else:
        print(f"Error: {response.json()}")
        return None


def test_job_extraction_text():
    """Test job extraction from text."""
    print_section("Job Extraction from Text Test")
    
    sample_job_text = """
    Senior Software Engineer
    
    We are looking for an experienced Senior Software Engineer to join our team.
    
    Requirements:
    - 5+ years of software development experience
    - Strong proficiency in Python and JavaScript
    - Experience with React and FastAPI
    - Knowledge of cloud platforms (AWS, Azure)
    - Bachelor's degree in Computer Science or related field
    
    Responsibilities:
    - Design and develop scalable web applications
    - Lead technical discussions and code reviews
    - Mentor junior developers
    - Collaborate with product team
    
    Location: Remote
    Type: Full-time
    """
    
    print("Extracting job from sample text...")
    
    response = requests.post(
        f"{BASE_URL}/api/job/extract/text",
        json={"job_text": sample_job_text}
    )
    
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"Success: {data['success']}")
        
        if data['job_data']:
            print("\nJob Data:")
            print(f"  Title: {data['job_data']['job_title']}")
            print(f"  Level: {data['job_data']['job_level']}")
            print(f"  Required Skills: {', '.join(data['job_data']['required_skills'][:5])}")
            print(f"  Location: {data['job_data']['location']}")
        
        return data['job_data']
    else:
        print(f"Error: {response.json()}")
        return None


def test_alignment_analysis(cv_data, job_data):
    """Test CV-job alignment analysis."""
    print_section("CV-Job Alignment Analysis Test")
    
    if not cv_data or not job_data:
        print("⚠️  Missing CV or Job data. Skipping alignment test.")
        return None
    
    print("Analyzing CV-job alignment...")
    
    response = requests.post(
        f"{BASE_URL}/api/writer/analyze-alignment",
        json={
            "cv_data": cv_data,
            "job_data": job_data
        }
    )
    
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"Success: {data['success']}")
        
        if data['tailoring_plan']:
            plan = data['tailoring_plan']
            print("\nTailoring Plan:")
            print(f"  Matching Skills: {len(plan['matching_skills'])}")
            print(f"  Matching Experiences: {len(plan['matching_experiences'])}")
            print(f"  Keywords to Incorporate: {len(plan['keywords_to_incorporate'])}")
            print(f"\n  Reasoning: {plan['reasoning'][:200]}...")
        
        return data['tailoring_plan']
    else:
        print(f"Error: {response.json()}")
        return None


def test_supervisor_session():
    """Test supervisor conversational workflow."""
    print_section("Supervisor Session Test")
    
    # Start session
    print("Starting supervisor session...")
    start_response = requests.post(f"{BASE_URL}/api/supervisor/session/start")
    
    if start_response.status_code != 200:
        print(f"Failed to start session: {start_response.json()}")
        return
    
    session_data = start_response.json()
    session_id = session_data['session_id']
    print(f"Session ID: {session_id}")
    print(f"\nWelcome Message:\n{session_data['welcome_message']}")
    
    # Test message exchange
    print("\n--- Testing Message Exchange ---")
    
    test_message = "Can you help me understand how this works?"
    print(f"\nUser: {test_message}")
    
    message_response = requests.post(
        f"{BASE_URL}/api/supervisor/session/message",
        json={
            "session_id": session_id,
            "user_input": test_message
        }
    )
    
    if message_response.status_code == 200:
        message_data = message_response.json()
        print(f"\nAssistant: {message_data['assistant_message']}")
        
        if message_data['session_state']:
            state = message_data['session_state']
            print(f"\nSession State:")
            print(f"  Stage: {state['session_stage']}")
            print(f"  Has CV: {state['has_cv_data']}")
            print(f"  Has Job: {state['has_job_data']}")
            print(f"  Ready for Writer: {state['ready_for_writer']}")
    else:
        print(f"Error: {message_response.json()}")
    
    # Get session state
    print("\n--- Getting Session State ---")
    state_response = requests.get(f"{BASE_URL}/api/supervisor/session/{session_id}/state")
    
    if state_response.status_code == 200:
        print(json.dumps(state_response.json(), indent=2))
    
    # Cleanup
    print("\n--- Cleaning Up Session ---")
    delete_response = requests.delete(f"{BASE_URL}/api/supervisor/session/{session_id}")
    print(f"Session deleted: {delete_response.json()['success']}")


def test_writer_health():
    """Test writer agent health check."""
    print_section("Writer Agent Health Check")
    
    response = requests.get(f"{BASE_URL}/api/writer/health")
    print(f"Status Code: {response.status_code}")
    print(json.dumps(response.json(), indent=2))


def main():
    """Run all API tests."""
    print("\n" + "=" * 70)
    print("  JobWriterAI API Test Suite")
    print("=" * 70)
    print(f"\nTesting API at: {BASE_URL}")
    print("Make sure the FastAPI server is running!")
    
    try:
        # Test 1: Health Check
        if not test_health_check():
            print("\n❌ Health check failed. Is the server running?")
            return
        
        # Test 2: CV Extraction
        cv_data = test_cv_extraction()
        
        # Test 3: Job Extraction
        job_data = test_job_extraction_text()
        
        # Test 4: Alignment Analysis
        if cv_data and job_data:
            tailoring_plan = test_alignment_analysis(cv_data, job_data)
        
        # Test 5: Writer Health
        test_writer_health()
        
        # Test 6: Supervisor Session
        test_supervisor_session()
        
        print("\n" + "=" * 70)
        print("  ✅ All Tests Completed!")
        print("=" * 70)
        print("\nNote: Some tests may show warnings if test data is not available.")
        print("Check the API documentation for full endpoint details: http://localhost:8000/docs")
        
    except requests.exceptions.ConnectionError:
        print("\n❌ Connection Error: Could not connect to the API server.")
        print("Make sure the server is running at http://localhost:8000")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()


