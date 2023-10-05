# Import necessary libraries
import os
import boto3 as boto
import json
import yaml
import logging
import requests
import subprocess
from botocore.exceptions import ClientError

# Function to create an EKS client


logger = logging.getLogger(__name__)
logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] (tf_gen - facade) %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
)

def initalise_components(yaml_output: str):
    """
    Read the AWS region from the YAML file
    :param yaml_output: the YAML file
    :return: the AWS region name
    """
    try:
        file_path = os.path.join(os.getcwd(), yaml_output)
        with open(file_path, 'r') as yaml_file:
            config = yaml.safe_load(yaml_file)
        return config
    except Exception as e:
        raise Exception(f"An error occurred while reading the region from YAML: {e}")



def create_eks_client(region_name):
    """
    Create an EKS client
    :param region_name: the region name of the EKS cluster
    :return: the EKS client
    """
    try:
        return boto.client('eks',  region_name=region_name)
    except Exception as e:
        logger.warning("Failed to create EKS client:", str(e))
        return None


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

def check_vpc(vpc_id, region_name):
    """
    Check if a specified VPC exists and is available
    :param vpc_id: the VPC ID of cluster
    :return: true for successful or false for not successful
    """
    try:
        ec2 = boto.client('ec2', region_name=region_name)
        response = ec2.describe_vpcs(VpcIds=[vpc_id["value"]])

        if len(response['Vpcs']) == 1:
            vpc = response['Vpcs'][0]
            if vpc['State'] == 'available':
                logger.info(f"VPC {vpc_id} exists and is available.")
                return True
            else:
                logger.warning(f"VPC {vpc_id} exists but is not available.")
                return False
        else:
            logger.warning(f"VPC {vpc_id} does not exist.")
            return False
    except ClientError as e:
        logger.warning(f"An error occurred: {e}")
        return False


def check_subnets(subnet_ids):
    """
    Check if the specified subnets exist and are available
    :param subnet_ids: the subnet IDs of cluster
    :return: true for successful or false for not successful
    """
    try:
        response = eks.describe_subnets(SubnetIds=subnet_ids["value"])
        for subnet in response['Subnets']:
            if subnet['State'] != 'available':
                logger.warning(f"Subnet {subnet['SubnetId']} does not exist.")
                return False
        logger.info("All subnets exist.")
        return True
    except ClientError as e:
        logger.warning(f"An error occurred: {e}")
        return False

def check_alb(alb_arn):
    """
    Check if a specified Application Load Balancer (ALB) exists and is active
    :param alb_arn: the ALB ARN of cluster
    :return: true for successful or false for not successful
    """
    try:
        response = eks.describe_load_balancers(LoadBalancerArns=[alb_arn])
        if response['LoadBalancers'][0]['State']['Code'] == 'active':
            logger.info(f"ALB {alb_arn} exists.")
            return True
        else:
            logger.warning(f"ALB {alb_arn} does not exist.")
            return False
    except ClientError as e:
        logger.warning(f"An error occurred: {e}")
        return False


def check_eks(cluster_name):
    """
    Check if a specified EKS cluster exists and is active
    :param cluster_name: the name of the cluster
    :return: true for successful or false for not successful
    """
    try:
        response = eks.describe_cluster(name=cluster_name)
        if response['cluster']['status'] == 'ACTIVE':
            logger.info(f"EKS cluster {cluster_name} exists and is active.")
            return True
        else:
            logger.warning(
                f"EKS cluster {cluster_name} does not exist or is not active.")
            return False
    except ClientError as e:
        logger.warning(f"An error occurred: {e}")
        return False


def ping_alb(alb_dns_name):
    """
    Trigger ping checks to the ALB controller
    :param alb_dns_name: DNS name for the ALB Controller
    :return: Boolean for pass or fail
    """
    try:
        response = requests.get(
            url='http://' + alb_dns_name + '/ping', timeout=(15,))
        if response.text == 'pong':
            logger.info(f"ALB {alb_dns_name} is responding to pings.")
            return True
        else:
            logger.warning(f"ALB {alb_dns_name} is not responding to pings.")
            return False
    except ClientError as e:
        logger.warning(f"An error occurred: {e}")
        return False

def get_avaliablity_zones(aws_region_name,vpc_id):
     """
        Get each subnet as well as their avilability zones from the cluster then create a dictionary with each aviabilty zone as key and their respective subnets as values

        :param aws_region_name: the region name of the VPC
        :param vpc_id: the VPC ID of cluster
        :return: true for successful or false for not successful
        """
     ec2_client = boto.client('ec2', region_name=aws_region_name)

     subnet_response = ec2_client.describe_subnets(Filters=[{'Name': 'vpc-id', 'Values': [vpc_id]}])

    #get the subnet id as a key and the Availability zone as values then add them to a dictionary
     subnetId_and_azs = {}
     for subnet_info in subnet_response['Subnets']:
        subnet_id = subnet_info['SubnetId']
        availability_zone = subnet_info['AvailabilityZone']
        subnetId_and_azs[subnet_id] = availability_zone

     az_and_subnetId = {}

    #Create a new dictionary from the previous one, making the azs the key and the subnet the values and then return said dictionary
     for subnet_id, availability_zones in subnetId_and_azs.items():
        for az in availability_zones:
                if az not in az_and_subnetId:
                    az_and_subnetId[az] = []
                az_and_subnetId[az].append(subnet_id)

        return az_and_subnetId
     

