import uuid
from database_service import create_session, save_allocation

def test_allocations():
    # Create a test session ID and session
    session_id = str(uuid.uuid4())
    session = create_session(session_id)
    print(f"Created session: {session}")
    
    # Test data for allocations
    allocations = [
        (session_id, 1, 'initial', 50.00, 50.00),
        (session_id, 1, 'final', 60.00, 40.00),
        (session_id, 2, 'initial', 55.00, 45.00)
    ]

    # Insert allocations
    for allocation in allocations:
        result = save_allocation(*allocation)
        print(f"Saved allocation: {result}")

if __name__ == "__main__":
    test_allocations()
