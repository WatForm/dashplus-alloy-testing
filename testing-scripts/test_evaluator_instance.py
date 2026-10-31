from pathlib import Path
import re
import shlex
import tempfile

import config
from controller import *

SUCCESS = 0
PARSE_ERROR = 1
RESOLVE_ERROR = 2
OTHER_ERROR = 3

def test_generate_and_check(model_name):
    # Isolate runs so stale XML and models with the same stem cannot interfere.
    Path("out").mkdir(exist_ok=True)
    dump_dir = tempfile.mkdtemp(prefix="evaluator-", dir="out")
    cmd1 = (
        f"{config.alloy_evaluator} {shlex.quote(model_name)} -dumpInstance "
        f"-dumpDir={shlex.quote(dump_dir)}"
    )
    (output, err, rc_cmd1, time_taken) = run_command(cmd1)

    if rc_cmd1 != SUCCESS:
        print(f"{MAGENTA}NOT USABLE (generation failed): {model_name}{RESET}")
        print(f"{MAGENTA}InstanceGenerator: {rc_cmd1}{RESET}")
        return (0, 0)

    # The CLI colors its reports even when stdout is piped. Remove ANSI codes
    # before extracting paths or matching command-index filename suffixes.
    output = re.sub(r"\x1b\[[0-?]*[ -/]*[@-~]", "", output)

    # Only consume this invocation's SAT reports, never XML left by earlier runs.
    instances = []
    for line in output.splitlines():
        if "UNSAT — no instance to dump for: " in line:
            context = line.split("UNSAT — no instance to dump for: ", 1)[1].strip()
            print(f"{MAGENTA}SKIPPED (UNSAT, {context}): {model_name}{RESET}")
        elif "SAT — dumped instance to: " in line:
            instance_file = line.split("SAT — dumped instance to: ", 1)[1].strip()
            match = re.search(r"-instance-cmd(\d+)\.xml$", instance_file)
            command_index = int(match.group(1)) if match else None
            instances.append((instance_file, command_index))

    passed = failed = 0
    for instance_file, command_index in instances:
        context = "default scope" if command_index is None else f"command {command_index}"
        cmd2 = (
            f"{config.alloy_evaluator} {shlex.quote(model_name)} -evalConstraints "
            f"-xml={shlex.quote(instance_file)} -d"
        )
        if command_index is not None:
            cmd2 += f" -cmd={command_index}"
        (eval_output, eval_err, rc_cmd2, time_taken) = run_command(cmd2)

        if rc_cmd2 == SUCCESS and "Satisfied: TRUE" in eval_output:
            passed += 1
            if config.verbose:
                print(f"{BLUE}TEST RESULT: PASS, {model_name} ({context}){RESET}")
        else:
            failed += 1
            print(cmd1)
            print(cmd2)
            print(f"{RED}TEST RESULT: FAIL, {model_name} ({context}){RESET}")
            print(f"{RED}Generator: {rc_cmd1} Checker: {rc_cmd2}{RESET}")
            print(eval_output.strip())
            if eval_err:
                print(eval_err.strip())

    return (passed, failed)

if __name__ == "__main__":
    controller(test_generate_and_check)
