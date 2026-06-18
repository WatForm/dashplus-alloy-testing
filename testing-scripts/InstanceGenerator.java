// wget https://repo1.maven.org/maven2/org/alloytools/org.alloytools.alloy.dist/6.2.0/org.alloytools.alloy.dist-6.2.0.jar into sister directory libs

// jenv local 17.0.16
// run this with 
// javac -cp ../bin/org.alloytools.alloy.dist-6.2.0.jar InstanceGenerator.java
// java -cp .:../bin/org.alloytools.alloy.dist-6.2.0.jar InstanceGenerator model.als scopeNum numInstances

// generates numInstances .xml instances of model.als for an EXACT scope of scopeNum for every top-level sig
// if the model is unsat at that scope then no instance file is written 
// writes the files in the same directory as model.als
// overwrites any existing xml files of the same name

import java.io.File;

import java.util.List;
import java.util.ArrayList;
import java.util.Collections;
import java.util.stream.Collectors;
import java.io.PrintWriter;


import java.nio.file.Path;
import java.nio.file.Files;
import java.nio.charset.StandardCharsets;


import edu.mit.csail.sdg.alloy4.A4Reporter;
import edu.mit.csail.sdg.ast.Sig;
import edu.mit.csail.sdg.parser.CompModule;
import edu.mit.csail.sdg.parser.CompUtil;

import edu.mit.csail.sdg.translator.A4Options;
import edu.mit.csail.sdg.translator.A4Solution;

import edu.mit.csail.sdg.translator.A4SolutionWriter;

import edu.mit.csail.sdg.translator.TranslateAlloyToKodkod;

import kodkod.ast.Relation;


public class InstanceGenerator {

    //private static final String RUN_CMD_FORMAT = "run {} for exactly %d";
    private static final String INSTANCE_NAME_FORMAT = "%s-instance-%d-%d.xml";

    private static String getCmd(List<String> topLevelSigs, Integer scope) {
        String sc = String.valueOf(scope);
        if (topLevelSigs.isEmpty()) {
            return "\nrun {}";
        } else {
            return "\nrun {} for "+ sc + " but " +
                    topLevelSigs.stream()
                        .map(s -> "exactly "+sc+" " + s)
                        .collect(Collectors.joining(", ")) +"\n\n";
        }

    }

    public static void main(String[] args) throws Exception {

        if (args.length != 3) {
            System.err.println("FAIL: Args required: modelfileName scope instanceNum");
            System.exit(1);
        }

        String modelFileName = args[0];

        // get absolutePath for file
        Path path = Path.of(modelFileName);  
        Path absolutePath = path.toAbsolutePath();
        String fullFileName = absolutePath.toString();
        int dot = fullFileName.lastIndexOf(".");
        String outputFileNamePrefix =
            dot == -1 ? fullFileName : fullFileName.substring(0, dot);

        if (!Files.exists(absolutePath)) {
            System.out.println("File does not exist: " + fullFileName);
            System.exit(1);
        }

        Integer scope = Integer.parseInt(args[1]);
        if (! (scope >= 0)) {
            System.out.println("Scope must be >= 0");
            System.exit(1);
        }

        Integer numInstances = Integer.parseInt(args[2]);
        if (! (numInstances >= 1)) {
            System.out.println("numInstances must be >= 1");
            System.exit(1);
        }

        // read the contents of the input .als model
        String modelString = "";
        try {
            modelString = Files.readString(absolutePath, StandardCharsets.UTF_8);
        } catch (Exception e) {
            System.out.println("FAIL: Reading "+modelFileName +" failed with\n" + e.getMessage());
            System.exit(1);
        }

        List<String> topLevelSigs = new ArrayList<String>();
        
        A4Reporter rep = new A4Reporter();
        
        try {
            CompModule modelWorld = CompUtil.parseEverything_fromString(rep, modelString);
            for (Sig sig : modelWorld.getAllReachableSigs()) {
                if (sig.isTopLevel() && !sig.builtin && sig.isOne == null && sig.isLone == null) {
                    topLevelSigs.add(sig.label.replace("this/",""));
                }
            }
        } catch (Exception e) {
            System.out.println("FAIL: Alloy jar failed to parse model with message\n" + e.getMessage());
            System.exit(1);
        } 

        String cmd = getCmd(topLevelSigs,scope);
        String modelPlusCmd = modelString + cmd;
        CompModule modelPlusCmdWorld = null;
        try {
            modelPlusCmdWorld = CompUtil.parseEverything_fromString(rep, modelPlusCmd);
        } catch (Exception e) {
            System.out.println("FAIL: Alloy jar failed to parse model + cmd with message\n" + e.getMessage());
            System.exit(1);
        } 

        // because we added one to it
        int modelNumCmds = modelPlusCmdWorld.getAllCommands().size();
        // suppress kodkod messages
        A4Options opt = new A4Options();
        A4Solution sol = null;
        System.setProperty("org.slf4j.simpleLogger.log.kodkod.engine.config", "warn");
        try {
            sol = TranslateAlloyToKodkod.execute_command(
                rep, 
                modelPlusCmdWorld.getAllReachableSigs(), 
                modelPlusCmdWorld.getAllCommands().get(modelNumCmds-1), 
                opt); 
        } catch (Exception e) {
            System.out.println("FAIL: Alloy jar failed to execute model + cmd with message\n" + e.getMessage());
            System.exit(1);
        } 
        Integer k = 0;
        while (sol.satisfiable() && k < numInstances) {
            k++;
            String instanceFileName = INSTANCE_NAME_FORMAT.formatted(outputFileNamePrefix, scope, k);
            
            try (PrintWriter out = new PrintWriter(new File(instanceFileName))) {
                // sol.writeXML(instanceFileName) is flaky
                // it worked within dashplus but here gives an error
                // about extraSkolems not being initialized 
                A4SolutionWriter.writeInstance(rep,sol,out,Collections.emptyList(), null); 
            } catch (Exception e) {
                System.out.println("FAIL: Alloy jar failed to write solution\n" + e.getMessage());
                System.exit(1);
            } 
            System.out.println("Wrote: "+ instanceFileName);    
            sol = sol.next();   
        } 
    }
}
    
    



