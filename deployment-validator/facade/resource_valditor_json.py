import json
import yaml
import requests
import boto3 as boto
from botocore.exceptions import ClientError

# Load JSON data from the file
def load_json_data(file_name):
    with open(file_name, 'r') as json_file:
        return json.load(json_file)

# Load availability zones from a YAML file
def load_availability_zones(file_name):
    with open(file_name, 'r') as yaml_file:
        return yaml.safe_load(yaml_file)

# Creating a dictionary to store subnet IDs as keys and their associated availability zones
#as values
def create_subnet_availability_zones(data):
    subnet_availability_zones = {}
    for subnet in data['SUBNET']:
        if 'id' in subnet and 'availabilityZone' in subnet:
            subnet_id = subnet['id']
            availability_zone = subnet['availabilityZone']
            subnet_availability_zones[subnet_id] = availability_zone
    return subnet_availability_zones

# Check if a VPC exists and its state
def check_vpc(data):
    if 'VPC' in data:
        vpc = data['VPC']
        if 'id' in vpc and 'state' in vpc:
            vpc_id = vpc['id']
            state = vpc['state']
            print(f"VPC with ID {vpc_id} is {state}")
        else:
            print("VPC is missing ID or state")
    else:
        print("VPC does not exist")

# Check if a SUBNET exists and its state
def check_subnet(json_file):
    if 'SUBNET' in json_file:
        subnets = json_file['SUBNET']
        for subnet in subnets:
            if 'id' in subnet and 'state' in subnet:
                subnet_id = subnet['id']
                state = subnet['state']
                print(f"SUBNET with ID {subnet_id} is {state}")
            else:
                print("SUBNET is missing ID or state")
    else:
        print("SUBNET does not exist")

# Check if an ALB exists and its state
def check_alb(json_file):
    if 'ALB' in json_file:
        alb = json_file['ALB']
        if 'id' in alb and 'state' in alb:
            alb_id = alb['id']
            state = alb['state']
            print(f"ALB with ID {alb_id} is {state}")
        else:
            print("ALB is missing ID or state")
    else:
        print("ALB does not exist")

# Check if an EKS exists and its state
def check_eks(json_file):
    if 'EKS' in json_file:
        eks = json_file['EKS']
        if 'id' in eks and 'state' in eks:
            eks_id = eks['id']
            state = eks['state']
            print(f"EKS with ID {eks_id} is {state}")
        else:
            print("EKS is missing ID or state")
    else:
        print("EKS does not exist")

# Check if each subnet has two availability zones
def check_subnet_availability_zones(subnet_availability_zones):
    for subnet_id, zones in subnet_availability_zones.items():
        if len(zones) != 2:
            print(f"Subnet {subnet_id} does not have exactly two availability zones: {zones}")

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
    

    
