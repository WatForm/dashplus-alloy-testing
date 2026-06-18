import static ca.uwaterloo.watform.parser.Parser.*;
import ca.uwaterloo.watform.alloyast.AlloyFile;
import ca.uwaterloo.watform.alloymodel.AlloyModel;
import ca.uwaterloo.watform.utils.*;
import ca.uwaterloo.watform.utils.Reporter;

import java.nio.file.Path;
import java.nio.file.Paths;
public class DPParseResolve {

    // must be in sync with python and Java for running aa

    static Integer SUCCESS = 0;
    static Integer PARSE_ERROR = 1;
    static Integer RESOLVE_ERROR = 2;
    static Integer OTHER_ERROR = 3;

    public static void main(String[] args) throws Exception {
        try {
        	Path path = Paths.get(args[0]);
            AlloyModel file = parseToModel(path.toAbsolutePath());
            System.out.println("DP successfully parsed and resolved.");
            System.exit(SUCCESS);
        } catch (Reporter.AbortSignal abortSignal) {
        	// this is what comes from parse if there is a
        	// parsing error
        	System.err.println("Parsing error");
        	System.exit(PARSE_ERROR);         
        } catch (UserError e) {
            // this is what comes from resolve if there is a
            // parsing error
            System.err.println("Resolving error");
            System.exit(RESOLVE_ERROR);   
        } catch (Exception e) {
        	System.err.println(e.getClass().getName());
        	System.err.println(e.getMessage());
            System.exit(OTHER_ERROR);
        }

        
    }
}