def check_subnet_availability_zones(az_and_subnet, valid_az_list, public_subnet_ids, private_subnet_ids):
    """
    Check if the availability zones are valid and if each az has exactly 1 private
    and 1 public subnet
    :param az_and_subnet: the availability zones and their respective subnets
    :param valid_az_list: the list of valid AZs
    :param public_subnet_ids: the public subnet IDs
    :param private_subnet_ids: the private subnet IDs
    :return: true for successful or false for not successful
    """
    try:
        # Initialize a flag to track validation status
        is_valid = True

        # Iterate through each availability zone
        for az, subnet_ids in az_and_subnet.items():
            # Check if the availability zone is in the valid AZ list
            if az not in valid_az_list:
                logger.warning(f"Invalid AZ '{az}' found.")
                is_valid = False
                continue

            # Check if the number of subnets in this AZ is exactly 1 public and 1 private
            public_count = sum(1 for subnet_id in subnet_ids if subnet_id in public_subnet_ids)
            private_count = sum(1 for subnet_id in subnet_ids if subnet_id in private_subnet_ids)

            if public_count != 1 or private_count != 1:
                logger.warning(f"AZ '{az}' does not have exactly 1 public and 1 private subnet.")
                is_valid = False

        return is_valid

    except Exception as e:
        logger.warning(f"An error occurred: {e}")
        return False
   
def run_az_validator(json_file, config, vpc_id):

    """
    This function runs the necceary functions needed to validate if each availability zone
    has exactly 1 public and 1 private subnet
    :param json_file: the json file that contains the subnet ids
    :param yaml_file: the yaml file that contains the availability zones
    :param aws_region_name: the region name of the VPC
    :param vpc_id: the VPC ID of cluster
    
    """
    private_subnets=json_file["public_subnets"]["value"]
    public_subnets=json_file["public_subnets"]["value"]

    avaliablity_zones=config["availability_zones"]
    get_az_dict=get_avaliablity_zones(config["aws_region"], vpc_id)
    check_subnet_availability_zones(get_az_dict, avaliablity_zones, public_subnets, private_subnets)

    check_subnet_availability_zones(get_az_dict, avaliablity_zones, public_subnets, private_subnets )



def check_k8s_connection():
    """
    Check if you can successfully run a 'kubectl get nodes' command,
      indicating a working connection to the Kubernetes cluster
    :return: true for successful or false for not successful
    """
    try:
        output = subprocess.check_output(["kubectl", "get", "nodes"])
        logger.info("Connection to Kubernetes cluster is working.")
        return True
    except subprocess.CalledProcessError as e:
        logger.warning(e.output,"")
        logger.warning("Connection to Kubernetes cluster is not working.")
        return False


def run_validator(output_file: str,yaml_file: str):

    """
    Run all the validation checks
    :param output_file: the output file
    :return: true for successful or false for not successful

    """
    

# Create the EKS client
    initalise_components(yaml_file)
    config = initalise_components(yaml_file)
    global eks
    eks = create_eks_client(config["aws_region"])


# If the EKS client is not created, log an error message
    if eks is None:
        logger.warning("EKS client is not created. Please check your AWS credentials.")
    
    # Load resource information from JSON file
    resource_info = load_json_data(output_file)
    
    # Check VPC
    vpc_id = resource_info.get("vpc_id")
    if vpc_id:
        if not check_vpc(vpc_id, config["aws_region"]):
            quit(1)

    # Check Subnets
    subnet_ids = resource_info.get("subnet_ids")
    if subnet_ids:
        if not check_subnets(subnet_ids):
            quit(1)
        
    # Check Subnet Availability Zones
    if vpc_id:
        if not run_az_validator(resource_info, config, vpc_id):
            quit(1)
        
    # Check ALB
    alb_arn = resource_info.get("alb_arn")
    if alb_arn:
        if not check_alb(alb_arn):
            quit(1)

    # Check EKS Cluster
    cluster_name = resource_info.get("cluster_name")
    if cluster_name:
        if not check_eks(cluster_name):
            quit(1)

    # Ping ALB
    alb_dns_name = resource_info.get("alb_dns_name")
    if alb_dns_name:
        if not ping_alb(alb_dns_name):
            quit(1)

    # Check K8s Connection
    if not check_k8s_connection():
        quit(1)

    # If all checks pass, log a success message
    logger.info("All resource validation checks passed.")
