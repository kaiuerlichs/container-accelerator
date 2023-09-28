import yaml
from facade.setup_connection import initialise_k8s_connection
from facade.create_namespaces import create_namespaces
from utils.args_util import load_args


args = load_args()

with open(args.config_file, "r") as file:
    config = yaml.safe_load(file)


initialise_k8s_connection(config["cluster_name"], config["aws_region"])
create_namespaces(config["cluster_namespaces"])
