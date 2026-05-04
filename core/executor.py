import subprocess
import time
import os
from models import ExecutionIntent, ExecutionResult


class Executor:

    def __init__(self, workspace_dir: str = "sandbox/default", index: int = 0):
        self.workspace_dir = workspace_dir
        self.index = index
        self._ensure_workspace()

    def _ensure_workspace(self):
        os.makedirs(self.workspace_dir, exist_ok=True)

    def run(self, intent: ExecutionIntent, index: int) -> ExecutionResult:
        self.index = index
        return self._run_bash(intent.command, intent.timeout)

    def _run_bash(self, command: str, timeout: int) -> ExecutionResult:
        start = time.time()
        print(f"Running command id: {self.index}, at: {start} with timeout: {timeout}s")
        cleaned_command = self.clean_bash(command)

        # basic safety
        forbidden = ["rm -rf", "shutdown", "reboot", ":(){:|:&};:"]
        for cmd in forbidden:
            if cmd in cleaned_command:
                return ExecutionResult(
                    stdout="",
                    stderr="Forbidden command detected",
                    exit_code=1,
                    execution_time_ms=0,
                    command=cleaned_command,
                    language="bash",
                    timed_out=False
                )

        cmd = ["bash", "-c", cleaned_command]

        try:
            process = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=self.workspace_dir
            )


            print(f"====Process completed, id: {self.index} ====> {process}")



            return ExecutionResult(
                stdout=process.stdout,
                stderr=process.stderr,
                exit_code=process.returncode,
                execution_time_ms=int((time.time() - start) * 1000),
                command=" ".join(cmd),
                language="bash",
                timed_out=False
            )

        except subprocess.TimeoutExpired:
            return ExecutionResult(
                stdout="",
                stderr="Timeout expired",
                exit_code=124,
                execution_time_ms=int((time.time() - start) * 1000),
                command=" ".join(cmd),
                language="bash",
                timed_out=True
            )

    def clean_bash(self, command: str) -> str:
        command = command.strip()

        # remove markdown
        command = command.replace("```bash", "").replace("```", "")
        # remove shebang
        if command.startswith("#!"):
            command = "\n".join(command.split("\n")[1:])

        return command.strip()