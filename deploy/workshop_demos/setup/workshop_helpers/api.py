"""Authenticated diagnostic API calls retaining stages, cache status and citations."""
import json
import urllib.error
import urllib.request
from .auth import identity_token
from .discovery import read_serving


class ApiClient:
    """Call the deployed lesson API with audience-bound authentication and explicit project configuration.
    
    Example: client = ApiClient(config); response = client.request("/health")
    """
    def __init__(self, config):
        """Resolve the serving API URL and identity-token audience from explicit settings or Cloud Run.
        
        Example: Construct the owning class with the arguments shown above; subsequent methods reuse these settings.
        """
        self.config = config
        self.serving = read_serving(config, config.api_service, config.api_revision)
        self.audience = config.api_audience or self.serving.environment.get("SELF_URL") or self.serving.service_url
        self.url = (config.api_base_url or self.audience).rstrip("/")
        if not self.url.startswith("https://") or not self.audience:
            raise RuntimeError("Could not resolve the API URL and token audience.")

    def request(self, path, body=None, timeout=180):
        """Send authenticated JSON and return decoded evidence; raise with the HTTP error body on failure.
        
        Example: self.request(path, body, timeout) in the owning lesson/helper context
        """
        token = identity_token(self.config, self.audience)
        request = urllib.request.Request(
            self.url + path, method="POST" if body is not None else "GET",
            data=json.dumps(body).encode() if body is not None else None,
            headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        )
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                return json.load(response)
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")[:1500]
            raise RuntimeError(f"API {path}: HTTP {exc.code}: {detail}") from exc
