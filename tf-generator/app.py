import yaml
import logging
from util.yaml_validator import validate_yaml
from facade.tf_gen import generate_tf_from_yaml

if __name__ == "__main__":
    try:
        with open("config.yml", "r") as file:
            config = yaml.safe_load(file)
    except FileNotFoundError as e:
        logging.error(f"yaml_safe_load - File Not found - {e}")
        exit(1)

    try:
        config = validate_yaml(config)
    except ValueError as e:
        logging.error(f"validate_yaml - Invalid configuration file provided - {e}")
        exit(2)

    try:
        generate_tf_from_yaml(config)
    except Exception as e:
        logging.error(f"generate_tf_from_yaml - Invalid configuration file provided - {e}")
        exit(3)
