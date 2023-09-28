import logging
from kubernetes import client as k8s_client


logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    filename="run.log"
)


def create_namespaces(namespaces_to_create: list):
    """Creates k8s namespaces in the cluster

    :param namespaces_to_create: List of namespaces to create
    """
    v1 = k8s_client.CoreV1Api()
    try:
        existing_namespaces = [item.metadata.name for item in v1.list_namespace().items]
    except Exception as e:
        logger.exception("Failed to retrieve existing namespaces")
        quit(1)
    
    for name in namespaces_to_create:
        if name in existing_namespaces:
            continue

        ns = k8s_client.V1Namespace(metadata=k8s_client.V1ObjectMeta(
            name=name, 
            labels={
                "name": name
            })
        )
        
        try:
            v1.create_namespace(ns)
            logger.info(f"Namespace {name} created successfully")
        except Exception as e:
            logger.exception(f"Failed to create namespace {name}")
            quit(1)
