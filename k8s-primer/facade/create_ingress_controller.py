from facade.ingress_controllers.aws_ingress_controller import AWSIngressController


def create_ingress_controller(ingress_type, cluster_name, region, vpc_id=None):
    match ingress_type:
        case "aws":
            controller = AWSIngressController(
                cluster_name=cluster_name,
                region=region,
                vpc_id=vpc_id
            )
        case _:
            raise ValueError(f"Unknown ingress type: {ingress_type}")
        
    controller.install()