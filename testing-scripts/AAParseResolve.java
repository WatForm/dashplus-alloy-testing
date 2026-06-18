
import edu.mit.csail.sdg.alloy4.Err;
import edu.mit.csail.sdg.alloy4.ErrorSyntax;
import edu.mit.csail.sdg.alloy4.ErrorType;
import edu.mit.csail.sdg.parser.CompUtil;
import edu.mit.csail.sdg.parser.CompModule;

import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;

public class AAParseResolve {

    // must be in sync with python and Java for running dashplus

    static Integer SUCCESS = 0;
    // cannot be separated from resolving phase in AA
    //static Integer PARSE_ERROR = 1;
    static Integer RESOLVE_ERROR = 2;
    static Integer OTHER_ERROR = 3;

    public static void main(String[] args) throws Exception {
        try {
            // the following does not work for parse only
            // Module world = CompUtil.parse(new A4Reporter(), fileName);
            CompModule world =
                CompUtil.parseEverything_fromFile(null, null, args[0]);
            if (world == null) {
                System.err.println("Is file empty?");
                System.exit(OTHER_ERROR);
            } else {
                System.out.println("AA successfully parsed and resolved.");
                System.exit(SUCCESS);
            }
        } catch (ErrorSyntax e) {
            // these don't match DP's PARSE_ERROR 
            // an AA ErrorSyntax may include a 'missing symbol' kind of e
            System.err.println(e);
            System.exit(RESOLVE_ERROR);   
        } catch (ErrorType e) {
            System.err.println(e);
            System.exit(RESOLVE_ERROR);
        } catch (Err e) {
            System.err.println(e);
            System.exit(OTHER_ERROR);
        } catch (Exception e) {
            System.err.println(e.getMessage());
            System.exit(OTHER_ERROR);
        }
        
    }
}

