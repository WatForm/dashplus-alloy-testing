# General script for common parts of dash-testing operations
# hopefully no need to modify this script to add another kind of test

import config
import os
import sys
import subprocess
import time 
from concurrent.futures import ThreadPoolExecutor
from threading import Lock, Event

RED = "\033[31m"
MAGENTA = "\033[35m"
BLUE = "\033[34m"
GREEN = "\033[32m"
RESET = "\033[0m"

def color(c: str,msg: str):
    return c+msg+RESET

class Response:
    def __init__(self,cmd: str,stdout: str,stderr: str,time: int, return_code: int, isTimeout: bool = False,isException: bool = False):
        self.cmd = cmd
        self.time = time
        self.stdout = stdout
        self.stderr = stderr
        self.return_code = return_code
        self.isException = isException
        self.isTimeout = isTimeout
    
    def ok(self):
        return not self.isTimeout and not self.isException and self.return_code == 0
    
    def __str__(self):
        return f"""
        cmd: {self.cmd}
        time: {self.time}
        return code: {self.return_code}
        stdout: {self.stdout}
        stderr: {self.stderr}
        """



count_pass = 0
count_fail = 0
lock = Lock()
stop_event = Event() 

def controller(func_per_model):

    who = ""
    if len(sys.argv) > 1:
        who = sys.argv[1]
    config.setup(who)
    print("sources: "+str(config.sources))
    print("targets: "+str(config.targets))
    print("verbose: "+str(config.verbose))
    print("stop_on_first_fail: "+str(config.stop_on_first_fail))
    print("timeout: " + str(config.timeout))
    print("num_threads: "+str(config.num_threads)+"\n")

    for source in config.sources:
        print('Searching source:', source)
        if not os.path.exists(source):
            print("No files to test")
            break

        target_files = sorted(
            os.path.join(r, file)
            for r, d, f in os.walk(source)
            for file in f if file.endswith(config.targets)
        )

        futures = []
        with ThreadPoolExecutor(max_workers=config.num_threads) as executor:
            for f in target_files:
                if config.stop_on_first_fail and stop_event.is_set():
                    print("Stopping submission of new tests due to a failure.")
                    sys.exit(1)
                futures.append(executor.submit(run_test, func_per_model, f))
            
            for future in futures:
                try:
                    future.result()
                except Exception as e:
                    print(f"Exception from test: {e}")

    global count_pass
    global count_fail
    print("Passed: ", count_pass)
    print("Failed: ", count_fail)

def run_test(func_per_model, alloy_model):
    global count_pass
    global count_fail
    if stop_event.is_set():
        return

    (cnt_pass, cnt_fail) = func_per_model(alloy_model)
    with lock:
        count_pass += cnt_pass 
        count_fail += cnt_fail
        if cnt_fail>0 and config.stop_on_first_fail:
            stop_event.set()

# methods called by individual checks (see check_*.py files)

def run_command(cmd: str) -> Response:
    
    start = time.perf_counter()
    with subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        universal_newlines=True,
        shell=True
    ) as p:
        try:
            (output, err) = p.communicate(timeout=config.timeout)
            if config.verbose:
                # put this after executing command to get input
                # and output matched better when running in threads
                print("Running:", cmd)
            rc = p.returncode
            end = time.perf_counter()
            elapsed = end - start
            return Response(cmd,output,err,elapsed,rc)
            # return (output, err, rc, elapsed)

        except subprocess.TimeoutExpired:
            p.kill()
            (output, err) = p.communicate()
            if config.verbose:
                # put this after executing command to get input
                # and output matched better when running in threads
                print("Running:", cmd)
            rc = p.returncode
            end = time.perf_counter()
            elapsed = end - start
            return Response(cmd,"","",elapsed,rc,isTimeout=True)
            # return ("", "Timeout", 1, elapsed)
        except Exception as e:
            print(f"Error running test: {cmd}")
            return Response(cmd,"","",elapsed,1,isException=True)
            # return ("", "Exception", 1, 0)

def common_err_response(cmd, output, err, time_taken):
    if time_taken >= config.timeout:
        print(f"{RED}TEST RESULT: ERROR, {cmd}, time: TIMEOUT {config.timeout}{RESET}")
    else:
        print(f"{RED}TEST RESULT: ERROR, {cmd}, time: {time_taken}{RESET}")
    print(f"{RED}{output}{RESET}")
    print(f"{MAGENTA}{err}{RESET}")
    


def common_pass_response(model, output, err, time_taken):
    if config.verbose:
        # eventually we may want to record this in a csv file
        print(f"{GREEN}TEST RESULT: PASS, {model}, {output}, {time_taken}{RESET}")

def test_fail(model_name, message):
    print(color(RED,f"FAILED: {model_name} {message}"))

def test_pass(model_name, message):
    print(color(GREEN,f"PASSED: {model_name} {message}"))

def compose_message(response: Response) -> str:
    if response.isTimeout:
        return "Timeout"
    if response.isException:
        return "Exception"
    return str(message)
