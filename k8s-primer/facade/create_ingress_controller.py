import logging
from facade.ingress_controllers.aws_ingress_controller import AWSIngressController


logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    filename="run.log"
)


def create_ingress_controller(ingress_type, cluster_name, region, vpc_id=None):
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