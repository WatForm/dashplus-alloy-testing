/*
    To use this script:
    - (may already be done) wget https://repo1.maven.org/maven2/org/alloytools/org.alloytools.alloy.dist/6.2.0/org.alloytools.alloy.dist-6.2.0.jar into sister directory libs
    - jenv local 17.0.16
    - jenv shell 17.0.16
    - javac -cp ../scoring/org.alloytools.alloy.dist-6.2.0.jar InstanceChecker.java

    Run the script with:
    java -cp .:../scoring/org.alloytools.alloy.dist-6.2.0.jar InstanceChecker modelfileName xmlFileName 

    This script adds to the model:
        one sig atom1 extends A       for every atom of every top-level sig
        sig = atom1 + atom2 + atom2   for every sig (top-level, subset sig, subsig)
        sig<:field = atom1 -> atom2 -> ... + atom3 -> atom3 -> ...   for every field of sig 
        run {} for X Int              where X is the bitwidth used in the instance

    - Scopes of sigs other than Int are not needed because they are set exactly in the facts
    - Overloading of fields within the model (because sig<:field is used above) is supported.
    - Atoms are stored in their unique signature (thus they may be in an extends child and not the parent), 
    thus to find all atoms in a sig, we have to traverse the sig hierarchy created by the parent ids
    
    Unsupported:
    - A/Ord or Ord/Ord (sigs arising from open statements)

    Assumptions:
    - the top-level sigs have univ as their parent  (seems to be true in all instances)
    - subset sigs ('in') have no parent in the XML (seems to be true in all instances)
    - ignores the upperbound tags in the XML (from old versions of AA)
    - seq/Int is never used so its scope doesn't matter (not sure how to check this one)
*/

import java.io.File;
import java.util.Set;
import java.util.HashSet;
import java.util.List;
import java.util.ArrayList;
import java.util.Map;
import java.util.HashMap;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

import javax.xml.parsers.DocumentBuilder;
import javax.xml.parsers.DocumentBuilderFactory;
import org.w3c.dom.Document;
import org.w3c.dom.NodeList;
import org.w3c.dom.Element;

import java.nio.file.Path;
import java.nio.file.Files;
import java.nio.charset.StandardCharsets;

import edu.mit.csail.sdg.alloy4.A4Reporter;
import edu.mit.csail.sdg.alloy4.XMLNode;

import edu.mit.csail.sdg.ast.Sig;
import edu.mit.csail.sdg.ast.Sig.PrimSig;
import edu.mit.csail.sdg.ast.Sig.Field;

import edu.mit.csail.sdg.parser.CompModule;
import edu.mit.csail.sdg.parser.CompUtil;

import edu.mit.csail.sdg.translator.A4Options;
import edu.mit.csail.sdg.translator.A4Solution;
import edu.mit.csail.sdg.translator.A4SolutionReader;
import edu.mit.csail.sdg.translator.A4Tuple;
import edu.mit.csail.sdg.translator.A4TupleSet;
import edu.mit.csail.sdg.translator.TranslateAlloyToKodkod;

import kodkod.ast.Relation;


public class InstanceChecker {

    private static Map<String,SigInfo> idToSigInfo;

    private static String SUBSET = "SUBSET"; // my choice of name
    private static String UNIV = "univ"; // AA's choice of name
    
    // turn a name in the XML into one that Alloy will 
    // accept in a model
    private static String alloyName(String name) {
        if (name.contains("$")) {
            return name.replace("$","ʃ") ;
        } else if (name.startsWith("this/")) {
            return name.replace("this/","");
        } else if (name.contains("/")) {
            System.out.println("Contains name non-'this' qualified name "+ name);
            System.exit(2);
            return "";
        } else 
            return name;
    }

    // determine the arity of a field
    // based on the number of "type" in "types"
    // e.g., <types> <type ID="8"/> <type ID="8"/> </types>
    private static int getFieldArity(Element field) {
        NodeList typesList = field.getElementsByTagName("types");
        if (typesList.getLength() == 0) return 0;
        Element types = (Element) typesList.item(0);
        NodeList typeNodes = types.getElementsByTagName("type");
        return typeNodes.getLength();
    }

