import argparse


def load_args():
    parser = argparse.ArgumentParser(description="Kubernetes Primer")
    parser.add_argument("config_file", help="Path to config file")
    return parser.parse_args()