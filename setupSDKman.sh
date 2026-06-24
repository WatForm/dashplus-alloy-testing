#!/bin/bash
export SDKMAN_DIR="$HOME/.sdkman"
[[ -s "$SDKMAN_DIR/bin/sdkman-init.sh" ]] && source "$SDKMAN_DIR/bin/sdkman-init.sh"


# get the models
cd models
if [ -d "catalyst-corpus" ]; then
    echo "catalyst-corpus exists; nothing to do"
    echo
else
	echo "Downloading catalyst-corpus.zip"
	rm -f catalyst-corpus.zip
	wget https://github.com/WatForm/dashplus-alloy-testing/releases/download/corpora-alloy-models/catalyst-corpus.zip
	echo "Unzipping"
	unzip catalyst-corpus.zip &> /dev/null
	echo "Catalyst corpus setup completed."
fi

if [ -d alloy-tools-models ]; then
	echo "alloy-tools-models exists; nothing to do"
	echo
else
	echo "Downloading alloy-tools-models"
	rm -f 886447d3369a9036aa4c3b49a82d7c557ab2e5f9.zip
	wget https://github.com/AlloyTools/models/archive/886447d3369a9036aa4c3b49a82d7c557ab2e5f9.zip
	echo "Unzipping"
	unzip 886447d3369a9036aa4c3b49a82d7c557ab2e5f9.zip &> /dev/null
	# a little bit of renaming to make filename more readable
	mv models-886447d3369a9036aa4c3b49a82d7c557ab2e5f9  alloy-tools-models
	rm -f 886447d3369a9036aa4c3b49a82d7c557ab2e5f9.zip
	# these util files fail AA6.2 because of circular imports
	# on integer
	rm -rf alloy-tools-models/utilities/types
	echo "alloy-tools-models set up completed."
fi

if [ -d eid-day-expert-models ]; then
	echo "eid-day-expert-models exists; nothing to do"
	echo
else
	echo "Downloading eid-day-expert-models"
	rm -f eid-day-expert-models.zip
	wget https://github.com/WatForm/dashplus-alloy-testing/releases/download/corpora-alloy-models/eid-day-expert-models.zip
	echo "Unzipping"
	unzip eid-day-expert-models.zip &> /dev/null
	rm -f eid-day-expert-models.zip
	cd eid-day-expert-models
	./setup.sh
	echo "eid-day-expert-models set up completed."
	cd ..
fi
echo "removing .als files not supported by dashplus parse/resolve"
echo "see models/remove-unsupported-dashplus-parse.py for list of these models and why"
echo 
python3 remove-unsupported-dashplus-parse.py
cd ..

if [ ! -d "libs" ]; then
	mkdir libs 
fi

# get AA 6.2
cd libs
if [[ -f "org.alloytools.alloy.dist-6.2.0.jar" ]]; then
	echo "org.alloytools.alloy.dist-6.2.0.jar exists; nothing to do"
	echo
else 
	echo "getting AA6.2"
	wget https://repo1.maven.org/maven2/org/alloytools/org.alloytools.alloy.dist/6.2.0/org.alloytools.alloy.dist-6.2.0.jar
fi

# get latest dashplus jar from a sister directory
if [[ -f "watform-dashplus.jar" ]]; then
	echo "watform-dashplus.jar exists; nothing to do"
	echo
else 
	echo "created symbolic link to dashplus jar in sister directory"
	ln -s ../../dashplus/app/build/libs/watform-dashplus.jar .
fi
cd ..

# compile InstanceGenerator.java and InstanceChecker.java
cd testing-scripts
echo "compiling java helpers"
sdk use java 17.0.19-amzn  
javac -cp "../libs/org.alloytools.alloy.dist-6.2.0.jar" InstanceGenerator.java
javac -cp "../libs/org.alloytools.alloy.dist-6.2.0.jar" InstanceChecker.java
javac -cp "../libs/org.alloytools.alloy.dist-6.2.0.jar" AAParseResolve.java
sdk use java 25.0.2-open
javac -cp "../libs/*" DPParse.java
javac -cp "../libs/*" DPParseResolve.java

cd ..



