"""
Deployment Manager
Manages deployment of business infrastructure to cloud providers (Railway, Fly.io, Docker).
"""
import os
import json
import time
import uuid
import logging
import subprocess
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)


class DeploymentStatus(Enum):
    PENDING = "pending"
    BUILDING = "building"
    DEPLOYING = "deploying"
    RUNNING = "running"
    STOPPED = "stopped"
    FAILED = "failed"
    SCALING = "scaling"


class DeploymentTarget(Enum):
    RAILWAY = "railway"
    FLY_IO = "flyio"
    DOCKER = "docker"
    LOCAL = "local"


@dataclass
class DeploymentConfig:
    """Configuration for a deployment."""
    target: DeploymentTarget = DeploymentTarget.DOCKER
    service_name: str = ""
    image: str = ""
    region: str = "iad"
    env_vars: Dict[str, str] = None
    cpu: float = 0.25
    memory: int = 512  # MB
    replicas: int = 1
    port: int = 8000
    health_check_path: str = "/health"
    auto_restart: bool = True
    env_file: Optional[str] = None

    def __post_init__(self):
        if self.env_vars is None:
            self.env_vars = {}


@dataclass
class DeploymentResult:
    """Result of a deployment operation."""
    id: str
    status: DeploymentStatus
    target: DeploymentTarget
    url: Optional[str] = None
    logs: List[str] = field(default_factory=list)
    error: Optional[str] = None
    created_at: str = ""
    updated_at: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)


