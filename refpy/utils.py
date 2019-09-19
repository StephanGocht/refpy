import argparse
import logging
import parsy

from refpy import InvalidProof
from refpy import ParseError
from refpy.verifier import Verifier, Context
from refpy.parser import OPBParser
from refpy.rules import registered_rules
from refpy.parser import RuleParser
from refpy.exceptions import ParseError
from refpy.optimized.constraints import PropEngine
from refpy.constraints import defaultFactory
from time import perf_counter

profile = False

if profile:
    import cProfile

def run(formulaFile, rulesFile, settings = None):
    if profile:
        pr = cProfile.Profile()
        pr.enable()


    rules = list(registered_rules)

    start_parse = perf_counter()

    context = Context()

    try:
        formula = OPBParser().parse(formulaFile)
        numVars, numConstraints = formula[0]
        context.formula = formula[1]
    except ParseError as e:
        e.fileName = formulaFile.name
        raise e

    context.propEngine = PropEngine(numVars)
    context.ineqFactory =  defaultFactory

    try:
        rules = RuleParser().parse(rules, rulesFile)
    except ParseError as e:
        e.fileName = rulesFile.name
        raise e

    logging.info("Parsing Time: %.2f" % (perf_counter() - start_parse))
    verify = Verifier(settings, context)
    verify(rules)

    if profile:
        pr.disable()
        pr.print_stats()

def runUI(*args):
    try:
        run(*args)
    except InvalidProof as e:
        print("Verification failed.")
        hint = str(e)
        if len(hint) > 0:
            print("Hint: %s" %(str(e)))
        return 1
    except ParseError as e:
        logging.error(e)
        exit(1)
    except NotImplementedError as e:
        logging.error(e)
        exit(1)
    except Exception as e:
        if logging.getLogger().getEffectiveLevel() != logging.DEBUG:
            logging.error("Sorry, there was an internal error. Please rerun with debugging "
                "and make a bug report.")
            exit(1)
        else:
            print("Sorry, there was an internal error. Because you are runing in "
                "debug mod I will give you the exception.")
            raise e
    else:
        print("Verification succeeded.")
    return 0


def run_cmd_main():
    p = argparse.ArgumentParser(
        description = """Command line tool to verify derivation
            graphs. See Readme.md for a description of the file
            format.""")
    p.add_argument("formula", help="Formula containing axioms.", type=argparse.FileType('r'))
    p.add_argument("derivation", help="Refutation / Proof Log.", type=argparse.FileType('r'))
    p.add_argument(
        '-d', '--debug',
        help="Print lots of debugging statements.",
        action="store_const", dest="loglevel", const=logging.DEBUG,
        default=logging.INFO,
    )
    p.add_argument(
        '-v', '--verbose',
        help="Be verbose",
        action="store_const", dest="loglevel", const=logging.INFO,
    )

    Verifier.Settings.addArgParser(p)

    args = p.parse_args()

    verifyerSettings = Verifier.Settings.extract(args)

    logging.basicConfig(level=args.loglevel)

    return runUI(args.formula, args.derivation, verifyerSettings)
