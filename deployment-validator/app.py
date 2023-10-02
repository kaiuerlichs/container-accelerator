import yaml
import logging

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] (deployment_validator) %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

if __name__ == "__main__":
    try:
        with open("config.yml", "r") as file:
            config = yaml.safe_load(file)
    except FileNotFoundError as e:
        logger.error(f"yaml_safe_load - File Not found - {e}")
        exit(1)