import os
import json
import subprocess
import re

BASE = os.path.expanduser("~/.aigent/ui")

def logStatus(data: dict):
    os.makedirs(BASE, exist_ok=True)

    tmp = os.path.join(BASE, "status.tmp")
    final = os.path.join(BASE, "status.json")

    with open(tmp, "w") as f:
        json.dump(data, f)

    os.replace(tmp, final)

def sanitize_command(command: str) -> str:
        # remove sudo
        command = command.replace("sudo ", "")

        # remove markdown code fences (```bash ... ```)
        command = re.sub(r"```[a-zA-Z]*", "", command)
        command = command.replace("```", "")

        return command.strip()

def scan_workspace(base_path: str, max_depth: int = 2, max_items: int = 50) -> str:
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

def scan_ports(ports=[8000, 3000, 5000, 8080, 8081]) -> str:
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