    // each Sig XML node stores only the atoms unique to 
    // that sig, so we have to populate the parent sigs
    // with the atoms from their child sigs
    // as well as their own atoms
    private static List<String>collectAtoms(String id) {
        List<String> atoms = new ArrayList<String>();
        for (String child:idToSigInfo.get(id).children) {
            atoms.addAll(collectAtoms(child));
        }
        atoms.addAll(idToSigInfo.get(id).atoms);
        return atoms;
    }

    public static void main(String[] args) throws Exception {

        if (args.length != 2) {
            System.err.println("FAIL: Args required: modelfileName xmlFileNamem");
            System.exit(2);
        }

        // check args are fine
        String modelFileName = args[0];
        String xmlFileName = args[1];

        Path modelPath = Path.of(modelFileName).toAbsolutePath();  
        String modelFullFileName = modelPath.toString();
        if (!Files.exists(modelPath)) {
            System.out.println("File does not exist: " + modelFullFileName);
            System.exit(2);
        }

        Path xmlPath = Path.of(xmlFileName).toAbsolutePath();  
        String xmlFullFileName = xmlPath.toString();
        if (!Files.exists(xmlPath)) {
            System.out.println("File does not exist: " + xmlFullFileName);
            System.exit(2);
        }

        // read the contents of the input .als model
        String modelString = "";
        try {
            modelString = Files.readString(modelPath, StandardCharsets.UTF_8);
        } catch (Exception e) {
            System.out.println("FAIL: Reading "+modelFullFileName +" failed with\n" + e.getMessage());
            System.exit(2);
        }

        // create the CompModel of the .als file
        A4Reporter rep = new A4Reporter();
        CompModule modelWorld = null;
        try {
            modelWorld = CompUtil.parseEverything_fromString(rep, modelString);
        } catch (Exception e) {
            System.out.println("FAIL: Alloy jar failed to parse model with message\n" + e.getMessage());
            System.exit(2);
        }
    
        // get the field/sig names used in the model
        // these names include seq/Int, and other builtins
        // as well as this/E, etc.
        Set<String> modelSigNames = new HashSet<String>();
        Set<String> modelFieldNames = new HashSet<String>();
        for (Sig s : modelWorld.getAllReachableSigs()) {
            if (!s.builtin)
                modelSigNames.add(alloyName(s.label));
            for (Sig.Field f : s.getFields()) {
                modelFieldNames.add(alloyName(f.label) + " of " + alloyName(s.label));
            }   
        }
        
        // read the XML file
        // do not rely on Alloy at all 
        // (i.e., do not read the XML as an A4Solution)
        // rather do the XML parsing ourselves
        Document doc = null;
        
        Set<String> xmlSigNames = new HashSet<String>();
        Set<String> xmlFieldNames = new HashSet<String>();
        NodeList sigs = null;
        NodeList fields = null;
        String univId = null;  // sigs that have this is parent are top-level sigs

        try {
            DocumentBuilderFactory factory = DocumentBuilderFactory.newInstance();
            DocumentBuilder builder = factory.newDocumentBuilder();
            doc = builder.parse(new File(xmlFullFileName));

            sigs = doc.getElementsByTagName("sig");

            // get all info about the sigs out of the XML
            // into a hashmap
            idToSigInfo = new HashMap<>();
            
            for (int i = 0; i < sigs.getLength(); i++) {
                Element sig = (Element) sigs.item(i);
                if (sig.getAttribute("label").equals(UNIV)) {
                        // top-level sigs have univ as parent in XML
                        // so we need to get the id of univ
                        univId = sig.getAttribute("ID");
                } else if (sig.getAttribute("label").equals("String") && sig.getElementsByTagName("atom").getLength() != 0) {
                    System.out.println("atoms of sig String are not supported");
                    System.exit(2);
                } else if (!sig.hasAttribute("builtin")) {
                    String label = alloyName(sig.getAttribute("label"));
                    // add to the list of all xml names
                    xmlSigNames.add(label);

                    String myId = sig.getAttribute("ID");
                    
                    // everything except univ has a parent id
                    String parentId = sig.getAttribute("parentID");
                    if (parentId.equals("")) parentId = SUBSET;
                    boolean isAbstract = 
                        sig.hasAttribute("abstract") ? 
                            sig.getAttribute("abstract").equals("yes") : 
                            false; 
        
                    List<String> atomList = new ArrayList<String>();
                    NodeList atoms = sig.getElementsByTagName("atom");
                    for (int j = 0; j < atoms.getLength(); j++) {
                            Element atom = (Element) atoms.item(j);
                            String atomLabel = atom.getAttribute("label");
                            atomList.add(alloyName(atomLabel));
                    }

                    idToSigInfo.put(myId, 
                        new SigInfo(label, myId, parentId, isAbstract, atomList));
                }

            }
            
           
            // in the hash map turn parent pointers into child pointers
            // so we can collect the descendants later
            String idOfParent;
            for (String id: idToSigInfo.keySet()) {
                if (!idToSigInfo.get(id).parentId.equals(univId) && !idToSigInfo.get(id).parentId.equals(SUBSET)) {
                    idOfParent = idToSigInfo.get(id).parentId;
                    idToSigInfo.get(idOfParent).addChild(id);
                }
            }

            // this just collects the field names
            // from the XML
            // right now, there does not seem to be a reason
            // to keep field info separately from the XML
            // data structures
            fields = doc.getElementsByTagName("field");
            for (int i = 0; i < fields.getLength(); i++) {
                Element field = (Element) fields.item(i);
                String label = field.getAttribute("label");
                String parentId = field.getAttribute("parentID");
                xmlFieldNames.add(alloyName(label)+" of " + idToSigInfo.get(parentId).label);
            }

        } catch (Exception e) {
            System.out.println("FAIL: Reading "+xmlFullFileName +" failed with\n" + e.getMessage());
            e.printStackTrace();
            System.exit(2);
        }

        // check the modelNames subseteq of xmlNames
        // the problem of names used in the XML that are not used in the model
        // will be caught in the Alloy solving below
        // but if the model contains names not used in the XML, the solver will 
        // provide values for them
        if (!xmlSigNames.containsAll(modelSigNames)) {
            System.out.println("FAIL: Model has sigs not in XML:");
            modelSigNames.removeAll(xmlSigNames);
            System.out.println(modelSigNames);   
            System.exit(2);
        }
        if (!xmlFieldNames.containsAll(modelFieldNames)) {
            System.out.println("FAIL: Model has fields not in XML:");
            modelFieldNames.removeAll(xmlFieldNames);
            System.out.println(modelFieldNames);   
            System.exit(2);
        }

        // create a string that is one sigs 
        StringBuilder newSigs = new StringBuilder();
        // create a string that is facts that represent the instance in Alloy
        StringBuilder newFacts = new StringBuilder();
        
        for (String id:idToSigInfo.keySet()) {
            // no builtins will be in this map
            // produce nothing if it is an abstract sig
            if (!idToSigInfo.get(id).isAbstract ) {
                
                String sigLabel = idToSigInfo.get(id).label;
                
                List<String> atomsUniqueToSig = idToSigInfo.get(id).atoms;
                
                // could be none 
                for (String a: atomsUniqueToSig) {
                    // one sig atom_name extends immediateParentSig name {}
                    newSigs.append("\none sig "+ a + " extends "+ sigLabel + " {}");
                }
                
                List<String> allAtoms = collectAtoms(id); 
                // sig = a$1 + a$2 + ... 
                newFacts.append("\n    "+ sigLabel + " = "); 
                if (allAtoms.size() == 0) 
                    // sigs are always of unary arity
                    newFacts.append("none");
                else { 
                    newFacts.append(String.join("\n      + ", allAtoms) );
                }
                
            }
        }

        // add facts for the fields
        // we get this info straight from the XML
        Element field;
        String fieldLabel;
        String parentId;
        Integer arity;
        NodeList tuples;
        List<String> arrows;
        List<String> arrow;
        Element tuple;
        for (int i = 0; i < fields.getLength(); i++) {

            field = (Element) fields.item(i);
            fieldLabel = field.getAttribute("label");
            arity = getFieldArity(field);
            parentId = field.getAttribute("parentID");
            tuples = field.getElementsByTagName("tuple");
            arrows = new ArrayList<String>();
            
            if (tuples.getLength() == 0) {
                continue;
            } else {
                arrows = new ArrayList<String>();

                for (int k=0; k < tuples.getLength(); k++) {
                    tuple = (Element) tuples.item(k);
                    NodeList atoms = tuple.getElementsByTagName("atom");     
                    arrow = new ArrayList<String>();
                    // create a$1 -> b$2
                    for (int j=0; j < atoms.getLength(); j++) {
                        Element atom = (Element) atoms.item(j);
                        String atomLabel = atom.getAttribute("label");
                        arrow.add(alloyName(atomLabel));
                    }
                    arrows.add(String.join(" -> ", arrow));
                }

                // f_name = a$1 -> b$2 + a$2 -> b$3 + ...
                newFacts.append("\n    "+idToSigInfo.get(parentId).label+"<:"+alloyName(fieldLabel) +" = ");
                newFacts.append(String.join("\n       + ", arrows));
            }        
        }

        // create a string that is the model plus the sigs and facts representing the instance
        StringBuilder checkerModel =  new StringBuilder(modelString); 
        checkerModel.append(newSigs);
        checkerModel.append("\n\nfact {"+newFacts+"\n}\n");

        // tack on the end of the model, the cmd that this XML is supposed to
        // satisfy and remember the cmd's number in satCmdNum
        // the cmd will tell us the scope
        NodeList inst = doc.getElementsByTagName("instance");
        if (inst.getLength() > 1) {
            System.out.println("FAIL: More than one instance in XML\n");
            System.exit(2);
        }
        Element x = (Element) inst.item(0);
        // this is hacky but works for our purposes
        // and gets the scope from the XML file
        String cmd = x.getAttribute("command");
        String bitwidth = x.getAttribute("bitwidth");
        
        checkerModel.append("\nrun {} for "+bitwidth+" Int\n");
        System.out.println(checkerModel.toString());
        A4Solution sol = null;
        try {
            // check if checkerModel is Sat
            // parsing or solve will fail if xml has names that model does not
            CompModule checkerModelWorld = CompUtil.parseEverything_fromString(rep, checkerModel.toString());
            // the following will be the run cmd that we just added (so an earlier cmd in the model is irrelevant)
            int satCmdNum = checkerModelWorld.getAllCommands().size() - 1;
            // this is the only place we do solving
            // hopefully it is quick because the instance is specific
            A4Options opt = new A4Options();
            sol = TranslateAlloyToKodkod.execute_command(rep, checkerModelWorld.getAllReachableSigs(), checkerModelWorld.getAllCommands().get(satCmdNum), opt);  
        } catch (Exception e) {
            System.out.println("FAIL: Solving checker model failed with\n" + e.getMessage());
            System.exit(2);
        }
        
        if (!sol.satisfiable()) {
            System.out.println("FAIL: checkerModel unsat");
            System.exit(1);
        } else {
            System.out.println("PASS: xml is instance of model");
            System.exit(0);
        }
    }

    static class SigInfo {

        // whether it is top-level or not is determined by having a
        // parent with the id of univId
        String label;
        String myId;
        String parentId;
        boolean isAbstract;
        List<String> atoms;
        List<String> children = new ArrayList<String>();

        SigInfo(
            String label, 
            String myId, 
            String parentId, 
            boolean isAbstract, 
            List<String> atoms) {
            this.label = alloyName(label);
            this.myId = myId;
            this.parentId = parentId;
            this.isAbstract = isAbstract;
            this.atoms = atoms;
        }

        void addChild(String child) {
            this.children.add(alloyName( child));
        }

    }

}
    
    



