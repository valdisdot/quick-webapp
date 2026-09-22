from urllib.parse import urlparse
import socket
import requests
from typing import Optional


def tcp_ping(url, port=443, timeout=5):
    """
    Checks if the server is available for a TCP connection.
    """

    host = urlparse(url).hostname or url
    try:
        socket.create_connection((host, port), timeout=timeout).close()
        return True
    except OSError as e:
        return False

def http_ping(url: str, method: str = "HEAD", timeout: int = 5) -> Optional[int]:
    """
    Checks if the server is available for a HTTP requests.
    """
    
    try:
        response = requests.request(
            method=method,
            url=url,
            allow_redirects=True,
            timeout=timeout,
            verify=False
        )
        return response.status_code
    except requests.RequestException:
        return None
