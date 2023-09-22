from util.tf_string_builder import TFStringBuilder
import boto3

_steps_registry = [
    "_generate_tf_header",
    "_generate_eks_modules",
    "_generate_k8s_namespaces",
    "_generate_ingress_controller"
]


def generate_tf_from_yaml(config: dict) -> str:
    """
    Main Generation Method Called from entrypoint with the configuration as a dictionary.
    :param config: Dictionary of the configuration file
    :return: String containing the output configuration data
    """
    output_buffer = ""
    for step in _steps_registry:
        output_buffer += eval(f"{step}(config)")  # Execute each step in the registry passing the dictionary to each
    return output_buffer


def _generate_tf_header(config: dict) -> str:
    # TODO: Complete Method
    return ""


def _generate_eks_modules(config):
    source = "terraform-aws-modules/eks/aws"
    version = "19.16.0"

    eks_config = {}
    eks_config["cluster_name"] = config["cluster_name"]
    eks_config["cluster_version"] = str(config["eks_version"]) if "eks_version" in config else "1.27"
    eks_config["subnets"] = ("aws_subnet.private_subnet[*].id", "ref")
    eks_config["vpc_id"] = ("aws_vpc.vpc.id", "ref")

    if (not config["fargate"] if "fargate" in config else True):
        eks_config["eks_managed_node_groups"] = {
            group["name"]: {
                "min_size": group["min_size"],
                "max_size": group["max_size"],
                "desired_capacity": group["desired_capacity"],
                "instance_type": group["instance_type"],
                "name": group["name"]
            }
        for group in config["node_groups"]}

    else:
        eks_config["fargate_profiles"] = {
            "default": {
                "name": "default",
                "selectors": [{"namespace": ns} for ns in config["cluster_namespaces"]]
            }
        }

    return TFStringBuilder.generate_module("eks", source, version, eks_config)


def _generate_k8s_namespaces(config):
    cluster_datapoint_config = {
        "name": ("module.eks.cluster_name", "ref")
    }
    k8s_provider_config = {
        "host": ("data.eks_cluster.cluster.endpoint", "ref"),
        "cluster_ca_certificate": ("base64decode(data.eks_cluster.cluster.certificate_authority.0.data)", "ref")
    }
    k8s_ns_configs = [{"metadata": {"name": ns}} for ns in config["cluster_namespaces"]]

    output = ""
    output += TFStringBuilder.generate_data("eks_cluster", "cluster", cluster_datapoint_config)
    output += TFStringBuilder.generate_provider("kubernetes", k8s_provider_config)

    for ns_config in k8s_ns_configs:
        output += TFStringBuilder.generate_resource("kubernetes_namespace", ns_config["metadata"]["name"], ns_config)

    return output


def _generate_ingress_controller(config):
    match config["ingress_type"]:
        case "alb":
            return _generate_alb_ingress_controller(config)
        case _:
            return ""


def _generate_alb_ingress_controller(config):
    # Will be done in CA-39
    pass


# Facade to hold all the functions to generate terraform files

def _generate_vpc_resource(config):
    """
    Method for generating a vpc object
    :param config: Dictionary representation of  config file
    :return: Dictionary of the vpc's config options
    """
    vpc_config = {"cidr_block": str(config["cidr_block"]) if "cidr_block" in config else "10.0.0.0/16"}

    return vpc_config


def _generate_subnet_resources(config):
    """
    Method for generating all subnets within a vpc
    :param config: Dictionary representation of config file
    :return: A list of subnet config options
    """
    subnets = []
    if "availability_zones" in config:
        for availability_zone in config["availability_zones"]:
            subnet_config = {"cidr_block": "10.0.1.0/24", "availability_zone": availability_zone, "vpc_name": "main"}
            subnets.append(subnet_config)
    else:
        ec2_client = boto3.client("ec2", region_name=config["aws_region"])
        availability_zone_names = list(map(lambda az: az["ZoneName"],
                                           ec2_client.describe_availability_zones()["AvailabilityZones"]))
        for availability_zone in availability_zone_names:
            subnet_config = {"cidr_block": "10.0.1.0/24", "availability_zone": availability_zone}
    return subnets
