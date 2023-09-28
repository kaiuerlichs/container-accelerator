import yaml
import logging
from facade.create_ingress_controller import create_ingress_controller
from facade.setup_connection import initialise_k8s_connection
from facade.create_namespaces import create_namespaces
from utils.args_util import load_args


logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    filename="run.log"
)


args = load_args()

with open(args.config_file, "r") as file:
    config = yaml.safe_load(file)

initialise_k8s_connection(config["cluster_name"], config["aws_region"])
create_namespaces(config["cluster_namespaces"])
create_ingress_controller(config["ingress_type"], config["cluster_name"], config["aws_region"])
