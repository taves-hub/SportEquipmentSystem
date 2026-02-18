from app import app

# Test if we can access storekeeper dashboard
with app.test_client() as client:
    # First try to login as a storekeeper
    test_payroll = '100206'  # Gladys Mitei - approved
    response = client.post('/login', data={'username': test_payroll, 'password': 'Password123'}, follow_redirects=True)
    print(f'Login response status: {response.status_code}')
    print(f'Final URL after login: {response.request.url}')
    response_text = response.get_data(as_text=True)
    print(f'Response contains dashboard: {"dashboard" in response_text}')
    print(f'Response contains storekeeper: {"storekeeper" in response_text}')
    print(f'Response contains login: {"login" in response_text}')

    # Check if we got redirected to storekeeper dashboard
    if '/storekeeper/dashboard' in str(response.request.url):
        print("SUCCESS: Storekeeper login worked!")
    else:
        print("ISSUE: Storekeeper login did not redirect to dashboard")
        print(f"Response text preview: {response_text[:500]}...")