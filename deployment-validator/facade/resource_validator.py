# Import necessary libraries
import boto3 as boto
import json
import logging
import requests
import subprocess
from botocore.exceptions import ClientError

# Function to create an EKS client

if logger is None:
    logger = logging.getLogger(__name__)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] (tf_gen - facade) %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

def create_eks_client():
    try:
        return boto.client('eks')
    except Exception as e:
        logger.warning("Failed to create EKS client:", str(e))
        return None


# Create the EKS client
eks = create_eks_client()

# If the EKS client is not created, log an error message
if eks is None:
    logger.warning("EKS client is not created. Please check your AWS credentials.")


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

# Function to check if a specified VPC exists and is available


def check_vpc(vpc_id):
    try:
        ec2 = boto.client('ec2')
        response = ec2.describe_vpcs(VpcIds=[vpc_id])

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

# Function to check if the specified subnets exist and are available


def check_subnets(subnet_ids):
    try:
        response = eks.describe_subnets(SubnetIds=subnet_ids)
        for subnet in response['Subnets']:
            if subnet['State'] != 'available':
                logger.warning(f"Subnet {subnet['SubnetId']} does not exist.")
                return False
        logger.info("All subnets exist.")
        return True
    except ClientError as e:
        logger.warning(f"An error occurred: {e}")
        return False

# Function to check if a specified Application Load Balancer (ALB) exists and is active


def check_alb(alb_arn):
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

# Function to check if a specified EKS cluster exists and is active


def check_eks(cluster_name):
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

# Function to chekck if the ALB  is up and running it sends out a ping and checks responds with 'pong'


def ping_alb(alb_dns_name):
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

# Function to check if you can successfully run a 'kubectl get nodes' command, indicating a working connection to the Kubernetes cluster


def check_k8s_connection():
    try:
        output = subprocess.check_output(["kubectl", "get", "nodes"])
        logger.info("Connection to Kubernetes cluster is working.")
        return True
    except subprocess.CalledProcessError as e:
        logger.warning(e.output,"")
        logger.warning("Connection to Kubernetes cluster is not working.")
        return False

# Function to all the validation checks
def run_validator():
    # Load resource information from JSON file
    resource_info = load_json_data("resource_info.json")

    # Check VPC
    vpc_id = resource_info.get("vpc_id")
    if vpc_id:
        if not check_vpc(vpc_id):
            return

    # Check Subnets
    subnet_ids = resource_info.get("subnet_ids")
    if subnet_ids:
        if not check_subnets(subnet_ids):
            return

    # Check ALB
    alb_arn = resource_info.get("alb_arn")
    if alb_arn:
        if not check_alb(alb_arn):
            return

    # Check EKS Cluster
    cluster_name = resource_info.get("cluster_name")
    if cluster_name:
        if not check_eks(cluster_name):
            return

    # Ping ALB
    alb_dns_name = resource_info.get("alb_dns_name")
    if alb_dns_name:
        if not ping_alb(alb_dns_name):
            return

    # Check K8s Connection
    if not check_k8s_connection():
        return

    # If all checks pass, log a success message
    logger.info("All resource validation checks passed.")
