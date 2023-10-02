import json
import logging

import yaml
import requests
from botocore.exceptions import ClientError

if logger is None:
    logger = logging.getLogger(__name__)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] (deployment_validator - facade/res_val_json) %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )


def load_json_data(file_name: str) -> dict:
    """
    Load JSON data from the file.
    :param file_name: file path of JSON
    :return: dictionary of the file
    """
    try:
        with open(file_name, "r") as json_file:
            return json.load(json_file)
    except FileNotFoundError as e:
        logger.error(f"load_json_data - File Not found - {e}")
        exit(1)


def load_availability_zones(file_name: str) -> dict:
    """
    Load availability zones from a YAML file.
    :param file_name: file path of YAML
    :return: dictionary of the file
    """
    try:
        with open(file_name, 'r') as yaml_file:
            return yaml.safe_load(yaml_file)
    except FileNotFoundError as e:
        logger.error(f"load_availability_zones - File Not found - {e}")
        exit(1)


def create_subnet_availability_zones(data: dict) -> dict:
    """
    Creating a dictionary to store subnet IDs as keys and their associated availability zones as values.
    :param data: loaded configuration file
    :return: list of AZs per subnet
    """
    subnet_availability_zones = {}
    for subnet in data['SUBNET']:
        if 'id' in subnet and 'availabilityZone' in subnet:
            subnet_id = subnet['id']
            availability_zone = subnet['availabilityZone']
            subnet_availability_zones[subnet_id] = availability_zone
    return subnet_availability_zones


def check_vpc(data: dict):
    """
    Check if a VPC exists and its state.
    :param data: loaded configuration file
    """
    if 'VPC' in data:
        vpc = data['VPC']
        if 'id' in vpc and 'state' in vpc:
            vpc_id = vpc['id']
            state = vpc['state']
            logger.info(f"check_vpc - VPC with ID {vpc_id} is {state}")
        else:
            logger.warning("check_vpc - VPC is missing ID or state")
    else:
        logger.error("check_vpc - VPC does not exist")


def check_subnet(json_file: dict):
    """
    Check if a SUBNET exists and its state
    :param json_file: loaded configuration file
    """
    if 'SUBNET' in json_file:
        subnets = json_file['SUBNET']
        for subnet in subnets:
            if 'id' in subnet and 'state' in subnet:
                subnet_id = subnet['id']
                state = subnet['state']
                logger.info(f"check_subnet - SUBNET with ID {subnet_id} is {state}")
            else:
                logger.warning(f"check_subnet - SUBNET is missing ID or state")
    else:
        logger.error(f"check_subnet - SUBNET does not exist")


def check_alb(json_file: dict):
    """
    Check if an ALB exists and its state
    :param json_file: loaded configuration file
    """
    if 'ALB' in json_file:
        alb = json_file['ALB']
        if 'id' in alb and 'state' in alb:
            alb_id = alb['id']
            state = alb['state']
            logger.info(f"check_alb - ALB with ID {alb_id} is {state}")
        else:
            logger.warning(f"check_alb - ALB is missing ID or state")
    else:
        logger.error(f"check_alb - ALB does not exist")


def check_eks(json_file: dict):
    """
    Check if an EKS exists and its state
    :param json_file: loaded configuration file
    """
    if 'EKS' in json_file:
        eks = json_file['EKS']
        if 'id' in eks and 'state' in eks:
            eks_id = eks['id']
            state = eks['state']
            logger.info(f"check_eks - EKS with ID {eks_id} is {state}")
        else:
            logger.warning(f"check_eks - EKS is missing ID or state")
    else:
        logger.error(f"check_eks - EKS does not exist")


# TODO: I believe this check happens the wrong way around, it should be 2 subnets per AZ - AM 29/09/23
def check_subnet_availability_zones(subnet_availability_zones: dict):
    """
    Check if each subnet has two availability zones
    :param subnet_availability_zones: Dict of the availability zones
    :return:
    """
    for subnet_id, zones in subnet_availability_zones.items():
        if len(zones) != 2:
            logger.warning(f"check_subnet_availability_zones - Subnet {subnet_id} does not have exactly two "
                           f"availability zones: {zones}")


def ping_alb(alb_dns_name: str) -> bool:
    """
    Trigger ping checks to the ALB controller
    :param alb_dns_name: DNS name for the ALB Controller
    :return: Boolean for pass fail
    """
    try:
        response = requests.get(url='http://' + alb_dns_name + '/ping', timeout=(15,))
        if response.text == 'pong':
            logger.info(f"ping_alb - ALB {alb_dns_name} is responding to pings.")
            return True
        else:
            logger.warning(f"ping_alb - ALB {alb_dns_name} is not responding to pings.")
            return False
    except ClientError as e:
        logger.error(f"ping_alb - Client Error - {e}")
        return False
