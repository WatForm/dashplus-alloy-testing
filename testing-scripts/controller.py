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
RESET = "\033[0m"
MAGENTA = "\033[35m"
BLUE = "\033[34m"


count_pass = 0
count_fail = 0
lock = Lock()
stop_event = Event() 
fail_list = []

def controller(func_per_als_model):

    global count_pass
    global count_fail
    global fail_list

    who = ""
    if len(sys.argv) > 1:
        who = sys.argv[1]
    config.setup(who)
    print("sources: "+str(config.sources))
    print("verbose: "+str(config.verbose))
    print("stop_on_first_fail: "+str(config.stop_on_first_fail))
    print("timeout: " + str(config.timeout))
    print("num_threads: "+str(config.num_threads)+"\n")

    for source in config.sources:
        print('Searching source:', source)
        print('\n')
        if not os.path.exists(source):
            print("No files to test")
            break

        alsfiles = sorted(
            os.path.join(r, file)
            for r, d, f in os.walk(source)
            for file in f if file.endswith(".als")
        )

        futures = []
        with ThreadPoolExecutor(max_workers=config.num_threads) as executor:
            for alsfile in alsfiles:
                if config.stop_on_first_fail and stop_event.is_set():
                    print("Stopping submission of new tests due to a failure.")
                    sys.exit(1)
                futures.append(executor.submit(run_test, func_per_als_model, alsfile))
            
            for future in futures:
                try:
                    future.result()
                except Exception as e:
                    print(f"Exception from test: {e}")


    print("Passed: ", count_pass)
    print("Failed: ", count_fail)
    print("Fail List:")
    for item in fail_list:
        print(item)

def run_test(func_per_als_model, als_model):
    global count_pass
    global count_fail
    global fail_list
    if stop_event.is_set():
        return

    (cnt_pass, cnt_fail) = func_per_als_model(als_model)
    with lock:
        count_pass += cnt_pass 
        count_fail += cnt_fail
        if (cnt_fail > 0):
            fail_list.append(als_model)
        print(f"Running tally -- Pass: {count_pass}; Fail: {count_fail}")
        if cnt_fail>0 and config.stop_on_first_fail:
            stop_event.set();

# methods called by individual checks (see check_*.py files)

def run_command(cmd):
    
    start = time.perf_counter()
    with subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        universal_newlines=True,
        shell=True
    ) as p:
        try:
            if config.verbose:
                print("Running:", cmd)
            (output, err) = p.communicate(timeout=config.timeout)
            rc = p.returncode
            end = time.perf_counter()
            elapsed = end - start
            return (output, err, rc, elapsed)

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
            return ("", "Timeout", 1, elapsed)
        except Exception as e:
            print(f"Error running test: {cmd}")
            return ("", "Exception", 1, 0)

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
        print(f"{BLUE}TEST RESULT: PASS, {model}, {time_taken}{RESET}")
