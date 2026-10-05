import re
import sys
from pathlib import Path

root_dir: str = sys.argv[1]
file_regex: str = sys.argv[2]
timeout: int = int(sys.argv[3])


current_dir = Path(root_dir)

absolute_paths: list[str] = []

for path in current_dir.rglob("*"):
	if path.is_file():
		abs_path = str(path.absolute())
		if abs_path.endswith(".als") and (bool(re.fullmatch(file_regex,abs_path))):
			absolute_paths.append(abs_path)


commands = "#!/bin/bash\n"

for p in absolute_paths:
	command: str = "timeout 3 java -jar ../dashplus/app/build/libs/alloytotla.jar "+p+" &> ./temp/"+p.rsplit("/", 1)[-1]+".log"
	commands = commands + "\n" + command


print(commands)