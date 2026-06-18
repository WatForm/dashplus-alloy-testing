# Dashplus Alloy Tests

* all tests are designed to be run from within the `scripts` directory

* assumes dashplus is a sister directory to dash-testing

* this directory holds both helper Java files (e.g., AAParseResolve.java) and python scripts to run test (test_aa_dp_parse.py) and additional helper Java files.


## Python Testing 

- run as in 
 'python3 test_sat_inside_dashplus.py nad'

*test_X.py*
- has a function that is run per model_name
	- function sets a cmd to run on the model_name and receives its (output, err, return_code, time_take) from run_command(cmd)
	- decides how to process cmd results and output for pass/fail
	- returns (x,y) where x is a count of passes and y is a count of fails for this test (usually (1,0) or (0,1))
- main: controller(function_per_model_name)

*controller.py*
- takes a func_per_model_name argument and walks over entire directory of .als files to run that function on each model
- records tally of pass/fails
- currently can run multiple threads but we probably don't want this for any performance testing
- additionally provides function "run_command" and "common_err_response", "common_pass_response", which can be used in test_X.py

*config.py*
- sets paths and directories to run tests on
- setup fcn can have an argument for "who" (e.g., nad->Nancy) to setup one person's usual defaults without affecting anyone else and still commit to the repo.


## Helper Java Files

* there are common return error codes used across these files to be compared in python scripts

*AAParseResolve.java* (relies only on AA6.2)
	CompModule world =
                CompUtil.parseEverything_fromFile(null, null, args[0]);

*DPParse.java*
	AlloyFile file = parse(path.toAbsolutePath());

*DPParseResolve.java*
 	AlloyModel file = parseToModel(path.toAbsolutePath());

*InstanceChecker.java*
	modelWorld = CompUtil.parseEverything_fromString(rep, modelString);
	creates a string that is the model plus XML from .als file
	runs that file for SAT

*InstanceGenerator.java*
	creates X XML files of instances of X instances of a model at default scope Y







		


