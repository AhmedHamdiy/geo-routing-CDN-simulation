import requests
import time
import sys

GEO_MAPPING = {
    "US-Client (Near Edge 1)": "http://localhost:8081",
    "EU-Client (Near Edge 2)": "http://localhost:8082"
}

CDN_HOST = "mycdn.com"
TEST_URL_PATH = "/" 
FULL_URL = f"{GEO_MAPPING['US-Client (Near Edge 1)']}{TEST_URL_PATH}" 


def get_cdn_response(edge_url, location_name):
    """Makes a request to a specific Edge node and returns key headers/data."""
    print(f"\n--- Simulating Request from: {location_name} ({edge_url}) ---")
    
    headers = {'Host': CDN_HOST}
    
    try:
        start_time = time.time()
        response = requests.get(edge_url + TEST_URL_PATH, headers=headers)
        end_time = time.time()
        
        latency_ms = (end_time - start_time) * 1000

        cache_status = response.headers.get('X-Cache-Status', 'N/A')
        edge_server = response.headers.get('X-Edge-Server', 'N/A')
        
        print(f"  > Status Code: {response.status_code}")
        print(f"  > X-Edge-Server: {edge_server}")
        print(f"  > X-Cache-Status: {cache_status}")
        print(f"  > Latency: {latency_ms:.2f} ms")
        
        return cache_status, latency_ms
        
    except requests.exceptions.RequestException as e:
        print(f"  > ERROR: Failed to connect to {edge_url}. Ensure the container is running and port is exposed.")
        print(f"  > Exception: {e}")
        sys.exit(1)


def simulate_geo_routing():
    print("Starting CDN Simulation Test...")

    print("\n\n#####################################################")
    print("## 1. Testing US-EAST Region (Edge 1 - Low Latency) ##")
    print("#####################################################")

    us_url = GEO_MAPPING["US-Client (Near Edge 1)"]
    us_name = "US-Client (Near Edge 1)"

    print("\n--- US Test 1: Cold Cache (Expected MISS) ---")
    get_cdn_response(us_url, us_name)
    
    print("\n--- US Test 2: Warm Cache (Expected HIT) ---")
    get_cdn_response(us_url, us_name)


    print("\n\n####################################################")
    print("## 2. Testing EU-WEST Region (Edge 2 - High Latency) ##")
    print("####################################################")

    eu_url = GEO_MAPPING["EU-Client (Near Edge 2)"]
    eu_name = "EU-Client (Near Edge 2)"

    print("\n--- EU Test 1: Cold Cache (Expected MISS, SLOW) ---")
    miss_status, miss_latency = get_cdn_response(eu_url, eu_name)
    
    print("\n--- EU Test 2: Warm Cache (Expected HIT, FAST) ---")
    hit_status, hit_latency = get_cdn_response(eu_url, eu_name)

    print("\n\n#####################################################")
    print("## 3. Latency Verification (EU Edge) ##")
    print("#####################################################")
    if (miss_status == 'MISS' or miss_status == 'EXPIRED') and hit_status == 'HIT':
        print(f"Successfully verified caching on EU Edge:")
        print(f"  > MISS Latency (connecting to Origin): {miss_latency:.2f} ms")
        print(f"  > HIT Latency (served from Cache): {hit_latency:.2f} ms")
        print(f"  > Latency Improvement: {miss_latency - hit_latency:.2f} ms")
        print("\nGeoDNS/Caching simulation SUCCESSFUL: Cached content served faster than fetching from Origin.")
    else:
         print("\nLatency Verification FAILED: Cache statuses were not MISS then HIT. Check NGINX logs.")
         
if __name__ == "__main__":
    simulate_geo_routing()