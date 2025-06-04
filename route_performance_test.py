"""
Complete route performance testing to verify optimization success
"""
import requests
import time
from concurrent.futures import ThreadPoolExecutor

def test_route_performance():
    """Test performance of key application routes"""
    base_url = "http://localhost:5000"
    
    routes_to_test = [
        "/",
        "/health",
        "/healthz",
        "/manager/clients",
        "/manager/clients/analytics",
        "/register"
    ]
    
    print("Testing route performance...")
    print("-" * 50)
    
    for route in routes_to_test:
        start_time = time.time()
        try:
            response = requests.get(f"{base_url}{route}", timeout=10)
            end_time = time.time()
            duration = end_time - start_time
            
            print(f"{route:<30} {response.status_code:<4} {duration:.3f}s")
            
            if duration > 5.0:
                print(f"  WARNING: Route taking >5s")
            elif duration > 2.0:
                print(f"  CAUTION: Route taking >2s")
                
        except requests.exceptions.Timeout:
            print(f"{route:<30} TIMEOUT >10s")
        except Exception as e:
            print(f"{route:<30} ERROR {str(e)[:30]}")
    
    print("-" * 50)
    print("Performance test completed")

def test_concurrent_requests():
    """Test how the application handles concurrent requests"""
    base_url = "http://localhost:5000"
    
    def make_request():
        start = time.time()
        try:
            response = requests.get(f"{base_url}/health", timeout=5)
            return time.time() - start, response.status_code
        except:
            return None, None
    
    print("\nTesting concurrent request handling...")
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(make_request) for _ in range(10)]
        results = [f.result() for f in futures]
    
    successful_requests = [(duration, status) for duration, status in results if duration is not None]
    
    if successful_requests:
        avg_duration = sum(r[0] for r in successful_requests) / len(successful_requests)
        print(f"Concurrent requests: {len(successful_requests)}/10 successful")
        print(f"Average response time: {avg_duration:.3f}s")
    else:
        print("No successful concurrent requests")

if __name__ == "__main__":
    test_route_performance()
    test_concurrent_requests()