# Dashplus Alloy Tests

* all tests are designed to be run from within the `testing-scripts` directory

* assumes dashplus is a sister directory to dash-alloy-testing

* this directory holds both helper Java files (e.g., AAParseResolve.java) and python scripts to run test (test_aa_dp_parse.py) and additional helper Java files.


## Python Testing 

Filter a collected JSON report with `aggregation_script.py`. The first argument is
the input report, the last is a new output filepath, and every filter is an explicit
`--model PATH VALUE` or `--command PATH VALUE` triple. All filters must match;
`/` separates nested keys within the selected model or command. The scope is
determined only by the flag, with no automatic lookup or fallback.
Missing fields do not match. Models failing model filters are removed. Model-only
filters retain matching models even when their `commands` list is empty. If any
command filters are present, models with no surviving commands are removed.
Metadata and ordering of retained records are preserved.

```sh
python3 aggregation_script.py out/od-report.json --command dump/status sat --command evaluation/status false out/od-filtered.json
python3 aggregation_script.py out/od-report.json --command index json:null out/od-defaults.json
python3 aggregation_script.py out/od-report.json --command evaluation/integers/integer_activity_in_constraints json:true out/od-integer-activity.json
python3 aggregation_script.py out/od-report.json --model discovery/status unsupported out/od-discovery-unsupported.json
```

Bare values match strings (`false` matches the status string). Use `json:` for
typed JSON values such as `json:null`, `json:false`, and `json:4`, or `str:` to
force a literal string. Missing fields never match null. With no filter triples,
all commands are preserved. The script prints matched and total model/command
counts and includes them in a top-level `counts` object in the output report.
Model-only filters count matching models even if they have no commands; with
no filters, every model counts as matched. Command filters count a model as matched
when at least one command survives. Totals refer to the current input report.
Existing output files are rejected.

- example test: `python3 test_sat_inside_dashplus.py nad`

*test_X.py* (create one of these files for every kind of test to run)
- has a function that is run per model_name
	- function sets a cmd to run on the model_name and receives its (output, err, return_code, time_take) from run_command(cmd)
	- decides how to process cmd results and output for pass/fail
	- returns (x,y) where x is a count of passes and y is a count of fails for this test (usually (1,0) or (0,1))
- main: controller(function_per_model_name)

*controller.py* (unlikely to be edited very often)
- takes a func_per_model_name argument and walks over entire directory of .als files to run that function on each model
- records tally of pass/fails
- currently can run multiple threads but we probably don't want this for any performance testing
- additionally provides function "run_command" and "common_err_response", "common_pass_response", which can be used in test_X.py

*config.py* (set parameters for test)
- sets paths and directories to run tests on
- flags for verbose, stop_on_first_fail, etc.
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







		


