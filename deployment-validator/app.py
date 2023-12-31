import logging
from util.args_util import load_args
from facade.resource_validator import run_validator


logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] (deployment_validator) %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)


if __name__ == "__main__":
    args = load_args()
    run_validator(args.output_file, args.config_file)