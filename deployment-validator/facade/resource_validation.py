# Import necessary libraries
import boto3 as boto
import requests
import subprocess
from botocore.exceptions import ClientError

# Function to create an EKS client
def create_eks_client():
    try:
        return boto.client('eks')
    except Exception as e:
        print("Failed to create EKS client:", str(e))
        return None

# Create the EKS client
eks = create_eks_client()

# If the EKS client is not created, print an error message
if eks is None:
    print("EKS client is not created. Please check your AWS credentials.")

# Function to check if the specified subnets exist and are available
def check_subnets(subnet_ids):
    try:
        response = eks.describe_subnets(SubnetIds=subnet_ids)
        for subnet in response['Subnets']:
            if subnet['State'] != 'available':
                print(f"Subnet {subnet['SubnetId']} does not exist.")
                return False
        print("All subnets exist.")
        return True
    except ClientError as e:
        print(f"An error occurred: {e}")
        return False

# Function to check if a specified Application Load Balancer (ALB) exists and is active
def check_alb(alb_arn):
    try:
        response = eks.describe_load_balancers(LoadBalancerArns=[alb_arn])
        if response['LoadBalancers'][0]['State']['Code'] == 'active':
            print(f"ALB {alb_arn} exists.")
            return True
        else:
            print(f"ALB {alb_arn} does not exist.")
            return False
    except ClientError as e:
        print(f"An error occurred: {e}")
        return False

# Function to check if a specified EKS cluster exists and is active
def check_eks(cluster_name):
    try:
        response = eks.describe_cluster(name=cluster_name)
        if response['cluster']['status'] == 'ACTIVE':
            print(f"EKS cluster {cluster_name} exists.")
            return True
        else:
            print(f"EKS cluster {cluster_name} does not exist.")
            return False
    except ClientError as e:
        print(f"An error occurred: {e}")
        return False

# Function to chekck if the ALB  is up and running it sends out a ping and checks responds with 'pong'
def ping_alb(alb_dns_name):
    try:
        response = requests.get(url='http://'+ alb_dns_name +'/ping', timeout=(15,))
        if response.text=='pong':
            print(f"ALB {alb_dns_name} is responding to pings.")
            return True
        else:
            print(f"ALB {alb_dns_name} is not responding to pings.")
            return False
    except ClientError as e:
        print(f"An error occurred: {e}")
        return False

# Function to check if you can successfully run a 'kubectl get nodes' command, indicating a working connection to the Kubernetes cluster
def check_k8s_connection():
    try:
        output = subprocess.check_output(["kubectl", "get", "nodes"])
        print("Connection to Kubernetes cluster is working.")
        return True
    except subprocess.CalledProcessError as e:
        print(e.output)
        print("Connection to Kubernetes cluster is not working.")
        return False
