from data.users import USERS_IPS
from data.url_domains import URLS_TO_IPS
from data.edge_endpoints import EDGE_ENDPOINTS

def resolve(requested_url, user_ip):
    dest_ip = URLS_TO_IPS.get(requested_url)
    if not dest_ip:
        raise ValueError(f"URL {requested_url} not found in URLS_TO_IPS mapping.")
    ip_data = USERS_IPS.get(user_ip)
    region = ip_data["region"]
    location_name = ip_data["location_name"]

    nearest_edge_url = EDGE_ENDPOINTS.get(region)
    if nearest_edge_url:
        return nearest_edge_url, location_name, dest_ip
    else:  
        return EDGE_ENDPOINTS["AFRICA-NORTH"], "Default AFRICA-NORTH", dest_ip

if __name__ == "__main__":
    test_ip_us = "173.194.12.1"
    test_ip_africa = "2001:db8::1"
    
    us_url, us_loc, us_dest_ip = resolve("mywebsite.com", test_ip_us)
    print(f"Client IP: {test_ip_us} -> Routed URL: {us_url} (Region: {us_loc}) -> Destination IP: {us_dest_ip}")
    
    af_url, af_loc, af_dest_ip = resolve("mywebsite.com", test_ip_africa)
    print(f"Client IP: {test_ip_africa} -> Routed URL: {af_url} (Region: {af_loc}) -> Destination IP: {af_dest_ip}")