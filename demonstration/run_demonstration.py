from config.Environment import Environment
from scenarios.MdocMdlAamva import MdocMdlAamva
from scenarios.MdocMdlScenario import MdocMdlScenario
import argparse

# Get command line options...
parser = argparse.ArgumentParser("run_demonstration")
parser.add_argument("scenario", help="The type of scenario to use for the demonstration.", choices=['mdoc_mdl', 'mdoc_mdl_aamva'])
parser.add_argument("-i", "--issuance", help="Performs credential issuance between an issuer and holder over DIDComm for the specified format.", action="store_true", default=False)
parser.add_argument("-v", "--verification", help="Performs credential verification between a holder and verifier over DIDComm for the specified format.", action="store_true", default=False)
parser.add_argument("-d", "--deleteAgents", help="Wipes all agents and their associated data. If present, no other action is performed.", action="store_true", default=False)
args = parser.parse_args()

# Init environment
env = Environment()

# If neither issuance not verification flags were set, set both.
if (not args.issuance and not args.verification):
    args.issuance = True
    args.verification = True

# Based on command line options, choose scenario...
if (args.scenario == "mdoc_mdl"): 
    demonstration = MdocMdlScenario()
elif (args.scenario == "mdoc_mdl_aamva"):
    demonstration = MdocMdlAamva()


# Execute scenario
print(f"Running {args.scenario} demonstration with flags issuance={args.issuance} verification={args.verification} deleteAgents={args.deleteAgents}")
demonstration.execute(env, args.scenario, args.issuance, args.verification, args.deleteAgents)
