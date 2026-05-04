
from models import ExecutionResult
from agents.softwareEngineerAgent import SoftwareEngineerAgent
import sys

def main():
    task = task = """
        Create a FastAPI app with:
        - running on port 8081
        - GET /test returning {"message": "Testing 123"}

        Then:
        - install dependencies
        - run the server
        - test it using curl
        """
    context = "This is a simple task to test the agent's ability to create and execute a Python script."
    print(f"Task: {task}")
    
    # TODO: create UI interface for windows and linux.

    # TODO: Create a pipeline of agents, where one agent creates the script, another agent reviews it, and a third agent executes it and provides feedback. The first agent should then use that feedback to improve the script and try again, until the task is completed successfully or a maximum number of iterations is reached.
    agent = SoftwareEngineerAgent(context=context, task=task)

    result: ExecutionResult = agent.doWork()
    if result.exit_code != 0:
        print("Task failed, unknown error.")
        sys.exit(1)

    print("Task completed successfully.")

if __name__ == "__main__":
    main()