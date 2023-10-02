import ipaddress

from constants.defaults import DEFAULT_CIDR_BLOCK, VALID_EKS_VERSIONS, VALID_INGRESS_TYPES
from util.aws import get_aws_regions, get_aws_availability_zones, get_aws_instance_types, get_dynamodb_tables, \
    get_bucket_names, get_table_partition_key


def validate_yaml(config: dict):
    """
    Validates yaml config file against schema
    :param config: dictionary from yaml
    :return: config with default values
    """

    # Validate AWS region
    if "aws_region" not in config or config["aws_region"] == "":
        raise ValueError("Field aws_region is required")
    if config["aws_region"] not in get_aws_regions():
        raise ValueError(f"{config['aws_region']} is not a valid AWS region")
    # Validate backend bucket name
    if "bucket_name" not in config or config["bucket_name"] == "":
        raise ValueError("Field bucket_name is required")
    elif config["bucket_name"] not in get_bucket_names():
        raise ValueError(
            f"{config['bucket_name']} is not a valid bucket name. You must create the bucket before running this program"
        )

    # Validate dynamodb name
    if "dynamodb_table_name" not in config or config["dynamodb_table_name"] == "":
        raise ValueError("Field dynamodb_table_name is required")
    elif config["dynamodb_table_name"] not in get_dynamodb_tables():
        raise ValueError(
            f"{config['dynamodb_table_name']} is not a valid DynamoDB name. You must create the table before running this program"
        )
    elif get_table_partition_key(config["dynamodb_table_name"]) != "LockID":
        raise KeyError(
            f"{config['dynamodb_table_name']} does not have the field 'LockID'. You must create this partition key in the table before running this program")
    # Validate CIDR block
    if "cidr_block" not in config or config["cidr_block"] == "":
        config["cidr_block"] = DEFAULT_CIDR_BLOCK
    try:
        ipaddress.ip_network(config["cidr_block"])
    except ValueError:
        raise ValueError(f"{config['cidr_block']} is not a valid CIDR block")

    # Validate availability zones
    if "availability_zones" not in config or \
            config["availability_zones"] == "" or \
            config["availability_zones"] == []:
        config["availability_zones"] = get_aws_availability_zones(config["aws_region"])
    else:
        valid_zones = get_aws_availability_zones(config["aws_region"])
        for zone in config["availability_zones"]:
            if zone not in valid_zones:
                raise ValueError(f"{zone} is not a valid availability zone")

    # Validate cluster name
    if "cluster_name" not in config or config["cluster_name"] == "":
        raise ValueError("Field cluster_name is required")

    # Validate eks version
    if "eks_version" not in config or config["eks_version"] == "":
        config["eks_version"] = "1.27"
    config["eks_version"] = str(config["eks_version"])
    if config["eks_version"] not in VALID_EKS_VERSIONS:
        raise ValueError(f"{config['eks_version']} is not a valid EKS version")

    # Validate fargate flag
    if "fargate" not in config or config["fargate"] == "":
        config["fargate"] = False

    # Validate cluster namespaces
    if "cluster_namespaces" not in config or \
            config["cluster_namespaces"] == "" or \
            config["cluster_namespaces"] == []:
        config["cluster_namespaces"] = ["kube-system"]

    # Validate ingress type
    if "ingress_type" not in config or config["ingress_type"] == "":
        config["ingress_type"] = "alb"
    if config["ingress_type"] not in VALID_INGRESS_TYPES:
        raise ValueError(f"{config['ingress_type']} is not a valid ingress controller type")

    # Check node groups exist
    if config["fargate"] is False and \
            "node_groups" not in config or \
            config["node_groups"] == "" or \
            config["node_groups"] == []:
        raise ValueError("Field node_groups is required in non-fargate clusters")

    valid_instance_types = get_aws_instance_types(config["aws_region"])
    # Validate each node group
    for group in config["node_groups"]:
        if "name" not in group or group["name"] == "":
            raise ValueError("Field name is required in node_groups")
        if "instance_type" not in group or group["instance_type"] == "":
            raise ValueError("Field instance_type is required in node_groups")
        if "min_size" not in group or group["min_size"] == "":
            raise ValueError("Field min_size is required in node_groups")
        if "max_size" not in group or group["max_size"] == "":
            raise ValueError("Field max_size is required in node_groups")

        # Validate numbers
        if not isinstance(group["min_size"], int):
            raise ValueError(f"{group['min_size']} is not a valid number")
        if not isinstance(group["max_size"], int):
            raise ValueError(f"{group['max_size']} is not a valid number")

        # Validate node group min and max sizes
        if group["min_size"] < 1 or group["min_size"] > group["max_size"]:
            raise ValueError(f"min_size must be between 1 and max_size")
        if group["max_size"] < group["min_size"]:
            raise ValueError(f"max_size must be greater than min_size")

        # Validate desired capacity
        if "desired_capacity" in group:
            if not isinstance(group["desired_capacity"], int):
                raise ValueError(f"{group['desired_capacity']} is not a valid number")
            elif group["desired_capacity"] < group["min_size"] or \
                    group["desired_capacity"] > group["max_size"]:
                raise ValueError(f"desired_capacity must be between min_size and max_size")

        # Validate instance type
        if group["instance_type"] not in valid_instance_types:
            raise ValueError(f"{group['instance_type']} is not a valid instance type")

    # Validate public ingress
    if "enable_public_ingress" not in config or config["enable_public_ingress"] == "":
        config["enable_public_ingress"] = False
    if "ingress_from_port" not in config or config["ingress_from_port"] == "":
        config["ingress_from_port"] = 80
    if not isinstance(config["ingress_from_port"], int):
        raise ValueError(f"{config['ingress_from_port']} is not a valid ingress to port number")
    if "ingress_to_port" not in config or config["ingress_to_port"] == "":
        config["ingress_to_port"] = 80
    if not isinstance(config["ingress_to_port"], int):
        raise ValueError(f"{config['ingress_to_port']} is not a valid ingress from port number")
    if "ingress_protocol" not in config or config["ingress_protocol"] == "":
        config["ingress_protocol"] = "tcp"

    # Validate tagging
    if "resource_owner" not in config or config["resource_owner"] == "":
        raise ValueError("Tag resource_owner is required")
    if "environment" not in config or config["environment"] == "":
        config["environment"] = "dev"

    # Validate additional tags
    for tag in config["additional_tags"]:
        if "key" not in tag or tag["key"] == "" or "value" not in tag or tag["value"] == "":
            raise ValueError("Additional tags must have a key and value")
