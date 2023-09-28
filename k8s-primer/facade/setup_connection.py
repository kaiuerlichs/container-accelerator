import os
import logging
import subprocess
from kubernetes import config as k8s_config


logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    filename="run.log"
)

def initialise_k8s_connection(cluster_name, region):
    """Initialises the connection to the k8s cluster

    :param cluster_name: The name of the cluster
    :param region: The AWS region the cluster is in
    """
    current_path = os.getcwd()
    kubeconfig_path = os.path.join(current_path, 'kubeconfig')

    try:
        _generate_kubeconfig_file(cluster_name, region, kubeconfig_path)
        k8s_config.load_kube_config(config_file=kubeconfig_path)
        logger.info("Kubeconfig loaded successfully")
        
    except Exception as e:
        logger.exception("Failed to load kubeconfig")
        quit(1)


def _generate_kubeconfig_file(cluster_name, region, kubeconfig_path):
    command = f'aws eks update-kubeconfig --name {cluster_name} --region {region} --kubeconfig {kubeconfig_path}'
    subprocess.run(command, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
