import config
from controller import *

SUCCESS = 0
PARSE_ERROR = 1
RESOLVE_ERROR = 2
OTHER_ERROR = 3

def test_generate_and_check(model_name):
    # Step 1: Generate an instance (XML) from the model
    cmd1 = f"{config.dashplus} {model_name} -dumpInstance"
    (output, err, rc_cmd1, time_taken) = run_command(cmd1)

    if rc_cmd1 != SUCCESS:
        print(f"{MAGENTA}NOT USABLE (generation failed): {model_name}{RESET}")
        print(f"{MAGENTA}InstanceGenerator: {rc_cmd1}{RESET}")
        return (0, 0)

    # Step 2: Check the generated instance against the model
    # The instance XML path is expected to be printed by InstanceGenerator to output
    model_stem = model_name.split("/")[-1].replace(".als", "")
    instance_file = f"out/{model_stem}-instance.xml"
    print(f"INSTANCE IS: {instance_file}")
    
    cmd2 = f"{config.dashplus} {model_name} -evalFacts -xml={instance_file} -d"
    (output, err, rc_cmd2, time_taken) = run_command(cmd2)

    if rc_cmd2 == SUCCESS and "The facts are satisfied" in output:
        if config.verbose:
            print(f"{BLUE}TEST RESULT: PASS, {model_name}{RESET}")
            print(f"Generator: {rc_cmd1} Checker: {rc_cmd2}")
        return (1, 0)
    else:
        print(cmd1)
        print(cmd2)
        print(f"{RED}TEST RESULT: FAIL{RESET}")
        print(f"{RED}Generator: {rc_cmd1} Checker: {rc_cmd2}{RESET}")
        print(output.strip())
        return (0, 1)

if __name__ == "__main__":
    controller(test_generate_and_check)