class DeploymentManager:
    """
    Manages deployment of services to various cloud platforms.

    Supports:
    - Railway (via API)
    - Fly.io (via flyctl)
    - Docker (local)
    - Mock/simulation mode for testing
    """

    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self._active_deployments: Dict[str, DeploymentResult] = {}
        self._api_tokens = {
            "railway": os.environ.get("RAILWAY_API_TOKEN", ""),
            "flyio": os.environ.get("FLY_API_TOKEN", ""),
        }

    def create_deployment(self, config: DeploymentConfig) -> DeploymentResult:
        """
        Create a new deployment.

        Args:
            config: Deployment configuration

        Returns:
            DeploymentResult with status and details
        """
        deployment_id = f"deploy-{uuid.uuid4().hex[:12]}"

        try:
            if config.target == DeploymentTarget.RAILWAY:
                result = self._deploy_railway(deployment_id, config)
            elif config.target == DeploymentTarget.FLY_IO:
                result = self._deploy_flyio(deployment_id, config)
            elif config.target == DeploymentTarget.DOCKER:
                result = self._deploy_docker(deployment_id, config)
            else:
                result = self._deploy_local(deployment_id, config)

            self._active_deployments[deployment_id] = result
            return result

        except Exception as e:
            logger.error(f"Deployment failed: {e}")
            return DeploymentResult(
                id=deployment_id,
                status=DeploymentStatus.FAILED,
                target=config.target,
                error=str(e),
                created_at=datetime.utcnow().isoformat(),
                updated_at=datetime.utcnow().isoformat(),
            )

    def get_deployment_status(self, deployment_id: str) -> Optional[DeploymentResult]:
        """Get the status of a deployment."""
        return self._active_deployments.get(deployment_id)

    def stop_deployment(self, deployment_id: str) -> bool:
        """Stop a running deployment."""
        result = self._active_deployments.get(deployment_id)
        if not result:
            return False

        try:
            if result.target == DeploymentTarget.DOCKER:
                self._stop_docker_deployment(deployment_id)
            elif result.target == DeploymentTarget.FLY_IO:
                self._stop_flyio_deployment(result)
            elif result.target == DeploymentTarget.RAILWAY:
                self._stop_railway_deployment(result)

            result.status = DeploymentStatus.STOPPED
            result.updated_at = datetime.utcnow().isoformat()
            return True

        except Exception as e:
            logger.error(f"Failed to stop deployment {deployment_id}: {e}")
            return False

    def scale_deployment(self, deployment_id: str, replicas: int,
                        cpu: float = None, memory: int = None) -> bool:
        """Scale a deployment."""
        result = self._active_deployments.get(deployment_id)
        if not result:
            return False

        try:
            if result.target == DeploymentTarget.FLY_IO:
                self._scale_flyio(result, replicas, cpu, memory)
            elif result.target == DeploymentTarget.DOCKER:
                pass  # Docker single-container, scaling handled by replicas
            elif result.target == DeploymentTarget.RAILWAY:
                self._scale_railway(result, replicas)

            result.metadata["replicas"] = replicas
            if cpu:
                result.metadata["cpu"] = cpu
            if memory:
                result.metadata["memory"] = memory
            result.status = DeploymentStatus.SCALING
            result.updated_at = datetime.utcnow().isoformat()
            return True

        except Exception as e:
            logger.error(f"Failed to scale deployment {deployment_id}: {e}")
            return False

    def get_logs(self, deployment_id: str, lines: int = 100) -> List[str]:
        """Retrieve deployment logs."""
        result = self._active_deployments.get(deployment_id)
        if not result:
            return []

        try:
            if result.target == DeploymentTarget.DOCKER:
                return self._get_docker_logs(deployment_id, lines)
            elif result.target == DeploymentTarget.FLY_IO:
                return self._get_flyio_logs(result, lines)
            elif result.target == DeploymentTarget.RAILWAY:
                return self._get_railway_logs(result, lines)
        except Exception as e:
            logger.error(f"Failed to get logs: {e}")

        return result.logs[-lines:] if result.logs else []

    def list_deployments(self, status: Optional[str] = None) -> List[DeploymentResult]:
        """List all deployments, optionally filtered by status."""
        results = list(self._active_deployments.values())
        if status:
            results = [r for r in results if r.status.value == status]
        return results

    def cleanup(self, max_age_hours: int = 24):
        """Clean up old deployments."""
        cutoff = time.time() - (max_age_hours * 3600)
        to_remove = []

        for deploy_id, result in self._active_deployments.items():
            try:
                created = datetime.fromisoformat(result.created_at).timestamp()
                if created < cutoff and result.status == DeploymentStatus.STOPPED:
                    to_remove.append(deploy_id)
            except (ValueError, TypeError):
                pass

        for deploy_id in to_remove:
            self.stop_deployment(deploy_id)
            del self._active_deployments[deploy_id]

    # ---- Railway Deployment ----

    def _deploy_railway(self, deployment_id: str, config: DeploymentConfig) -> DeploymentResult:
        """Deploy to Railway.app via API."""
        tokens = self._api_tokens.get("railway")
        if not tokens:
            raise ValueError("RAILWAY_API_TOKEN not configured")

        try:
            import requests

            # Create Railway project
            headers = {
                "Authorization": f"Bearer {tokens}",
                "Content-Type": "application/json",
            }

            # Create project
            project_resp = requests.post(
                "https://backboard.railway.app/graphql",
                json={
                    "query": """
                        mutation {
                            projectCreate {
                                id
                                name
                            }
                        }
                    """
                },
                headers=headers,
                timeout=30,
            )

            if project_resp.status_code != 200:
                raise Exception(f"Railway API error: {project_resp.text}")

            project_id = project_resp.json()["data"]["projectCreate"]["id"]

            # Deploy service
            service_payload = {
                "projectId": project_id,
                "serviceName": config.service_name or f"autobiz-{deployment_id[:8]}",
                "imageUrl": config.image,
                "envVars": [
                    {"key": k, "value": v} for k, v in config.env_vars.items()
                ],
                "region": config.region,
            }

            deploy_resp = requests.post(
                f"https://backboard.railway.app/graphql",
                json={
                    "query": """
                        mutation serviceCreate($input: ServiceCreateInput!) {
                            serviceCreate(input: $input) {
                                id
                                name
                                url
                            }
                        }
                    """,
                    "variables": {"input": service_payload},
                },
                headers=headers,
                timeout=120,
            )

            if deploy_resp.status_code != 200:
                raise Exception(f"Railway deploy failed: {deploy_resp.text}")

            deploy_data = deploy_resp.json()["data"]["serviceCreate"]

            return DeploymentResult(
                id=deployment_id,
                status=DeploymentStatus.RUNNING,
                target=DeploymentTarget.RAILWAY,
                url=deploy_data.get("url", f"https://{deploy_data['name']}.up.railway.app"),
                created_at=datetime.utcnow().isoformat(),
                updated_at=datetime.utcnow().isoformat(),
                metadata={
                    "project_id": project_id,
                    "service_id": deploy_data["id"],
                    "region": config.region,
                },
            )

        except ImportError:
            raise ImportError("requests library required for Railway deployment. Install with: pip install requests")

    # ---- Fly.io Deployment ----

    def _deploy_flyio(self, deployment_id: str, config: DeploymentConfig) -> DeploymentResult:
        """Deploy to Fly.io via flyctl."""
        tokens = self._api_tokens.get("flyio")
        if not tokens:
            raise ValueError("FLY_API_TOKEN not configured")

        try:
            # Validate flyctl availability
            result = subprocess.run(
                ["flyctl", "version"],
                capture_output=True, text=True, timeout=10
            )
            if result.returncode != 0:
                raise Exception("flyctl not installed or not accessible")

            app_name = f"autobiz-{deployment_id[:8].lower()}"

            # Create fly.toml
            fly_config = f"""
app = "{app_name}"
primary_region = "{config.region}"

[build]
  dockerfile = "Dockerfile"

[http_service]
  internal_port = {config.port}
  force_https = true
  auto_stop_machines = "stop"
  auto_start_machines = True
  min_machines_running = {config.replicas}

[[vm]]
  size = "shared-cpu-{config.cpu}"
  memory = "{config.memory}mb"
"""

            # Write and deploy
            import tempfile
            with tempfile.TemporaryDirectory() as tmpdir:
                flytoml_path = os.path.join(tmpdir, "fly.toml")
                with open(flytoml_path, "w") as f:
                    f.write(fly_config)

                deploy_result = subprocess.run(
                    ["flyctl", "deploy", "--config", flytoml_path, "--remote-only"],
                    capture_output=True, text=True, timeout=300,
                    env={**os.environ, "FLY_API_TOKEN": tokens}
                )

                if deploy_result.returncode != 0:
                    raise Exception(f"flyctl deploy failed: {deploy_result.stderr}")

                url = f"https://{app_name}.fly.dev"

                return DeploymentResult(
                    id=deployment_id,
                    status=DeploymentStatus.RUNNING,
                    target=DeploymentTarget.FLY_IO,
                    url=url,
                    logs=deploy_result.stdout.split('\n')[-50:],
                    created_at=datetime.utcnow().isoformat(),
                    updated_at=datetime.utcnow().isoformat(),
                    metadata={
                        "app_name": app_name,
                        "region": config.region,
                        "vm_size": f"shared-cpu-{config.cpu}",
                    },
                )

        except FileNotFoundError:
            raise FileNotFoundError("flyctl not found. Install from: https://fly.io/docs/hands-on/install-flyctl/")
        except subprocess.TimeoutExpired:
            logger.error("flyctl deploy timed out")
            return DeploymentResult(
                id=deployment_id,
                status=DeploymentStatus.FAILED,
                target=DeploymentTarget.FLY_IO,
                error="Deployment timed out after 300s",
                created_at=datetime.utcnow().isoformat(),
                updated_at=datetime.utcnow().isoformat(),
            )

    # ---- Docker Deployment ----

    def _deploy_docker(self, deployment_id: str, config: DeploymentConfig) -> DeploymentResult:
        """Deploy using local Docker."""
        try:
            import docker
            client = docker.from_env()
        except ImportError:
            raise ImportError("docker-py not installed. Install with: pip install docker")

        try:
            container_name = f"autobiz-{deployment_id[:8]}"

            # Pull image if needed
            try:
                client.images.get(config.image)
            except docker.errors.ImageNotFound:
                logger.info(f"Pulling Docker image: {config.image}")
                client.images.pull(config.image)

            # Build host config
            host_config = docker.types.HostConfig(
                port_bindings={
                    config.port: ('127.0.0.1', config.port)
                },
                mem_limit=f"{config.memory}m",
                nano_cpus=int(config.cpu * 1e9),
                restart_policy=docker.types.RestartPolicy(
                    condition="always" if config.auto_restart else "no"
                ),
            )

            # Create and start container
            policy = "always" if config.auto_restart else None
            container = client.containers.run(
                config.image,
                name=container_name,
                detach=True,
                ports={config.port: ('127.0.0.1', config.port)},
                environment=config.env_vars or {},
                mem_limit=f"{config.memory}m",
                nano_cpus=int(config.cpu * 1e9),
                restart=policy,
            )

            return DeploymentResult(
                id=deployment_id,
                status=DeploymentStatus.RUNNING,
                target=DeploymentTarget.DOCKER,
                url=f"http://localhost:{config.port}",
                created_at=datetime.utcnow().isoformat(),
                updated_at=datetime.utcnow().isoformat(),
                metadata={
                    "container_id": container.id[:12],
                    "container_name": container_name,
                    "port": config.port,
                },
            )

        except Exception as e:
            logger.error(f"Docker deployment failed: {e}")
            raise

    def _deploy_local(self, deployment_id: str, config: DeploymentConfig) -> DeploymentResult:
        """Run service locally using subprocess."""
        import subprocess
        port = config.port or 8000
        cmd = ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", str(port)]

        proc = subprocess.Popen(
            cmd,
            env={**os.environ, **config.env_vars},
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        return DeploymentResult(
            id=deployment_id,
            status=DeploymentStatus.RUNNING,
            target=DeploymentTarget.LOCAL,
            url=f"http://localhost:{port}",
            created_at=datetime.utcnow().isoformat(),
            updated_at=datetime.utcnow().isoformat(),
            logs=[f"Starting local deployment on port {port}"],
            metadata={"pid": proc.pid, "port": port},
        )

    # ---- Helper methods for non-Docker stop/cleanup ----

    def _stop_docker_deployment(self, deployment_id: str):
        try:
            import docker
            client = docker.from_env()
            result = self._active_deployments.get(deployment_id)
            if result and result.metadata.get("container_name"):
                container = client.containers.get(result.metadata["container_name"])
                container.stop()
                container.remove()
        except Exception:
            logger.warning(f"Could not stop Docker container for {deployment_id}")

    def _stop_flyio_deployment(self, result: DeploymentResult):
        try:
            app_name = result.metadata.get("app_name")
            if app_name:
                subprocess.run(
                    ["flyctl", "apps", "destroy", app_name, "--yes"],
                    capture_output=True, timeout=30,
                )
        except Exception:
            logger.warning(f"Could not stop Fly.io deployment {result.id}")

    def _stop_railway_deployment(self, result: DeploymentResult):
        # Railway project cleanup via API would go here
        logger.info(f"Stopping Railway deployment: {result.id}")

    def _scale_flyio(self, result: DeploymentResult, replicas: int,
                     cpu: float = None, memory: int = None):
        app_name = result.metadata.get("app_name")
        if not app_name:
            return

        cmd = ["flyctl", "scale", "count", str(replicas)]
        if cpu:
            cmd.extend(["--vm-cpu-kind", "shared", "--vm-cpus", str(cpu)])
        if memory:
            cmd.extend(["--vm-memory", f"{memory}mb"])

        subprocess.run(cmd, capture_output=True, timeout=120,
                      env={**os.environ, "FLY_API_TOKEN": self._api_tokens.get("flyio", "")})

    def _scale_railway(self, result: DeploymentResult, replicas: int):
        tokens = self._api_tokens.get("railway")
        if tokens:
            try:
                import requests
                headers = {"Authorization": f"Bearer {tokens}"}
                # Railway scaling API call
                requests.post(
                    f"https://backboard.railway.app/graphql",
                    json={
                        "query": """
                            mutation ($input: ServiceUpdateInput!) {
                                serviceUpdate(input: $input) { id }
                            }
                        """,
                        "variables": {"input": {
                            "id": result.metadata.get("service_id"),
                            "numReplicas": replicas,
                        }}
                    },
                    headers=headers, timeout=30,
                )
            except Exception as e:
                logger.error(f"Railway scaling failed: {e}")

    def _get_docker_logs(self, deployment_id: str, lines: int) -> List[str]:
        try:
            import docker
            client = docker.from_env()
            result = self._active_deployments.get(deployment_id)
            if result:
                container = client.containers.get(result.metadata["container_name"])
                logs = container.logs(tail=lines).decode('utf-8', errors='replace')
                return logs.split('\n')
        except Exception:
            pass
        return []

    def _get_flyio_logs(self, result: DeploymentResult, lines: int) -> List[str]:
        try:
            app_name = result.metadata.get("app_name")
            if app_name:
                proc = subprocess.run(
                    ["flyctl", "logs", "-a", app_name, "--lines", str(lines)],
                    capture_output=True, text=True, timeout=30
                )
                if proc.returncode == 0:
                    return proc.stdout.split('\n')[-lines:]
        except Exception:
            pass
        return []

    def _get_railway_logs(self, result: DeploymentResult, lines: int) -> List[str]:
        # Railway logs via API
        return result.logs[-lines:] if result.logs else []


# Convenience function for quick deployments
def deploy_service(config: Dict[str, Any]) -> DeploymentResult:
    """Quick deployment helper function."""
    manager = DeploymentManager()
    deployment_config = DeploymentConfig(
        target=DeploymentTarget(config.get("target", "docker")),
        service_name=config.get("service_name", ""),
        image=config.get("image", "python:3.11-slim"),
        region=config.get("region", "iad"),
        env_vars=config.get("env_vars", {}),
        cpu=config.get("cpu", 0.25),
        memory=config.get("memory", 512),
        replicas=config.get("replicas", 1),
        port=config.get("port", 8000),
    )
    return manager.create_deployment(deployment_config)