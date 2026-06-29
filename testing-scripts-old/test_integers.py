import config
from controller import *
import os
import json



def test_translate_run_and_time_tla(model_name):

	with open(model_name) as file:
		contents = file.read()

	correct = "util/integer" not in contents
	
	if correct:
		test_pass(model_name, "free of integers")
		return (1,0)
	else:
		test_fail(model_name, f"contains util integer")
		return (0,1)


	test_fail(model_name, "something went wrong")
	return (0,1)
	


if __name__ == "__main__":
    controller(test_translate_run_and_time_tla) 