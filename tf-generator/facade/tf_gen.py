import ipaddress
import math
import os

from constants.defaults import DEFAULT_CIDR_BLOCK
from util.aws import get_aws_availability_zones
from util.tf_string_builder import TFStringBuilder

_steps_registry = [
    "_generate_tf_header",
    "_generate_aws_provider",
    "_generate_eks_modules",
    "_generate_k8s_namespaces",
    "_generate_ingress_controller",
    "_generate_vpc_resource",
    "_generate_subnet_resources",
    "_generate_iam_roles"
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
            for group in config["node_groups"]
        }

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


def _generate_vpc_resource(config):
    """
    Method for generating a vpc object
    :param config: Dictionary representation of  config file
    :return: Dictionary of the vpc's config options
    """
    vpc_config = {
        "cidr_block": str(config["cidr_block"]) if "cidr_block" in config else DEFAULT_CIDR_BLOCK
    }

    return TFStringBuilder.generate_resource("aws_vpc", f"vpc_{config['aws_region']}", vpc_config)


def _generate_subnet_resources(config):
    """
    Method for generating all subnets within a vpc
    :param config: Dictionary representation of config file
    :return: A list of subnet config options
    """
    subnets = []
    network = ipaddress.ip_network(str(config["cidr_block"]) if "cidr_block" in config else DEFAULT_CIDR_BLOCK)
    availability_zones = []
    if "availability_zones" in config:
        availability_zones = config["availability_zones"]
    else:
        availability_zones = get_aws_availability_zones(config["aws_region"])

    # Calculate number of Addresses to allocate to each block (rounded to nearest power of 2)
    addresses_per_subnet = 2 ** math.floor(
        (math.log(network.num_addresses / (2 * len(availability_zones))) / math.log(2)))

    # Determine the minimum netmask to allocate that number of addresses
    subnet_net_mask \
        = int(32 - math.log2(addresses_per_subnet))

    # Difference between new masks and old masks
    num_modifiable_bits = int(subnet_net_mask - network.prefixlen)

    # Convert the address to an integer for calculations of subnets
    network_as_int = int(network.network_address)

    for i, availability_zone in enumerate(availability_zones):
        # Each AZ is assigned 2 subnets, i * 2 and i * 2 + 1
        sub_network_index = i * 2

        # Calculate the new base address from the index and the original address
        sub_net1_base_address = _generate_base_address(sub_network_index, network, num_modifiable_bits,
                                                       network_as_int)

        # Convert the new address into a string, appending the netmask
        subnet_1 = f"{ipaddress.ip_address(sub_net1_base_address)}/{subnet_net_mask}"

        # Create a config object for the first subnet
        subnet1_config = {
            "cidr_block": subnet_1,
            "availability_zone": availability_zone,
            "vpc_id": (f"aws_vpc.vpc_{config['aws_region']}.id", "ref")
        }

        # Add the first subnet to the list of subnets
        subnets.append(subnet1_config)

        sub_net2_base_address = _generate_base_address(sub_network_index + 1, network, num_modifiable_bits,
                                                       network_as_int)

        subnet_2 = f"{ipaddress.ip_address(sub_net2_base_address)}/{subnet_net_mask}"

        subnet2_config = {
            "cidr_block": subnet_2,
            "availability_zone": availability_zone,
            "vpc_id": (f"aws_vpc.vpc_{config['aws_region']}.id", "ref")
        }

        subnets.append(subnet2_config)

    builder = ""
    for i, subnet in enumerate(subnets):
        builder += TFStringBuilder.generate_resource("aws_subnet",
                                                     f"subnet_{i % 2}_{subnet['availability_zone']}", subnet)
    return builder


def _generate_base_address(sub_network_index, network, num_modifiable_bits, network_as_int):
    """
    :param sub_network_index: The index of which subnet is being generated
    :param network: The IP network object for the VPC network
    :param num_modifiable_bits: The number of modifiable bits available for subnet generation
    :param network_as_int: The network address of the VPC as an integer
    :return: The base address of the new subnet
    """
    return ((sub_network_index << (network.prefixlen - int(num_modifiable_bits))) |
            network_as_int)


def _generate_iam_roles(config: dict) -> str:
    """
    Generate the required blocks for 2 IAM roles that can interact with the generated EKS cluster
    :param config: YAML Config dict
    :return: Blocks of IAM roles
    """
    output = ""
    output += TFStringBuilder.generate_data("aws_iam_policy_document", "cluster_admin_policy_doc", {
        "statement": {
            "actions": ["eks:*"],
            "resources": [("aws_eks_cluster.cluster.arn", "ref")],
            "effect": "Allow"
        }
    })
    output += TFStringBuilder.generate_data("aws_iam_policy_document", "cluster_dev_policy_doc", {
        "statement": {
            "actions": ["eks:AccessKubernetesApi"],
            "resources": [("aws_eks_cluster.cluster.arn", "ref")],
            "effect": "Allow"
        }
    })
    output += TFStringBuilder.generate_resource("aws_iam_policy", "ca_cluster_admin_policy", {
        "name": "cluster admin policy",
        "description": "All Access to Cluster",
        "policy": ("data.aws_iam_policy_document.cluster_admin_policy_doc.json", "ref")
    })
    output += TFStringBuilder.generate_resource("aws_iam_policy", "ca_cluster_dev_policy", {
        "name": "cluster dev policy",
        "description": "Access to K8s CLI for Cluster",
        "policy": ("data.aws_iam_policy_document.cluster_dev_policy_doc.json", "ref")
    })
    output += TFStringBuilder.generate_resource("aws_iam_role", "ca_cluster_admin_role", {
        "name": "cluster admin role",
        "managed_policy_arns": [("aws_iam_policy.ca_cluster_admin_policy.arn", "ref")]
    })
    output += TFStringBuilder.generate_resource("aws_iam_role", "ca_cluster_dev_role", {
        "name": "cluster dev role",
        "managed_policy_arns": [("aws_iam_policy.ca_cluster_dev_policy.arn", "ref")]
    })
    return output


def _generate_aws_provider(config: dict) -> str:
    """
    Generate the AWS Provider Block
    :param config: YAML Config dict
    :return: Block of Provider
    """
    return TFStringBuilder.generate_provider("aws", {
        "access_key": os.environ.get(config['access_token_key'], "ACCESS_TOKEN"),
        "secret_key": os.environ.get(config['secret_token_key'], "SECRET_TOKEN"),
        "region": config['aws_region'],
        "assume_role": {
            "role_arn": config['administrator_iam_role_arn']
        } if config['administrator_iam_role_arn'] is not None else None
    })
