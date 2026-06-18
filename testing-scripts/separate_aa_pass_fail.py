import config
from controller import *
from pathlib import Path
import shutil

SUCCESS = 0
PARSE_ERROR = 1
RESOLVE_ERROR = 2
OTHER_ERROR = 3

def separate_aa_pass_fail(model_name):
    cmd1 = f"{config.aa_parse_resolve} {model_name}"
    (output,err, rc_cmd1, time_taken) = run_command(cmd1)
    if rc_cmd1 == SUCCESS:
        if config.verbose:
            print(f"{BLUE}TEST RESULT: PASS, {model_name}{RESET}")
            print(f"AA: {rc_cmd1}")
            return (1,0)
    else:
        model_name_path = Path(model_name)
        new_model_name = model_name.replace("catalyst-corpus-pass", "catalyst-corpus-fail")
        new_model_name_path = Path(new_model_name)
        new_model_name_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(model_name_path, new_model_name_path)
        print(f"{RED}TEST RESULT: FAIL --> moving model to {new_model_name}{RESET}")
        print(f"{RED}AA: {rc_cmd1} {RESET}")
        return (0,1)
    
        

if __name__ == "__main__":
    controller(separate_aa_pass_fail) 