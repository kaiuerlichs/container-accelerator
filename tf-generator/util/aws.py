import boto3


def get_aws_regions():
    """
    Returns list of AWS regions
    :return: list of AWS regions
    """
    ec2 = boto3.client("ec2")
    regions = [region["RegionName"] for region in ec2.describe_regions()["Regions"]]
    return regions


def get_aws_availability_zones(region: str):
    """
    Returns list of AWS availability zones for a given region
    :param region: AWS region
    :return: list of AWS availability zones
    """
    ec2 = boto3.client("ec2")
    response = ec2.describe_availability_zones(Filters=[
        {
            'Name': 'region-name',
            'Values': [region]
        }
    ])
    zones = [zone["ZoneName"] for zone in response["AvailabilityZones"]]
    return zones


def get_aws_instance_types(region: str):
    """
    Returns list of AWS instance types
    :return: list of AWS instance types
    """
    ec2 = boto3.client("ec2")
    response = ec2.describe_instance_type_offerings(
        LocationType='region',
        Filters=[
            {
                'Name': 'location',
                'Values': [region]
            }
        ]
    )
    types = [type["InstanceType"] for type in response["InstanceTypeOfferings"]]
    return types


def get_aws_roles(prefix: str = None) -> dict:
    """
    Returns the list of roles that match the optional prefix.
    :param prefix: Optional prefix to search for
    :return: Dictionary of roles on the account
    """
    iam = boto3.client("iam")
    return iam.list_roles(PathPrefix=prefix).Roles
