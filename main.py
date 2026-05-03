
from models import ExecutionIntent
from agents.softwareEngineerAgent import SoftwareEngineerAgent


def main():
    task = "create a py file named hello.py that prints 'Hello, World!' and then execute it."
    context = "This is a simple task to test the agent's ability to create and execute a Python script."
    print(f"Task: {task}")


    # Initial Agent
    agent = SoftwareEngineerAgent(context=context, task=task)

    agent.doWork()


if __name__ == "__main__":
    main()