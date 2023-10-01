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


def get_bucket_names() -> list:
    s3 = boto3.client("s3")
    return list(map(lambda bucket: bucket["Name"], s3.list_buckets()["Buckets"]))


def get_dynamodb_tables() -> list:
    dynamodb = boto3.client("dynamodb")

    return dynamodb.list_tables()["TableNames"]


def get_table_partition_key(table_name: str) -> str:
    dynamodb = boto3.client("dynamodb")
    keys = filter(lambda key: (key["KeyType"] == "HASH"), dynamodb.describe_table(TableName=table_name)["Table"][
        "KeySchema"])
    key = list(map(lambda key: key["AttributeName"], keys))[0]
    return key
