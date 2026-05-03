from core.executor import Executor
from core import executor
from llm import call_llm, call_ops_llm
import re

from models import ExecutionIntent

class SoftwareEngineerAgent:

    def __init__(self,context="", task=""):
        self.context = context
        self.task = task
        self.executor = Executor()
        self.archetype = self.archetype()

    def sanitize_command(self,command: str) -> str:
        # remove sudo (basic safety)
        return command.replace("sudo ", "").strip()

    def archetype(self) -> str:
        context_text = self.context if self.context else "No project context provided."

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
                "content": f"{self.task}\n\nContext:\n{context_text}"
            }
        ]

        return arch
    
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
                        "No command fences. No comments unless absolutely required for execution.\n"
                        "Output must be directly runnable in a shell or interpreter.\n"
                        "You may return multiple commands separated by '&&' or new lines if needed.\n"
                        "You only create command or commands that can be executed in a terminal."
                        "Your output should be as concise as possible while still being correct and executable."
                    )
                },
                {
                    "role": "user",
                    "content": selected_task
                }
            ],
            "stream": False,
            "num_predict": 200,
            "temperature": 0.2
        }
        return call_ops_llm(payload)
    
    def should_stop(self,task, result) -> bool:
        messages = [
            {
                "role": "system",
                "content": "Answer ONLY YES or NO. No explanation."
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

                    Does this satisfy the task?
                    """
            }
        ]

        response = call_llm(messages, 50)
        return "yes" in response.lower()


    def evolve_intent(self,task, intent, result) -> ExecutionIntent:

        messages = [
            {
                "role": "system",
                "content": "Explain briefly what failed and how to fix it for a bash command generator."
            },
            {
                "role": "user",
                "content": f"""
                    TASK:
                    {task}

                    COMMAND:
                    {intent.command}

                    RESULT:
                    stdout:
                    {result.stdout}

                    stderr:
                    {result.stderr}

                    exit_code:
                    {result.exit_code}

                    Give a short FIX instruction.
                    """
            }
        ]

        feedback = call_llm(messages)

        new_command = self.sanitize_command(self.generate_command(f"{task}\n\nFix instructions:\n{feedback}"))

        print("\n[LLM FEEDBACK]:", feedback)
        print("[NEW COMMAND]:", new_command)

        return ExecutionIntent(
            command=new_command,
            timeout=intent.timeout
        )
    

    def doWork(self) -> ExecutionIntent:
        intent = ExecutionIntent(
            command=self.sanitize_command(self.generate_command()),
            timeout=50
        )

        max_iterations = 5

        for i in range(max_iterations):
            print(f"\n--- Iteration {i+1} ---")

            result = self.executor.run(intent)

            print("\nCommand:", result.command)
            print("STDOUT:", result.stdout.strip())
            print("STDERR:", result.stderr.strip())
            print("EXIT CODE:", result.exit_code)

            if self.should_stop(self.task, result):
                print("\nSTOP: task satisfied")
                break

            intent = self.evolve_intent(self.task, intent, result)

        return intent