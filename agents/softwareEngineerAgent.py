from core.executor import Executor
from core import executor
from llm import call_llm, call_ops_llm

from models import ExecutionIntent, ExecutionResult
from utils.agentUtiles import logStatus, sanitize_command, scan_workspace, scan_ports

WORKTIMEOUT = 100
SMALLPREDICTION = 50
AVERAGEPREDICTION = 150
LARGEPREDICTION = 300
MAX_ITERATIONS = 5
SANDBOX_PATH = "sandbox/SoftwareEngineerAgent"

commonPayloadMeassages = "\nWhen running a server:\n" \
            "- MUST run it in background using '&'\n"\
            "- MUST add 'sleep 5' before any test command\n"\
            "RULES:\n"\
            "- Output ONLY commands\n"

class SoftwareEngineerAgent:

    def __init__(self,context="", task=""):
        self.context = context
        self.task = task
        self.executor = Executor(SANDBOX_PATH)
        self.archetype = self.archetype()
        logStatus({
                "status": "An Agent was created",
                "ui_data": {
                    "type": "SoftwareEngineerAgent",
                    "ui_status_code": 300 # UI status code 300 means agent created and ready, waiting for task.
                }
            })

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
                    "- Never hardcode variables when possible, if you can't define them: abstract them as global constants or arguments in case is a function.\n"
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
        
        filesystem = scan_workspace(SANDBOX_PATH)
        portstatus = scan_ports()
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
                    "- Keep response under 10-12 short sentences OR max 1100 characters\n"
                    "- Be extremely concise\n"
                    "- Prefer actionable insights over explanations\n"
                    "- If relevant files likely exist, explicitly suggest: cat / ls / grep\n"
                    "- If multiple components are needed, suggest folder separation\n"
                    "- If task involves bugs, identify likely cause category (not detailed debugging)\n"
                    "- Define clear names for files, functions, variables, and commands when relevant, the agent needs to persist them.\n"
                    "- Before starting a server, always ensure previous instances are stopped using pkill or similar commands.\n"
                    "- Check if port or service is already running before suggesting to start it, if so suggest to stop it first using pkill or similar commands.\n"
                    "- DO NOT include markdown (e.g., ```bash).\n"
                    "- DO NOT include comments (#)."
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
        filesystem = scan_workspace(SANDBOX_PATH)
        payload = {
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You are a strict command generator for a terminal execution system.\n"
                        "NO explanations.\n"
                        "Return ONLY raw executable bash commands. No explanations. No markdown.\n"
                        "No comments.\n"
                        "Output must be directly runnable in a shell.\n"
                        "Your output should be concise, correct, and executable.\n"
                        "\n"
                        "CURRNT FILESYSTEM:\n"
                        f"{filesystem}\n"
                        "RULES:\n"
                        "- Output must be a valid bash script.\n"
                        "- You MAY use multiple lines.\n"
                        "- Use '&&' to chain commands when appropriate, but NOT required for heredoc blocks.\n"
                        "- For multi-line file creation, you MUST use a heredoc with this EXACT structure:\n"
                        "  cat <<EOF > filename\n"
                        "  <content>\n"
                        "  EOF\n"
                        "- 'EOF' MUST be on its own line with NO spaces or indentation.\n"
                        "- The heredoc block MUST be completed before any other command.\n"
                        "- NEVER use echo for multi-line content.\n"
                        "- Commands MUST be in correct execution order.\n"
                        "- ALWAYS install required dependencies explicitly.\n"
                        "- NEVER use invalid syntax like '&& &'.\n"
                        "- NEVER call curl before the server is started.\n"
                        "- Ensure all bash syntax is valid.\n"
                        "- DO NOT include markdown (e.g., ```bash).\n"
                        "- DO NOT include comments (#)."
                        "- NEVER ADD ```bash OR ``` IN ANY PART OF THE RESPONSE. you are running this command directly in a bash shell, markdown is not valid syntax."
                        f"{commonPayloadMeassages}"
                    )
                },
                {
                    "role": "user",
                    "content": selected_task
                }
            ],
            "stream": False,
            "num_predict": LARGEPREDICTION,
            "temperature": 0.5
        }
        return call_ops_llm(payload)
    
    def generate_test_command(self, task=None) -> str:
        selected_task = task if task else self.task
        filesystem = scan_workspace(SANDBOX_PATH)
        payload = {
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You are a strict test command generator.\n"
                        "The task is ALREADY executed.\n"
                        "Your ONLY job is to validate it.\n"
                        "Your are expert in QA testing.\n"
                        "\n"
                        "CRITICAL:\n"
                        "- DO NOT create, modify, or install anything.\n"
                        "- DO NOT start servers.\n"
                        "- DO NOT define functions.\n"
                        "- DO NOT explain.\n"
                        "\n"
                        "OUTPUT:\n"
                        "- ONLY raw bash commands.\n"
                        "- MUST be minimal.\n"
                        "- MUST be directly executable.\n"
                        "- NO comments.\n"
                        "- NO markdown.\n"
                        "\n"
                        "TEST RULES:\n"
                        "- If API → use curl to existing endpoint.\n"
                        "- Validate response content or status code.\n"
                        "\n"
                        "FORBIDDEN:\n"
                        "- NO '#'\n"
                        "- NO 'echo explanations'\n"
                        "- NO functions\n"
                        "- NO installs\n"
                        "- NO server startup\n"
                        "CURRENT FILESYSTEM:\n"
                        f"{filesystem}\n"
                        f"{commonPayloadMeassages}"
                    )
                },
                {
                    "role": "user",
                    "content": f"Task to test: {selected_task}"
                }
            ],
            "stream": False,
            "num_predict": SMALLPREDICTION,
            "temperature": 0.5
        }
        return call_ops_llm(payload)

    def doFeedback(self, task, command, result, test_command, testsResult) -> str:
        filesystem = scan_workspace(SANDBOX_PATH)
        messages = [
            {
                "role": "system",
                "content": "Answer ONLY as: \n"
                " 1. yes All good.\n"
                f" 2. NO, Include specific reasons for the failure, current filesystem: {filesystem}.\n"
                "Determine if the execution result satisfies the task requirements with no errors using only one of the above responses. \n"
                "Advise to reuse files already create by the agent in the filesystem when possible. \n"
                "You are a feedback system for a software engineering agent. Your job is to analyze the execution result of a command to determine if output does ordoesn't satisfy the task.\n"
                "Check for specific keywords in stdout or stderr that indicate success or failure. If you see evidence of failure, such as error messages in stderr or a non-zero exit code.\n"
            },
            {
                "role": "user",
                "content": f"""
                    Task:
                    {task}
                    \n
                    Bash Command Executed:
                    {command}
                    \n
                    Execution result:
                    stdout: {result.stdout}
                    stderr: {result.stderr}
                    exit_code: {result.exit_code}
                    \n
                    Bash Test Command Executed:
                    {test_command}
                    \n
                    Test Result:
                    stdout: {testsResult.stdout}
                    stderr: {testsResult.stderr}
                    exit_code: {testsResult.exit_code}
                    \n
                    Does this satisfy the task with no errors?
                    Look for specific keywords in stdout or stderr that indicate success.
                    """
            }
        ]

        response = call_llm(messages, SMALLPREDICTION)
        return response

    #TODO: extract logic to reuse in doWork.
    def evolve_intent(self, task, intent, feedback) -> ExecutionIntent:
        new_command = sanitize_command(self.generate_command(f"{task}\n\nFeedback:\n{feedback}"))

        return ExecutionIntent(
            command=new_command,
            timeout=intent.timeout,
            ui_data=intent.ui_data
        )
    
    def runTests(self, test_command) -> ExecutionResult:
        intent = ExecutionIntent(
            command=test_command,
            timeout=WORKTIMEOUT
        )
        try:
            result = self.executor.run(intent, 999)
        except Exception as e:
            print(f"[TEST EXECUTION ERROR]: {e}")
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
            print("[TEST EXECUTION FINISHED]")
        return result

    def doWork(self) -> ExecutionResult:
        logStatus({
                "status": "Work work!",
                "ui_data": {
                    "type": "SoftwareEngineerAgent",
                    "ui_status_code": 1 # UI status code 1 means agent created and ready, waiting for task.
                }
            })
        analyzed = self.analyze(self.task)
        command = sanitize_command(self.generate_command(self.task))
        test_command = sanitize_command(self.generate_test_command(self.task))

        print(f"---- Analysis: {analyzed} \n End Analysis----")
        print(f"---- Initial Command:\n {command} \n End Initial Command----")
        print(f"---- Test Command:\n {test_command} \n End Test Command----")

        logStatus({
                "status": "Got the Idea",
                "ui_data": {
                    "analysis": analyzed,
                    "command": command,
                    "test_command": test_command,
                    "ui_status_code": 2 # ui status code: 1 means starting, 2 means analyzed, 3 means thinking, 200 means success and done. from 1 to 199: accions before completion, from 200 to 299: completion and success, from 500 to 599: errors.
                }
            })

        intent = ExecutionIntent(
            command=command,
            timeout=WORKTIMEOUT
        )
        max_iterations = MAX_ITERATIONS
        feedback = "No feedback yet"

        for i in range(max_iterations):
            print(f"\n--- Iteration {i+1} ---")
            logStatus({
                "status": "thinking, I am doing the work...",
                "ui_data": {
                    "analysis": analyzed,
                    "command": command,
                    "test_command": test_command,
                    "ui_status_code": 3
                }
            })
            result = None
            try:
                logStatus({
                    "status": "running some commands in the terminal",
                    "ui_data": {
                        "stage": "executing",
                        "command": command,
                        "ui_status_code": 150
                    }
                })
                result = self.executor.run(intent, i)
            except Exception as e:
                print(f"[EXECUTION ERROR]: {e}")
                logStatus({
                    "status": "error, cli error",
                    "ui_data": {
                        "command": command,
                        "test_command": test_command,
                        "ui_status_code": 550 # UI have a dic with status codes, 550 means error.
                    }
                })
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
                testsResult = self.runTests(test_command)
                print(f"---- Test Command Result:\n stdout: {testsResult.stdout}\n")
                feedback = self.doFeedback(self.task, command, result, test_command, testsResult)
                print(f"Feedback: {feedback}\n")
            
                if "yes" in feedback.lower():
                    print("\nSTOP: task satisfied, STOPING agent ....")
                    logStatus({
                        "status": "agent done",
                        "ui_data": {
                            "status": "success",
                            "ui_status_code": 200
                        }
                    })
                    break
                else:
                    logStatus({
                        "status": "feedback",
                        "ui_data": {
                            "feedback": feedback,
                            "command": command,
                            "test_command": test_command,
                            "ui_status_code": 600 # UI status code 600 means feedback received and will evolve the command.
                        }
                    })        


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