import requests
from typing import Generator
from .config import get_api_key
from .models import PodResponse


class RunPodClient:
    def __init__(self, api_key: str | None = None) -> None:
        self.api_key = api_key or get_api_key()
        if not self.api_key:
            raise ValueError(
                "RunPod API key not found. Either:\n"
                "1. Set RUNPOD_API_KEY environment variable\n"
                "2. Run 'runpod-ssh configure' to set API key\n"
                "3. Pass API key directly using --api-key option"
            )

        self.url = f"https://api.runpod.io/graphql?api_key={self.api_key}"
        self.headers = {"Content-Type": "application/json"}

    def get_all_running_pods(
        self,
    ) -> Generator[tuple[str, tuple[str | None, int | None]], None, None]:
        query = """query Pods { myself { pods { name runtime { ports { ip isIpPublic publicPort } } } } }"""

        response = requests.post(self.url, json={"query": query}, headers=self.headers)
        response.raise_for_status()
        data = PodResponse.model_validate(response.json()["data"])

        for pod in data.myself["pods"]:
            if pod.runtime is None:
                continue

            ip = port = None
            for p in pod.runtime.ports:
                if p.is_ip_public:
                    ip, port = p.ip, p.public_port
                    break

            yield (pod.name, (ip, port))
