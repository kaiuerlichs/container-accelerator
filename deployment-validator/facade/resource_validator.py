# Import necessary libraries
import os
import boto3 as boto
import json
import yaml
import logging
import requests
import subprocess
from botocore.exceptions import ClientError


logger = logging.getLogger(__name__)
logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] (tf_gen - facade) %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
)

def load_config(yaml_output: str):
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


def check_subnets(subnet_ids, config):
    """
    Check if the specified subnets exist and are available
    :param subnet_ids: the subnet IDs of cluster
    :return: true for successful or false for not successful
    """
    try:
        ec2 = boto.client('ec2', region_name=config["aws_region"])
        response = ec2.describe_subnets(SubnetIds=subnet_ids)
        for subnet in response['Subnets']:
            if subnet['State'] != 'available':
                logger.warning(f"Subnet {subnet['SubnetId']} does not exist.")
                return False
        logger.info("All subnets exist.")
        return True
    except ClientError as e:
        logger.warning(f"An error occurred: {e}")
        return False


def check_alb(alb_arn, config):
    """
    Check if a specified Application Load Balancer (ALB) exists and is active
    :param alb_arn: the ALB ARN of cluster
    :return: true for successful or false for not successful
    """
    try:
        ec2 = boto.client('ec2', region_name=config["aws_region"])
        response = ec2.describe_load_balancers(LoadBalancerArns=[alb_arn])
        if response['LoadBalancers'][0]['State']['Code'] == 'active':
            logger.info(f"ALB {alb_arn} exists.")
            return True
        else:
            logger.warning(f"ALB {alb_arn} does not exist.")
            return False
    except ClientError as e:
        logger.warning(f"An error occurred: {e}")
        return False


def check_eks(cluster_name, config):
    """
    Check if a specified EKS cluster exists and is active
    :param cluster_name: the name of the cluster
    :return: true for successful or false for not successful
    """
    try:
        eks = boto.client('eks', region_name=config["aws_region"])
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


def check_availability_zones(private_subnets, public_subnets, config):
    ec2 = boto.client('ec2', region_name=config["aws_region"])

    azs = set(config["availability_zones"])
    private_azs_found = set()
    public_azs_found = set()

    for subnet_id in private_subnets:
        subnet_az = ec2.describe_subnets(SubnetIds=[subnet_id])['Subnets'][0]['AvailabilityZone']
        private_azs_found.add(subnet_az)

    for subnet_id in public_subnets:
        subnet_az = ec2.describe_subnets(SubnetIds=[subnet_id])['Subnets'][0]['AvailabilityZone']
        public_azs_found.add(subnet_az)

    if azs == private_azs_found and azs == public_azs_found:
        logger.info("All availability zones are valid.")
        return True
    else:
        logger.warning("Not all availability zones have a private and public subnet.")
        return False


def check_k8s_connection(cluster_name, region):
    """
    Check if you can successfully run a 'kubectl get nodes' command,
      indicating a working connection to the Kubernetes cluster
    :return: true for successful or false for not successful
    """
    try:
        output = subprocess.run(f"aws eks update-kubeconfig --name {cluster_name} --region {region}", shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        output = subprocess.run(["kubectl get nodes"], shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        logger.info("Connection to Kubernetes cluster is working.")
        return True
    except subprocess.CalledProcessError as e:
        logger.warning(e.output,"")
        logger.warning("Connection to Kubernetes cluster is not working.")
        return False


def run_validator(output_file: str, yaml_file: str):
    """
    Run all the validation checks
    :param output_file: the output file
    :return: true for successful or false for not successful
    """
    config = load_config(yaml_file)
    terraform_outputs = load_json_data(output_file)
    
    vpc_id = terraform_outputs.get("vpc_id")
    if vpc_id and not check_vpc(vpc_id["value"], config["aws_region"]):
        quit(1)

    subnet_ids = terraform_outputs.get("private_subnets")["value"] + terraform_outputs.get("public_subnets")["value"]
    if subnet_ids and not check_subnets(subnet_ids, config):
        quit(1)
        
    if subnet_ids and vpc_id and not check_availability_zones(terraform_outputs.get("private_subnets")["value"], terraform_outputs.get("public_subnets")["value"], config):
        quit(1)
        
    # Check ALB
    alb_arn = terraform_outputs.get("alb_arn")
    if alb_arn and not check_alb(alb_arn["value"], config):
        quit(1)

    # Check EKS Cluster
    cluster_name = config["cluster_name"]
    if cluster_name and not check_eks(cluster_name, config):
        quit(1)

    # Ping ALB
    alb_dns_name = terraform_outputs.get("alb_dns_name")
    if alb_dns_name and not ping_alb(alb_dns_name["value"]):
        quit(1)

    # Check K8s Connection
    if not check_k8s_connection(cluster_name, config["aws_region"]):
        quit(1)

    # If all checks pass, log a success message
    logger.info("All resource validation checks passed.")
