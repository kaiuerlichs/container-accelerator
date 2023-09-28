import logging
from facade.ingress_controllers.aws_ingress_controller import AWSIngressController


logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)


def create_ingress_controller(ingress_type, cluster_name, region, vpc_id=None):
    """Creates and installs an ingress controller

    :param ingress_type: The type of ingress controller to create
    :param cluster_name: The name of the cluster to install into
    :param region: The AWS region the cluster is in
    :param vpc_id: The ID of the VPC the cluster is in, defaults to None
    """
    match ingress_type:
        case "aws":
            controller = AWSIngressController(
                cluster_name=cluster_name,
                region=region,
                vpc_id=vpc_id
            )
        case _:
            logger.error(f"Unknown ingress type {ingress_type}")
        
    controller.install()