# Container Accelerator

## Configuration

### AWS Configuration

#### aws_region - required
Specifies the AWS region to deploy the infrastructure to.

#### bucket_name - required
Specifies the bucket to store the Terraform state

#### dynamodb_table_name - required
Specifies the DynamoDB table for locking the Terraform state file. This table must have "LockID" as its partition key

### Networking Configuration
#### cidr_block - *optional*
**Defaults to 10.0.0.0/16** \
\
Specifies the CIDR block assigned to the VPC. 

#### availability_zones - *optional*
**Defaults to all availability zones in the region** \
\
Specifies which regions to create a private and public subnet in. Each subnet will be given equal numbers of IP 
addresses based on the size of the CIDR block given to the VPC

### EKS Configuration

#### cluster_name - required
Specifies name of the cluster.

#### eks_version - *optional*
**Defaults to the latest version of EKS** \
\
Specifies the version of EKS to run

#### fargate - *optional*
**Defaults to false** \
\
Specifies if fargate should be used for compute resources

#### cluster_namespaces - *optional*
**Defaults to kube-system** \
\
Specifies the namespaces to create for the kubernetes cluster

#### ingress_type - *optional*
**Defaults to AWS**\
\
Specifies what kind of load balancer should be used to handle incoming traffic. \
\
**CURRENTLY ONLY AWS IS SUPPORTED**

### Node Group Configuration - *optional*
**Node group configuration is only used when fargate is set to false**

#### name - required
Specifies the name of the node group

#### instance_type - required
Specifies the type of instance to be used to run each node. Must be an EC2 instance

#### min_size - required
Specifies the minimum number of nodes to be running at any time in the cluster

#### max_size - required
Specifies the maximum number of nodes to be running at any time in the cluster

#### desired_capacity - required
Specifies the desired number of nodes to be running at any time in the cluster

### Ingress Configuration

#### enable_public_ingress - *optional*
**Defaults to false** \
\
Specifies if public ingress should be allowed for the cluster

#### ingress_from_port - *optional*
**Defaults to 80**\
\
Specifies the starting port for accepting traffic

#### ingress_to_port - *optional*
**Defaults to 80**\
\
Specifies the end port for accepting traffic

#### ingress_protocol - *optional*
**Defaults to TCP**\
\
Specifies the protocol for ingress traffic

### Tagging
These tags are added to every piece of infrastructure deployed to AWS

#### resource_owner - mandatory
Specifies the resource owner tag

#### environment - *optional*
**Defaults to dev**\
\
Specifies the environment type

#### additional_tags - *optional*
Specifies any additional tags to be added

##### key - mandatory
Specifies the key of the tag to be added

##### value - mandatory
Specifies the value of the tag to be added

### Roles and Permissions

#### ca_cluster_admin_role_name - *optional*
**Defaults to ca_cluster_admin**\
\
Specifies the name of the role for the cluster admin

#### ca_cluster_dev_role_name - *optional*
**Defaults to ca_cluster_dev**\
\
Specifies the name of the role for the cluster developer

#### access_token_env_key - mandatory
**THIS IS NOT A CREDENTIAL**\
\
Specifies the key of the secret that stores the AWS access key

#### secret_token_env_key - mandatory
**THIS IS NOT A CREDENTIAL**\
\
Specifies the key of the secret that stores the AWS secret token key

### Example Configuration
```yaml
# AWS configuration
aws_region: us-east-1 
bucket_name: tf-state-bucket
dynamodb_table_name: tf-locking-table

# VPC and Subnets
cidr_block: 10.0.0.0/16
availability_zones: 
  - us-east-1a
  - us-east-1b
  - us-east-1c
  - us-east-1d
  - us-east-1e
  - us-east-1f

# EKS configuration
cluster_name: my-cluster 
eks_version: 1.14 
fargate: false 
cluster_namespaces:
  - kube-system
  - default
ingress_type: aws

# node group configuration (only when fargate is false)
node_groups:
  - name: my-node-group 
    instance_type: t3.medium 
    min_size: 1 
    max_size: 3 
    desired_capacity: 2

# Public ingress
enable_public_ingress: true 
ingress_from_port: 80
ingress_to_port: 80 
ingress_protocol: tcp 

# Tagging
resource_owner: my-team 
environment: dev 
additional_tags:
  - key: Test
    value: Value
  - key: Test2
    value: Test3

# Roles and Permissions
ca_cluster_admin_role_name: ca_cluster_admin 
ca_cluster_dev_role_name: ca_cluster_dev 
access_token_env_key: ACCESS_TOKEN 
secret_token_env_key: SECRET_TOKEN 
```