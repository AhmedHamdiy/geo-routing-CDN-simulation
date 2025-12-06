import geoDNS_resolver
import data.users  as users
import requests
import time
import sys


def get_cdn_response(edge_address, location_name):
    print(f"\n--- Simulating Request from: {location_name} ({edge_address}) ---")    
    
    try:
        start_time = time.time()
        response = requests.get(edge_address)
        end_time = time.time()
        
        latency_ms = (end_time - start_time) * 1000

        cache_status = response.headers.get('X-Cache-Status', 'N/A')
        edge_server = response.headers.get('X-Edge-Server', 'origin')
        
        print(f"  > Status Code: {response.status_code}")
        print(f"  > X-Edge-Server: {edge_server}")
        print(f"  > X-Cache-Status: {cache_status}")
        print(f"  > Latency: {latency_ms:.2f} ms")
        
        return cache_status, latency_ms
        
    except requests.exceptions.RequestException as e:
        print(f"  > ERROR: Failed to connect to {edge_address}. Ensure the container is running and port is exposed.")
        print(f"  > Exception: {e}")
        sys.exit(1)


def simulate_geo_routing():    
    users_data= users.USERS_IPS
    for client_ip, ip_info in users_data.items():
        region = ip_info["region"]
    
        nearest_edge_url, location_name, dest_ip = geoDNS_resolver.resolve("mywebsite.com", client_ip)
        
        print(f"\n========================================================")
        print(f"## Testing Client IP: {client_ip} -> Routed to: {region} ##")
        print(f"========================================================")

        print("\n--- Request 1: Cold Cache/Revalidation ---")
        req1_status, req1_latency = get_cdn_response(nearest_edge_url, location_name)
        
        print("\n--- Request 2: Warm Cache (Expected HIT) ---")
        req2_status, req2_latency = get_cdn_response(nearest_edge_url, location_name)
        
        if req1_status == "MISS" and req2_status == "HIT":
            print("\n[Verification Summary]")
            print(f"  > Cache Test: {req1_status} -> {req2_status} (SUCCESS)")        
            print(f"  > MISS Latency (connecting to Origin): {req1_latency:.2f} ms")
            print(f"  > HIT Latency (served from Cache): {req2_latency:.2f} ms")
            print(f"  > Latency Improvement: {(req1_latency - req2_latency):.2f} ms (Proves Caching Benefit)")

        
if __name__ == "__main__":
    simulate_geo_routing()