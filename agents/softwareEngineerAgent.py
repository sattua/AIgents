import subprocess

from core.executor import Executor
from core import executor
from llm import call_llm, call_ops_llm

import os
from models import ExecutionIntent, ExecutionResult

WORKTIMEOUT = 100
SMALLPREDICTION = 50
AVERAGEPREDICTION = 150
LARGEPREDICTION = 300
SANDBOX_PATH = "sandbox/SoftwareEngineerAgent"

class SoftwareEngineerAgent:

    def __init__(self,context="", task=""):
        self.context = context
        self.task = task
        self.executor = Executor(SANDBOX_PATH)
        self.archetype = self.archetype()

    def sanitize_command(self,command: str) -> str:
        # remove sudo (basic safety)
        return command.replace("sudo ", "").strip()
        

    def scan_workspace(self, base_path: str, max_depth: int = 2, max_items: int = 50) -> str:
        result = []
        base_path = os.path.abspath(base_path)

        def walk(path, depth):
            if depth > max_depth:
                return
            try:
                items = sorted(os.listdir(path))[:max_items]
            except Exception:
                return

            for item in items:
                full_path = os.path.join(path, item)
                rel_path = os.path.relpath(full_path, base_path)

                if os.path.isdir(full_path):
                    result.append(f"[DIR]  {rel_path}/")
                    walk(full_path, depth + 1)
                else:
                    result.append(f"[FILE] {rel_path}")

        walk(base_path, 0)
        return "\n".join(result)
    
    def scan_ports(self, ports=[8000, 3000, 5000, 8080, 8081]) -> str:
        results = []

        for port in ports:
            try:
                cmd = f"lsof -i :{port}"
                output = subprocess.check_output(cmd, shell=True, text=True)

                lines = output.strip().split("\n")
                if len(lines) > 1:
                    results.append(f"[PORT {port}] IN USE")
                else:
                    results.append(f"[PORT {port}] FREE")

            except subprocess.CalledProcessError:
                results.append(f"[PORT {port}] FREE")

        return "\n".join(results)

    def archetype(self) -> str:
        context_text = self.context if self.context else "No project context provided."
        selected_task = self.task if self.task else "No specific task provided."
        arch = [
            {
                "role": "system",
                "content": (
                    "You are a senior full-stack software engineer.\n"
                    "Write clean, maintainable, production-ready commands and code.\n"
                    "Prefer simplicity over complexity.\n"
                    "Apply SOLID for human readability.\n"
                    "You MUST write secure commands and code using best practices.\n"
                    "When possible, write tests to ensure code quality.\n"
                    "Follow closy the instructions and requirements from the task.\n"
                    "Follow closy ISC2 standards in cybersecurity.\n"
                    "\n"
                    "RULES:\n"
                    "- Output ONLY commands and code\n"
                    "- Do NOT include explanations\n"
                    "- Do NOT include text before or after commands/code\n"
                    "- Commands and code must be complete and runnable\n"
                    "- Do NOT invent APIs or libraries\n"
                    "- Never hardcode secrets or sensitive info, try Env variables instead.\n"
                    "- Never hardcode variables when possible,  if you can't define them: abstract them as global constants or arguments in case is a function.\n"
                )
            },
            {
                "role": "user",
                "content": f"{selected_task}\n\nContext:\n{context_text}"
            }
        ]

        return arch
    
    def analyze(self, task=None) -> str:
        selected_task = task if task else self.task
        
        filesystem = self.scan_workspace(SANDBOX_PATH)
        portstatus = self.scan_ports()
        messages= [
            {
                "role": "system",
                "content": (
                    "You are a senior software engineering planner.\n"
                    "Your job is to quickly analyze tasks for command generation.\n"
                    f"Take in consideration the current file system:\n  /{filesystem}\n"
                    f"Take in consideration the current port status:\n  {portstatus}\n"
                    "\n"
                    "RULES (STRICT):\n"
                    "- Keep response under 8 short sentences OR max 1200 characters\n"
                    "- Be extremely concise\n"
                    "- Prefer actionable insights over explanations\n"
                    "- If relevant files likely exist, explicitly suggest: cat / ls / grep\n"
                    "- If multiple components are needed, suggest folder separation\n"
                    "- If task involves bugs, identify likely cause category (not detailed debugging)\n"
                    "- Define clear names for files, functions, variables, and commands when relevant, the agent needs to persist them.\n"
                    "- Before starting a server, always ensure previous instances are stopped using pkill or similar commands.\n"
                    "- Check if port or service is already running before suggesting to start it, if so suggest to stop it first using pkill or similar commands."
                    "\n"
                    "OUTPUT FORMAT (STRICT):\n"
                    "- Use 3 sections only:\n"
                    "  CONTEXT\n"
                    "  FILES\n"
                    "  PLAN\n"
                )
            },
            {
                "role": "user",
                "content": selected_task
            }
        ]
        return call_llm(messages, LARGEPREDICTION)


    def generate_command(self, task=None) -> str:
        selected_task = task if task else self.task
        payload = {
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You are a strict command generator for a terminal execution system.\n"
                        "NO explanations.\n"
                        "Return ONLY raw executable bash command. No explanations. No markdown.\n"
                        "No comments.\n"
                        "Output must be directly runnable in a shell or interpreter.\n"
                        "You may return multiple commands separated by ' && ', never new lines.\n"
                        "You only create command or commands that can be executed in a terminal."
                        "Your output should be as concise as possible while still being correct and executable.\n"
                            "RULES:\n"
                            "- If running a server (e.g., uvicorn, node, etc), you MUST run it in background using '&'.\n"
                            "- After starting a server, you MUST wait using 'sleep 5' or more before testing.\n"
                            "- After waiting, you MUST test your work, for example test the server using curl.\n"
                            "- Never block execution with long-running foreground processes.\n"
                            "\n"
                    )
                },
                {
                    "role": "user",
                    "content": selected_task
                }
            ],
            "stream": False,
            "num_predict": AVERAGEPREDICTION,
            "temperature": 0.2
        }
        return call_ops_llm(payload)
    
    def doFeedback(self,task, result) -> str:
        filesystem = self.scan_workspace(SANDBOX_PATH)

        messages = [
            {
                "role": "system",
                "content": "Answer ONLY as: \n"
                " 1. yes All good.\n"
                f" 2. NO, Include specific reasons for the failure, current filesystem: {filesystem}.\n"
                "Determine if the execution result satisfies the task requirements with no errors using only one of the above responses. \n"
                "You are a feedback system for a software engineering agent. Your job is to analyze the execution result of a command to determine if output does ordoesn't satisfy the task.\n"
                "Check for specific keywords in stdout or stderr that indicate success or failure. If you see evidence of failure, such as error messages in stderr or a non-zero exit code.\n"
            },
            {
                "role": "user",
                "content": f"""
                    Task:
                    {task}

                    Execution result:
                    stdout: {result.stdout}
                    stderr: {result.stderr}
                    exit_code: {result.exit_code}

                    Does this satisfy the task with no errors?
                    Look for specific keywords in stdout or stderr that indicate success.
                    """
            }
        ]

        response = call_llm(messages, SMALLPREDICTION)
        return response


    def evolve_intent(self, task, intent, feedback) -> ExecutionIntent:
        new_command = self.generate_command(f"{task}\n\nFeedback:\n{feedback}")
        print(f"---- New Command: {new_command} \n End New Command----")

        new_command = self.sanitize_command(new_command)

        return ExecutionIntent(
            command=new_command,
            timeout=intent.timeout
        )
    

    def doWork(self) -> ExecutionResult:
        analyzed = self.analyze(self.task)
        print(f"---- Analysis: {analyzed} \n End Analysis----")
        command = self.generate_command(self.task)
        print(f"---- Initial Command: {command} \n End Initial Command----")
        intent = ExecutionIntent(
            command=self.sanitize_command(command),
            timeout=WORKTIMEOUT
        )
        max_iterations = 5

        for i in range(max_iterations):
            print(f"\n--- Iteration {i+1} ---")
            feedback = "No feedback yet"
            try:
                result = self.executor.run(intent, i)
            except Exception as e:
                print(f"[EXECUTION ERROR]: {e}")
                result = ExecutionResult(
                    stdout="",
                    stderr=str(e),
                    exit_code=1,
                    execution_time_ms=0,
                    command=intent.command,
                    language="bash",
                    timed_out=False
                )

            finally:
                feedback = self.doFeedback(self.task, result)
                print(f"Feedback: {feedback}\n")
            
            if "yes" in feedback.lower():
                print("\nSTOP: task satisfied")
                break

            intent = self.evolve_intent(analyzed, intent, feedback)

        result = ExecutionResult(
            stdout=result.stdout,
            stderr=result.stderr,
            exit_code=result.exit_code,
            execution_time_ms=result.execution_time_ms,
            command=intent.command,
            language="bash"
        )
        return result