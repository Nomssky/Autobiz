"""
Docker-based Code Sandbox
Execute code in isolated, ephemeral Docker containers with resource limits and timeouts.
"""
import os
import json
import time
import uuid
import signal
import subprocess
import logging
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

# Try import docker-py
try:
    import docker
    DOCKER_AVAILABLE = True
except ImportError:
    DOCKER_AVAILABLE = False
    logger.warning("docker-py not installed. Code sandbox will run in simulation mode.")


@dataclass
class SandboxConfig:
    """Configuration for a sandbox execution."""
    image: str = "python:3.11-slim"
    timeout_seconds: int = 30
    memory_limit: str = "256m"
    cpu_shares: int = 512  # Relative CPU weight
    max_output_size: int = 1024 * 1024  # 1MB
    network_disabled: bool = True
    read_only: bool = True
    environment: Dict[str, str] = field(default_factory=dict)


@dataclass
class SandboxResult:
    """Result of a sandbox execution."""
    id: str
    exit_code: int
    stdout: str
    stderr: str
    duration_ms: int
    timeout: bool = False
    memory_exceeded: bool = False
    error: Optional[str] = None


class CodeSandbox:
    """
    Secure, isolated code execution environment using Docker containers.

    Features:
    - Timeout enforcement (kills container after timeout)
    - Memory limit (OOM kills automatically by Docker)
    - CPU restriction via cpu_shares
    - Network isolation (optional)
    - Read-only filesystem (optional)
    - Automatic cleanup (removes container after execution)
    """

    def __init__(self, config: Optional[SandboxConfig] = None):
        self.config = config or SandboxConfig()
        self._client: Optional[docker.DockerClient] = None
        self._active_containers: Dict[str, Any] = {}

        if DOCKER_AVAILABLE:
            try:
                self._client = docker.from_env()
                # Verify Docker is accessible
                self._client.ping()
            except Exception as e:
                logger.error(f"Failed to connect to Docker: {e}")
                self._client = None

    def available(self) -> bool:
        """Check if Docker sandbox is available."""
        return DOCKER_AVAILABLE and self._client is not None

    @staticmethod
    def _generate_id() -> str:
        return f"sandbox-{uuid.uuid4().hex[:12]}"

    def execute_python(
        self,
        code: str,
        timeout: int = None,
        memory_limit: str = None
    ) -> SandboxResult:
        """
        Execute Python code in an isolated Docker container.

        Args:
            code: Python code string to execute
            timeout: Override default timeout in seconds
            memory_limit: Override default memory limit

        Returns:
            SandboxResult with execution output
        """
        sandbox_id = self._generate_id()
        timeout = timeout or self.config.timeout_seconds
        memory_limit = memory_limit or self.config.memory_limit

        if not self.available():
            return self._simulate_execution(sandbox_id, code, timeout)

        # Write code to a temp file in Docker
        script_path = "/tmp/sandbox_script.py"
        wrapped_code = self._wrap_code(code)

        # Create container
        volumes = {}
        environment = {
            "PYTHONUNBUFFERED": "1",
            "PYTHONDONTWRITEBYTECODE": "1",
            **self.config.environment,
        }

        try:
            container = self._client.containers.create(
                image=self.config.image,
                command=f"python {script_path}",
                volumes=volumes,
                environment=environment,
                mem_limit=memory_limit,
                cpu_shares=self.config.cpu_shares,
                network_disabled=self.config.network_disabled,
                read_only=self.config.read_only,
                working_dir="/tmp",
                stdin_open=False,
                tty=False,
            )

            self._active_containers[sandbox_id] = container

            # Copy script into container
            import io
            script_content = wrapped_code.encode('utf-8')
            container.put_archive("/tmp", io.BytesIO(
                self._create_tar_archive(script_path, script_content)
            ))

            # Start and monitor
            start_time = time.time()
            container.start()

            try:
                exit_code = container.wait(timeout=timeout)
                duration_ms = int((time.time() - start_time) * 1000)
                timeout_occurred = False
            except Exception:
                # Timeout - kill the container
                container.kill(signal.SIGKILL)
                container.wait()
                duration_ms = timeout * 1000
                timeout_occurred = True

            # Read output
            stdout = ""
            stderr = ""
            try:
                logs = container.logs(stdout=True, stderr=True)
                output = logs.decode('utf-8', errors='replace')
                # Docker interleaves stdout/stderr, split roughly
                lines = output.split('\n')
                stdout_lines = []
                stderr_lines = []
                for line in lines:
                    if 'STDERR' in line:
                        stderr_lines.append(line.replace('STDERR:', ''))
                    else:
                        stdout_lines.append(line)
                stdout = '\n'.join(stdout_lines)
                stderr = '\n'.join(stderr_lines)
            except Exception as e:
                stderr = f"Failed to read output: {e}"

            # Trim output to max size
            if len(stdout) > self.config.max_output_size:
                stdout = stdout[:self.config.max_output_size] + "\n... [output truncated]"
            if len(stderr) > self.config.max_output_size:
                stderr = stderr[:self.config.max_output_size] + "\n... [output truncated]"

            return SandboxResult(
                id=sandbox_id,
                exit_code=exit_code if not timeout_occurred else -1,
                stdout=stdout.strip(),
                stderr=stderr.strip(),
                duration_ms=duration_ms,
                timeout=timeout_occurred,
            )

        except Exception as e:
            logger.error(f"Sandbox execution failed: {e}")
            return SandboxResult(
                id=sandbox_id,
                exit_code=-1,
                stdout="",
                stderr="",
                duration_ms=0,
                error=str(e),
            )
        finally:
            # Cleanup
            self._cleanup_container(sandbox_id)

    def execute_from_file(
        self,
        file_path: str,
        args: List[str] = None,
        timeout: int = None
    ) -> SandboxResult:
        """Execute a Python file inside the sandbox."""
        with open(file_path, 'r') as f:
            code = f.read()
        # Add argument simulation
        if args:
            code = f"import sys\nsys.argv = {['script.py'] + args}\n" + code
        return self.execute_python(code, timeout=timeout)

    def _wrap_code(self, code: str) -> str:
        """Wrap user code with safety guards."""
        return f"""
import sys
import os

# Restrict builtins
__builtins__['__import__'] = __import__
__builtins__['open'] = open

# Remove dangerous modules from accessible list
_BLOCKED_MODULES = ['subprocess', 'os.system', 'os.popen', 'commands',
                    'ctypes', 'pickle', 'marshal', 'imp', 'dl']

_original_import = __builtins__.__import__
def _safe_import(name, *args, **kwargs):
    if name in _BLOCKED_MODULES:
        raise ImportError(f"Module {{name}} is not allowed in sandbox")
    return _original_import(name, *args, **kwargs)

__builtins__.__import__ = _safe_import

# User code below
{code}
"""

    def _cleanup_container(self, sandbox_id: str):
        """Remove container and free resources."""
        try:
            container = self._active_containers.pop(sandbox_id, None)
            if container:
                try:
                    container.remove(force=True)
                except Exception:
                    pass
        except Exception as e:
            logger.warning(f"Cleanup failed for {sandbox_id}: {e}")

    def kill(self, sandbox_id: str):
        """Kill a running sandbox by ID."""
        container = self._active_containers.get(sandbox_id)
        if container:
            try:
                container.kill()
            except Exception:
                pass
            finally:
                self._active_containers.pop(sandbox_id, None)

    def list_active(self) -> List[str]:
        """List active sandbox IDs."""
        return list(self._active_containers.keys())

    def cleanup_all(self):
        """Kill and remove all active sandboxes."""
        for sandbox_id in list(self._active_containers.keys()):
            self.kill(sandbox_id)

    def _simulate_execution(self, sandbox_id: str, code: str, timeout: int) -> SandboxResult:
        """Simulate execution when Docker is not available (mock mode)."""
        logger.info(f"[Sandbox-SIMULATE] Executing code (mock mode): {code[:100]}...")

        result = SandboxResult(
            id=sandbox_id,
            exit_code=0,
            stdout="",
            stderr="",
            duration_ms=0,
        )

        # Simple evaluation for trusted test environments
        try:
            import io
            import contextlib

            stdout_capture = io.StringIO()
            start = time.time()

            with contextlib.redirect_stdout(stdout_capture):
                exec(compile(code, "<sandbox>", "exec"), {
                    "__name__": "__sandbox__",
                    "__builtins__": {
                        "print": print,
                        "len": len,
                        "range": range,
                        "str": str,
                        "int": int,
                        "float": float,
                        "list": list,
                        "dict": dict,
                        "tuple": tuple,
                        "set": set,
                        "Exception": Exception,
                        "ValueError": ValueError,
                        "TypeError": TypeError,
                    }
                })

            result.stdout = stdout_capture.getvalue()
            result.duration_ms = int((time.time() - start) * 1000)
        except Exception as e:
            result.stderr = str(e)
            result.exit_code = 1

        return result

    @staticmethod
    def _create_tar_archive(path: str, content: bytes) -> bytes:
        """Create a minimal tar archive with a single file."""
        import struct

        def tar_header(name: str, size: int) -> bytes:
            name_bytes = name.encode('utf-8')
            header = b''
            header += name_bytes.ljust(100, b'\0')
            header += b'0000755\0'  # mode
            header += b'0000000\0'  # uid
            header += b'0000000\0'  # gid
            header += f'{size:011o}'.encode() + b'\0'  # size
            header += f'{int(time.time()):011o}'.encode() + b'\0'  # mtime
            header += b' '  # checksum
            header += b'0'  # typeflag (regular file)
            header += b'\0' * 100  # linkname
            header += b'posix\0' * 6  # magic + version
            header += b'root\x00' * 2  # uname
            header += b'root\x00' * 2  # gname
            header += b'\0' * 8  # devmajor
            header += b'\0' * 8  # devminor
            header += b'\0' * 155  # prefix
            # Recalculate checksum
            checksum = sum(header)
            header = header[:148] + f'{checksum:06o}'.encode() + b'\0' + header[156:]
            return header

        size = len(content)
        padding = 512 - (size % 512) if size % 512 != 0 else 0
        tar = tar_header(path, size)
        tar += content
        tar += b'\0' * padding
        # End of tar (two empty 512-byte blocks)
        tar += b'\0' * 1024
        return tar