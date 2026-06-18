# config
# modify this file with each person's config for the tests

# defaults
# dashplus is in a sister directory to alloy-testing
dashplus = "java -ea -jar ../../dashplus/app/build/libs/watform-dashplus.jar "

# table gives output if sat; no output if not sat
alloy = "java -jar ../libs/org.alloytools.alloy.dist-6.2.0.jar exec -o - -f -t table"
aa_parse_resolve = 'java -cp ".:../libs/*" AAParseResolve'
dp_parse = 'java -cp ".:../libs/*" DPParse'
dp_parse_resolve = 'java -cp ".:../libs/*" DPParseResolve'

sources = [
			# too many models in first two for minor testing
			#'../models/catalyst-corpus/catalyst-corpus-pass',
			#'../models/catalyst-corpus/catalyst-corpus-fail'
			'../models/eid-day-expert-models',
			'../models/alloy-tools-models',
			]
verbose = True
stop_on_first_fail = True
timeout = 30000 # ms
num_threads = 12  # Number of threads to use for running tests concurrently

def setup(who):
	global dashplus
	global alloy
	global aa_parse_resolve_only
	global sources 
	global verbose
	global stop_on_first_fail
	global timeout
	global method
	global num_threads
	if who == "nad":
		print("Nancy's settings")
		# to run subdirectories
		sources = [
			#'../models/catalyst-corpus/catalyst-corpus-pass',
			# alloy-tools-models
			# all pass parsing
			#'../models/alloy-tools-models',
			'../models/eid-day-expert-models',
			]
		verbose = False
		stop_on_first_fail = True
		timeout = 30000 # ms
		# set this to 1 if want to see command/output matched up well console output
		num_threads = 1 
	#elif who == "someone_else's initials":
		# someone else can set their own values for the script parameters here
		# and commit it to the repo w/o clashing with anyone else's settings
	






