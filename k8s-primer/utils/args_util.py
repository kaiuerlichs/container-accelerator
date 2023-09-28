import argparse


def load_args():
    """Defines and loads the command-line arguments for the application

    :return: The args object
    """
    parser = argparse.ArgumentParser(description="Kubernetes Primer")
    parser.add_argument("config_file", help="Path to config file")
    return parser.parse_args()