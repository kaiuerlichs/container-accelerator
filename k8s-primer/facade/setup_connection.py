import os
import subprocess
from kubernetes import config as k8s_config


def initialise_k8s_connection(cluster_name, region):
    current_path = os.getcwd()
    kubeconfig_path = os.path.join(current_path, 'kubeconfig')

    try:
        _generate_kubeconfig_file(cluster_name, region, kubeconfig_path)
        k8s_config.load_kube_config(config_file=kubeconfig_path)
    except Exception as e:
        raise RuntimeError(f"Failed to initialise k8s connection: {e}")


def _generate_kubeconfig_file(cluster_name, region, kubeconfig_path):
    command = f'aws eks update-kubeconfig --name {cluster_name} --region {region} --kubeconfig {kubeconfig_path}'
    subprocess.run(command, shell=True, check=True)
