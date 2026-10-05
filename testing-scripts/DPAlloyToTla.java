
import static ca.uwaterloo.watform.alloytotla.AlloyToTlaCli.alloyToTlaDefaultOptions;
import ca.uwaterloo.watform.utils.*;
import ca.uwaterloo.watform.utils.Reporter;

import java.nio.file.Path;
import java.nio.file.Paths;

public class DPAlloyToTla{

    static Integer SUCCESS = 0;
    static Integer PARSE_ERROR = 1;
    static Integer RESOLVE_ERROR = 2;
    static Integer OTHER_ERROR = 3;

    public static void main(String[] args) throws Exception {
        try {
            Integer rc = alloyToTlaDefaultOptions(args[0]);
            if (rc == 0) {
                System.out.println("AlloyToTla successfully translated.");
                System.exit(SUCCESS);
            } else {
               System.exit(OTHER_ERROR); 
            }
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