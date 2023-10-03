import argparse
import logging


logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] (k8s-primer) %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)


def load_args():
    """Defines and loads the command-line arguments for the application

    :return: The args object
    """
    parser = argparse.ArgumentParser(description="Deployment validator")
    parser.add_argument("output_file", help="Path to terraform output file")
    return parser.parse_args()