import ipaddress
import logging
import math
import os

from constants.defaults import DEFAULT_CIDR_BLOCK
from util.aws import get_aws_availability_zones, get_aws_roles
from util.tf_string_builder import TFStringBuilder

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] (tf_gen - facade) %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

_steps_registry = [
    "_generate_tf_header",
    "_generate_aws_provider",
    "_generate_eks_modules",
    "_generate_vpc_modules",
    "_generate_ingress_controller_resources",
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
        logger.info(f"generate_tf_from_yaml - On Step: {step}")
        output_buffer += eval(f"{step}(config)")  # Execute each step in the registry passing the dictionary to each
    _output_to_tf_file(output_buffer, config["aws_region"])


def _generate_tf_header(config: dict) -> str:
    """
    Generates the terraform configuration object
    :param config: Dictionary of the configuration file
    :return: String containing terraform configuration data
    """
    header_args = {
        "required_providers": (
            {
                "aws": {
                    "source": "hashicorp/aws",
                    "version": "~> 5.19.0"
                }
            },
            "header"),
        "backend \"s3\"": (
            {
                "bucket": config["bucket_name"],
                "key": "state/terraform.state",
                "region": config["aws_region"],
                "encrypt": "true",
                "dynamodb_table": config["dynamodb_table_name"]
            },
            "header")
    }
    return TFStringBuilder.generate_tf_header(header_args)


def _generate_eks_modules(config):
    source = "terraform-aws-modules/eks/aws"
    version = "19.16.0"

    eks_config = {}
    eks_config["cluster_name"] = config["cluster_name"]
    eks_config["cluster_version"] = str(config["eks_version"]) if "eks_version" in config else "1.28"
    eks_config["subnet_ids"] = ("module.vpc.private_subnets", "ref")
    eks_config["vpc_id"] = ("module.vpc.vpc_id", "ref")
    eks_config["tags"] = _get_tags(config)

    if not config["fargate"] if "fargate" in config else True:
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

    output_block = TFStringBuilder.generate_module("eks", source, version, eks_config)
    output_block += TFStringBuilder.generate_output("eks_cluster_name", "module.eks.cluster_name", description="EKS Cluster Name")
    output_block += TFStringBuilder.generate_output("eks_cluster_endpoint", "module.eks.cluster_endpoint", description="EKS Cluster Endpoint")

    return output_block


def _generate_ingress_controller_resources(config):
    match config["ingress_type"]:
        case "aws":
            # Resources are created through k8s API at later stage
            return ""
        case _:
            return ""


def _generate_vpc_modules(config):
    """
    Method for generating a vpc object
    :param config: Dictionary representation of  config file
    :return: Dictionary of the vpc's config options
    """
    source = "terraform-aws-modules/vpc/aws"
    version = "5.1.2"

    vpc_config = {}
    vpc_config["name"] = f"vpc-{config['cluster_name']}"
    vpc_config["cidr"] = str(config["cidr_block"]) if "cidr_block" in config else DEFAULT_CIDR_BLOCK
    vpc_config["azs"] = config["availability_zones"] if "availability_zones" in config else \
                        get_aws_availability_zones(config["aws_region"])
    subnet_cidr = _generate_subnet_cidrs(vpc_config["cidr"], vpc_config["azs"])
    vpc_config["private_subnets"] = subnet_cidr[::2]
    vpc_config["public_subnets"] = subnet_cidr[1::2]
    vpc_config["enable_nat_gateway"] = True

    vpc_config["private_subnet_tags"] = {
        '"kubernetes.io/role/internal-elb"': 1
    }
    vpc_config["public_subnet_tags"] = {
        '"kubernetes.io/role/elb"': 1
    }
    vpc_config["tags"] = _get_tags(config)

    output_block = TFStringBuilder.generate_module("vpc", source, version, vpc_config)
    output_block += TFStringBuilder.generate_output("vpc_id", "module.vpc.vpc_id", description="VPC ID")
    output_block += TFStringBuilder.generate_output("private_subnets", "module.vpc.private_subnets", description="Private subnets")
    output_block += TFStringBuilder.generate_output("public_subnets", "module.vpc.public_subnets", description="Public subnets")

    return output_block


def _generate_subnet_cidrs(cidr, azs):
    subnets = []
    network = ipaddress.ip_network(cidr)
    availability_zones = azs

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

    for i in range(len(availability_zones)*2):

        base_address = _generate_base_address(i, network, num_modifiable_bits,
                                                       network_as_int)
        cidr_block = f"{ipaddress.ip_address(base_address)}/{subnet_net_mask}"
        subnets.append(cidr_block)

    return subnets


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


def _get_tags(config):
    tags = {
        "resource_owner": config["resource_owner"],
        "environment": config["environment"] if "environment" in config else "dev",
    }

    for additional_tag in config["additional_tags"]:
        tags.update({additional_tag["key"]: additional_tag["value"]})

    return tags


def _generate_iam_roles(config: dict) -> str:
    """
    Generate the required blocks for 2 IAM roles that can interact with the generated EKS cluster
    :param config: YAML Config dict
    :return: Blocks of IAM roles
    """
    # Set the defaults for role names
    role_name_admin = config['ca_cluster_admin_role_name'] if config['ca_cluster_admin_role_name'] is not None else \
        "ca_cluster_admin"
    role_name_dev = config['ca_cluster_dev_role_name'] if config['ca_cluster_dev_role_name'] is not None else \
        "ca_cluster_dev"
    # Check if roles exist
    admin_exists = False
    dev_exists = False
    roles = get_aws_roles(region=config["aws_region"])
    for role in roles:
        admin_exists |= (role["RoleName"] == role_name_admin)
        dev_exists |= (role["RoleName"] == role_name_dev)

    # Generate the policy documents for Administrator, Developer, and Service account
    output_block = TFStringBuilder.generate_data("aws_iam_policy_document", "cluster_admin_policy_doc", {
        "statement": ({
                          "actions": ["eks:*"],
                          "resources": [("module.eks.cluster_arn", "ref")],
                          "effect": "Allow",
                      }, "header")
    })
    output_block += TFStringBuilder.generate_data("aws_iam_policy_document", "cluster_dev_policy_doc", {
        "statement": ({
                          "actions": ["eks:AccessKubernetesApi"],
                          "resources": [("module.eks.cluster_arn", "ref")],
                          "effect": "Allow",
                      }, "header")
    })
    output_block += TFStringBuilder.generate_data("aws_iam_policy_document", "cluster_policy_doc_assume_role", {
        "statement": ({
                          "actions": ["sts:AssumeRole"],
                          "effect": "Allow",
                          "principals": ({
                              "type": "AWS",
                              "identifiers": ["*"]
                          }, "header")
                      }, "header")
    })

    # Generate the Policies for the roles
    output_block += TFStringBuilder.generate_resource("aws_iam_policy", "ca_cluster_admin_policy", {
        "name": "cluster-admin-policy",
        "description": "All Access to Cluster",
        "policy": ("data.aws_iam_policy_document.cluster_admin_policy_doc.json", "ref"),
        "tags": _get_tags(config)
    })
    output_block += TFStringBuilder.generate_resource("aws_iam_policy", "ca_cluster_dev_policy", {
        "name": "cluster-dev-policy",
        "description": "Access to K8s CLI for Cluster",
        "policy": ("data.aws_iam_policy_document.cluster_dev_policy_doc.json", "ref"),
        "tags": _get_tags(config)
    })

    # If either of the roles already exist, add the policy to the existing role, otherwise create a new role
    if not admin_exists:
        output_block += TFStringBuilder.generate_resource("aws_iam_role", "ca_cluster_admin_role", {
            "name": role_name_admin,
            "managed_policy_arns": [("aws_iam_policy.ca_cluster_admin_policy.arn", "ref")],
            "assume_role_policy": ("data.aws_iam_policy_document.cluster_policy_doc_assume_role.json", "ref"),
            "tags": _get_tags(config)
        })
    else:
        output_block += TFStringBuilder.generate_resource("aws_iam_policy_attachment",
                                                    "ca_cluster_admin_role_attach", {
                                                        "name": "cluster admin role",
                                                        "roles": [role_name_admin],
                                                        "policy_arn":
                                                            ("aws_iam_policy.ca_cluster_admin_policy.arn", "ref"),
                                                        "tags": _get_tags(config)
                                                    })
    if not dev_exists:
        output_block += TFStringBuilder.generate_resource("aws_iam_role", "ca_cluster_dev_role", {
            "name": role_name_dev,
            "managed_policy_arns": [("aws_iam_policy.ca_cluster_dev_policy.arn", "ref")],
            "assume_role_policy": ("data.aws_iam_policy_document.cluster_policy_doc_assume_role.json", "ref"),
            "tags": _get_tags(config)
        })
    else:
        output_block += TFStringBuilder.generate_resource("aws_iam_policy_attachment",
                                                    "ca_cluster_dev_role_attach", {
                                                        "name": "cluster dev role",
                                                        "roles": [role_name_dev],
                                                        "policy_arn":
                                                            ("aws_iam_policy.ca_cluster_dev_policy.arn", "ref"),
                                                        "tags": _get_tags(config)
                                                    })
    
    return output_block


def _generate_aws_provider(config: dict) -> str:
    """
    Generate the AWS Provider Block
    :param config: YAML Config dict
    :return: Block of Provider
    """
    return TFStringBuilder.generate_provider("aws", {
        "region": config['aws_region']
    })


def _output_to_tf_file(output_string, region_name):
    """
    Method for outputting the final string to a terraform file
    :param output_string: The string to output
    :param region_name: The region the infrastructure is deployed to
    """
    logger.info("Writing output to file")
    if not os.path.exists(f"./terraform-files"):
        os.makedirs(f"./terraform-files")
    with open(f"./terraform-files/main.tf", "w+") as file:
        file.write(output_string)
