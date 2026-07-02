# config
# modify this file with each person's config for the tests

# defaults
RECEIPT_FOLDER = "./libs/alloy"
RECEIPT_FILE = RECEIPT_FOLDER + "/receipt.json"

dashplus = "java -ea -jar ../dashplus/app/build/libs/watform-dashplus.jar"
alloy = "java -jar ./bin/org.alloytools.alloy.dist-6.2.0.jar exec -f -o -"
tlc = "java -jar ./bin/tla2tools.jar"

targets = ".als"

sources = [
			'./models/jackson'
		]
verbose = True
stop_on_first_fail = True
timeout = 3000 # ms
num_threads = 1  # Number of threads to use for running tests concurrently

def setup(who):
	global dashplus
	global alloy
	global sources 
	global verbose
	global stop_on_first_fail
	global timeout
	global method
	global num_threads
	global targets
	if who == "nad":
		print("Nancy's settings")
		# don't bother with setup each time; just run from sister directory
		dashplus = "java -ea -jar ../dashplus/app/build/libs/watform-dashplus.jar "
		
		# verbose = False
		# stop_on_first_fail = False
		timeout = 30000 # ms
		# set this to 1 if want to see command/output matched up well console output
		num_threads = 1 
		# a good combination when debugging is verbose=False, stop_on_first_fail=True, num_threads=12
	elif who == "mkj":
		print("Mathew's settings")
		# Mathew can set his own values for the script parameters here
	






