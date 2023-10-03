import yaml
import logging
from util.args_util import load_args
from util.yaml_validator import validate_yaml
from facade.tf_gen import generate_tf_from_yaml

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] (tf_gen) %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

if __name__ == "__main__":
    args = load_args()

    try:
        with open(args.config_file, "r") as file:
            config = yaml.safe_load(file)
    except FileNotFoundError as e:
        logger.error(f"yaml_safe_load - File Not found - {e}")
        exit(1)

    try:
        config = validate_yaml(config)
    except ValueError as e:
        logger.error(f"validate_yaml - Invalid configuration file provided - {e}")
        exit(2)

    try:
        generate_tf_from_yaml(config)
    except Exception as e:
        logger.error(f"generate_tf_from_yaml - Invalid configuration file provided - {e}")
        exit(3)
