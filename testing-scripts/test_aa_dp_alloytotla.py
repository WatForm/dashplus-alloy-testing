import config
from controller import *

SUCCESS = 0
PARSE_ERROR = 1
RESOLVE_ERROR = 2
OTHER_ERROR = 3

def test_aa_dp_alloytotla(model_name):
    # first check that it passes AA 
    cmd1 = f"{config.aa_parse_resolve} {model_name}"
    (output,err, rc_cmd1, time_taken) = run_command(cmd1)
    if rc_cmd1 == SUCCESS:
        cmd2 = f"{config.dp_alloytotla} {model_name}"
        (output,err, rc_cmd2, time_taken) = run_command(cmd2)
        if rc_cmd2 == SUCCESS:
            if config.verbose:
                print(f"{BLUE}TEST RESULT: PASS, {model_name}{RESET}")
            return (1,0)
        else:
            print(cmd1)
            print(cmd2)
            print(f"{RED}TEST RESULT: FAIL{RESET}")
            if config.verbose:
                print(f"{RED}{err}{RED}")
            return (0,1)
    else:
        print(f"{MAGENTA}NOT USABLE: {model_name}{RESET}")
        print(f"{MAGENTA}AA: {rc_cmd1}{RESET}")
        return (0,0)
        

if __name__ == "__main__":
    controller(test_aa_dp_alloytotla) 