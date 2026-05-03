import subprocess
import time
from models import ExecutionIntent, ExecutionResult


class Executor:

    def run(self, intent: ExecutionIntent) -> ExecutionResult:
        return self._run_bash(intent.command, intent.timeout)

    def _run_bash(self, command: str, timeout: int) -> ExecutionResult:
        start = time.time()
        cleaned_command = self.clean_bash(command)

        # 🔒 basic safety
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
                timeout=timeout
            )

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