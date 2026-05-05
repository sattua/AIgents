from dataclasses import dataclass
from typing import Optional, Dict


@dataclass
class ExecutionResult:
    stdout: str
    stderr: str
    exit_code: int

    execution_time_ms: int
    command: str
    language: str

    error_type: Optional[str] = None
    timed_out: bool = False

    metadata: Optional[Dict] = None

@dataclass
class ExecutionIntent:
    command: str
    ui_data: Optional[Dict] = None
    timeout: int = 10
    cwd: Optional[str] = None
    env: Optional[Dict[str, str]] = None

@dataclass
class ExecutionGoal:
    description: str

    # opcional pero muy útil
    success_criteria: Optional[str] = None

    max_iterations: int = 5

from typing import Literal


ExecutionAction = Literal["CONTINUE", "FIX", "DONE"]


@dataclass
class ExecutionDecision:
    action: ExecutionAction
    reason: Optional[str] = None

from typing import List


@dataclass
class ExecutionContext:
    history: List[ExecutionResult]

    current_goal: Optional[ExecutionGoal] = None
    iteration: int = 0

    shared_state: Optional[Dict] = None