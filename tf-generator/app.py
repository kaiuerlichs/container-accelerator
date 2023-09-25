import yaml
from util.yaml_validator import validate_yaml


with open("config.yml", "r") as file:
    config = yaml.safe_load(file)


try:
    config = validate_yaml(config)
except ValueError as e:
    print(e)
    exit(1)