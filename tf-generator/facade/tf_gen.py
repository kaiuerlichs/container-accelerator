import ipaddress
import math
import os

from constants.defaults import DEFAULT_CIDR_BLOCK
from util.aws import get_aws_availability_zones, get_aws_roles
from util.tf_string_builder import TFStringBuilder

_steps_registry = [
    "_generate_tf_header",
    "_generate_aws_provider",
    "_generate_eks_modules",
    "_generate_ingress_controller_resources",
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
    _output_to_tf_file(output_buffer, config["aws_region"])


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
    eks_config["tags"] = _get_tags(config)

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
    # Generate output block for EKS cluster name
    output_eks_cluster_name = TFStringBuilder.generate_output("eks_cluster_name", eks_config["cluster_name"],
                                                              description="EKS Cluster Name")

    # Generate output block for EKS cluster state (assuming you have a state variable)
    eks_cluster_state = "active"  # You need to obtain the actual state
    output_eks_cluster_state = TFStringBuilder.generate_output("eks_cluster_state", eks_cluster_state,
                                                               description="EKS Cluster State")

    output = output_eks_cluster_name
    output += TFStringBuilder.generate_module("eks", source, version, eks_config)
def _generate_k8s_namespaces(config):
    cluster_datapoint_config = {
        "name": ("module.eks.cluster_name", "ref"),
        "tags": _get_tags(config)
    }
    k8s_provider_config = {
        "host": ("data.eks_cluster.cluster.endpoint", "ref"),
        "cluster_ca_certificate": ("base64decode(data.eks_cluster.cluster.certificate_authority.0.data)", "ref"),
        "tags": _get_tags(config)
    }
    k8s_ns_configs = [{"metadata": {"name": ns}} for ns in config["cluster_namespaces"]]

    output = ""
    output += TFStringBuilder.generate_data("eks_cluster", "cluster", cluster_datapoint_config)
    output += TFStringBuilder.generate_provider("kubernetes", k8s_provider_config)

    for ns_config in k8s_ns_configs:
        output += TFStringBuilder.generate_resource("kubernetes_namespace", ns_config["metadata"]["name"], ns_config)

    return output


def _generate_ingress_controller_resources(config):
    match config["ingress_type"]:
        case "aws":
            # Resources are created through k8s API at later stage
            return ""
        case _:
            return ""


def _generate_vpc_resource(config):
    """
    Method for generating a vpc object
    :param config: Dictionary representation of  config file
    :return: Dictionary of the vpc's config options
    """
    vpc_config = {
        "cidr_block": str(config["cidr_block"]) if "cidr_block" in config else DEFAULT_CIDR_BLOCK
    }

    output = TFStringBuilder.generate_output("vpc_id", f"aws_vpc.vpc_{config['aws_region']}.id", description="VPC ID")
    output += TFStringBuilder.generate_output("vpc_state", f"aws_vpc.vpc_{config['aws_region']}.state",
                                              description="VPC State")

    return output + TFStringBuilder.generate_resource("aws_vpc", f"vpc_{config['aws_region']}", vpc_config)


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
            "vpc_id": (f"aws_vpc.vpc_{config['aws_region']}.id", "ref"),
            "tags": _get_tags(config)
        }

        # Add the first subnet to the list of subnets
        subnets.append(subnet1_config)

        sub_net2_base_address = _generate_base_address(sub_network_index + 1, network, num_modifiable_bits,
                                                       network_as_int)

        subnet_2 = f"{ipaddress.ip_address(sub_net2_base_address)}/{subnet_net_mask}"

        subnet2_config = {
            "cidr_block": subnet_2,
            "availability_zone": availability_zone,
            "vpc_id": (f"aws_vpc.vpc_{config['aws_region']}.id", "ref"),
            "tags": _get_tags(config)
        }

        subnets.append(subnet2_config)

    builder = ""
    for i, subnet in enumerate(subnets):
        builder += TFStringBuilder.generate_resource("aws_subnet",
                                                     f"subnet_{i % 2}_{subnet['availability_zone']}", subnet)
        subnet_index = i
        output_subnet_id = TFStringBuilder.generate_output(f"subnet_{subnet_index}_id",
                                                           f"aws_subnet.subne{subnet_index}.id",
                                                           description=f"Subnet {subnet_index} ID")
        builder += output_subnet_id

        # Add output block for subnet state
        output_subnet_state = TFStringBuilder.generate_output(f"subnet_{subnet_index}_state",
                                                              f"aws_subnet.subnet_{subnet_index}.state",
                                                              description=f"Subnet {subnet_index} State")
        builder += output_subnet_state

        # Add output block for availability zone
        output_availability_zone = TFStringBuilder.generate_output(f"subnet_{subnet_index}_availability_zone",
                                                                   subnet['availability_zone'],
                                                                   description=f"Subnet {subnet_index} Availability Zone")
        builder += output_availability_zone
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
    roles = get_aws_roles()
    for role in roles:
        admin_exists |= (role.RoleName == role_name_admin)
        dev_exists |= (role.RoleName == role_name_dev)

    output = ""

    # Generate the policy documents for Administrator, Developer, and Service account
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
    output += TFStringBuilder.generate_data("aws_iam_policy_document", "cluster_policy_doc_assume_role", {
        "statement": {
            "actions": ["sts:AssumeRole"],
            "effect": "Allow"
        }
    })

    # Generate the Policies for the roles
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

    # If either of the roles already exist, add the policy to the existing role, otherwise create a new role
    if not admin_exists:
        output += TFStringBuilder.generate_resource("aws_iam_role", "ca_cluster_admin_role", {
            "name": role_name_admin,
            "managed_policy_arns": [("aws_iam_policy.ca_cluster_admin_policy.arn", "ref")],
            "assume_role_policy": ("data.aws_iam_policy_document.cluster_policy_doc_assume_role.json", "ref")
        })
    else:
        output += TFStringBuilder.generate_resource("aws_iam_policy_attachment",
                                                    "ca_cluster_admin_role_attach", {
                                                        "name": "cluster admin role",
                                                        "roles": [(role_name_admin, "ref")],
                                                        "policy_arn":
                                                            ("aws_iam_policy.ca_cluster_admin_policy.arn", "ref")
                                                    })
    if not dev_exists:
        output += TFStringBuilder.generate_resource("aws_iam_role", "ca_cluster_dev_role", {
            "name": role_name_dev,
            "managed_policy_arns": [("aws_iam_policy.ca_cluster_dev_policy.arn", "ref")],
            "assume_role_policy": ("data.aws_iam_policy_document.cluster_policy_doc_assume_role.json", "ref")
        })
    else:
        output += TFStringBuilder.generate_resource("aws_iam_policy_attachment",
                                                    "ca_cluster_admin_role_attach", {
                                                        "name": "cluster dev role",
                                                        "roles": [(role_name_dev, "ref")],
                                                        "policy_arn":
                                                            ("aws_iam_policy.ca_cluster_dev_policy.arn", "ref")
                                                    })
    return output


def _generate_aws_provider(config: dict) -> str:
    """
    Generate the AWS Provider Block
    :param config: YAML Config dict
    :return: Block of Provider
    """
    return TFStringBuilder.generate_provider("aws", {
        "access_key": os.environ.get(config['access_token_env_key'], "ACCESS_TOKEN"),
        "secret_key": os.environ.get(config['secret_token_env_key'], "SECRET_TOKEN"),
        "region": config['aws_region'],
        "assume_role": {
            "role_arn": config['administrator_iam_role_arn']
        } if config['administrator_iam_role_arn'] is not None else None
    })

def _output_to_tf_file(output_string, region_name):
    """
    Method for outputting the final string to a terraform file
    :param output_string: The string to output
    :param region_name: The region the infrastructure is deployed to
    """
    print("Writing output to file")
    if not os.path.exists(f"./{region_name}"):
        os.makedirs(f"./{region_name}")
    with open(f"./{region_name}/main.tf", "w+") as file:
        file.write(output_string)


def _get_tags(config):
    tags = {
        "resource_owner": config["resource_owner"],
        "environment": config["environment"] if "environment" in config else "dev",
    }

    for additional_tag in config["additional_tags"]:
        tags.update({additional_tag["key"]: additional_tag["value"]})

    return tags
