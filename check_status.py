import requests

try:
    response = requests.get('http://localhost:5000/dashboard')
    print(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        print("Dashboard page loaded successfully!")
    else:
        print("Dashboard page returned an error.")
except Exception as e:
    print(f"Error: {str(e)}") 