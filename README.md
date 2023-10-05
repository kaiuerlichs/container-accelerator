
# Container Accelerator

This Container Accelerator is a quickstart deployment solution for AWS Elastic Kubernetes Service clusters. It takes in a simple yaml file providing the configuration of the AWS infrastructure and Kubernetes setup, and provides easy-to-use deployment pipelines to instatiate these resources.



## Getting Started

Follow the steps below to get started using the Container Accelerator and initiate an EKS cluster deployment in minutes.

### Prerequisites
- An AWS account with access priviledges to create EKS clusters
- An S3 bucket and DynamoDB table for remote terraform backend ([How do I do this?](https://spacelift.io/blog/terraform-s3-backend#terraform-s3-backend-implementation-)) 

### Usage

1. Fork the Container Accelerator repository found [here](https://github.com/kaiuerlichs/container-accelerator)
2. Set up the `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY` secrets in the GitHub Actions repository secrets
3. Create a new branch (i.e. `config`) and adjust the `config.yml` file to configure your EKS cluster deployment
4. Create a pull request onto the master branch 
```
This will start an Actions workflow that goes through the following steps:
- generate terraform files
- create deployment plan
```
5. Merge your pull request
```
This will start an Actions workflow that goes through the following steps:
- generate terraform files
- create deployment plan
- apply deployment plan
- configure the k8s cluster
- validate the deployment was successful
```

### Deleting a deployment

Using these steps, you can use the Container Accelerator tools to destroy an existing EKS deployment.

1. Ensure your `config.yml` contains the correct remote backend configuration
2. Navigate to the Actions tab and select the `Destroy current deployment` pipeline
3. Select `run workflow` and choose the master branch

The pipeline will now remove your existing EKS deployment matching the config.yml.
## Configuration parameters

#### AWS configuration

| Parameter | Type | Description |
| :---------| :----| :---------- |
| `aws_region` | `string` | **Required**. Specifies the AWS region to deploy the infrastructure to |
| `bucket_name` | `string` | **Required**. Specifies the bucket to store the Terraform state |
| `dynamodb_table_name` | `string` | **Required**. Specifies the DynamoDB table for locking the Terraform state file |

#### Networking configuration

| Parameter | Type | Description |
| :---------| :----| :---------- |
| `cidr_block` | `string` | **Defaults to `10.0.0.0/16`**. Specifies the CIDR block assigned to the VPC |
| `availability_zones` | `string` | **Defaults to all availability zones in the region**. Specifies which regions to create a private and public subnet in. Each subnet will be given equal numbers of IP addresses based on the size of the CIDR block given to the VPC |

#### EKS configuration

| Parameter | Type | Description |
| :---------| :----| :---------- |
| `cluster_name` | `string` | **Required**. Specifies name of the cluster |
| `eks_version` | `string` | **Defaults to `1.28`**. Specifies the version of EKS to run |
| `fargate` | `bool` | **Defaults to `false`**. Specifies if fargate should be used for compute resources |
| `cluster-namespaces` | `list` | **Defaults to `[kube-system]`**. Specifies the namespaces to create for the kubernetes cluster |
| `ingress_type` | `enum` | **Defaults to `aws`**. Specifies what kind of ingress controller should be used. Available controllers: `aws`, ... |.
| `node_groups` | `list` | **Required if fargate is false**. List of node groups to deploy into the cluster (see below) |

#### Node Group configuration (only when fargate is false)

| Parameter | Type | Description |
| :---------| :----| :---------- |
| `name` | `string` | **Required**. Specifies name of the node group |
| `instance_type` | `string` | **Required**. Specifies the type of EC2 instance to be used to run each node |
| `min_size` | `number` | **Required**. Specifies the minimum number of nodes to be running at any time in the cluster |
| `max_size` | `number` | **Required**. Specifies the maximum number of nodes to be running at any time in the cluster |
| `desired_capacity` | `number` | **Optional**. Specifies the desired number of nodes to be running at any time in the cluster |

#### Public ingress configuration

| Parameter | Type | Description |
| :---------| :----| :---------- |
| `enable_public_ingress` | `bool` | **Defaults to `false`**. Specifies if public ingress should be allowed for the cluster |

#### IAM roles

IAM roles are created during deployment to provide access control out of the box. Admin users will be able to create and destroy deployments, while dev users can deploy into the EKS cluster. 

(*May pass existing role names to attach policies to those roles.*)

| Parameter | Type | Description |
| :---------| :----| :---------- |
| `ca_cluster_admin_role_name` | `string` | **Defaults to `ca_cluster_admin`**. Specifies name of cluster admin IAM role |
| `ca_cluster_dev_role_name` | `string` | **Defaults to `ca_cluster_dev`**. Specifies name of cluster dev IAM role |

#### Global resource tagging

Global resource tags are attached to all resources created by the container accelerator.

| Parameter | Type | Description |
| :---------| :----| :---------- |
| `resource_owner` | `string` | **Required**. Specifies the resource owner tag |
| `environment` | `string` | **Defaults to `dev`**. Specifies the environment tag |
| `additional_tags` | `list` | **Optional**. Specifies additional tags by providing a key/value pair |


## Example config file

```yaml
# AWS configuration
aws_region: eu-west-1 
bucket_name: my-eks-cluster-state 
dynamodb_table_name: my-eks-cluster-lock 

# VPC and Subnets
cidr_block: 10.0.0.0/16 # defaults to 10.0.0.0/16
availability_zones: 
  - eu-west-1a
  - eu-west-1b
  - eu-west-1c

# EKS configuration
cluster_name: my-eks-cluster 
eks_version: 1.28 
fargate: false 
cluster_namespaces: 
  - kube-system
  - apps
ingress_type: aws 

# node group configuration 
node_groups:
  - name: my-node-group 
    instance_type: t2.micro 
    min_size: 1 
    max_size: 3 
    desired_capacity: 2

# Public ingress
enable_public_ingress: true 

# Tagging
resource_owner: dundee-team-7 
environment: dev 
additional_tags:
  - key: ekscluster
    value: my-eks-cluster

# Roles and Permissions
ca_cluster_admin_role_name: ca_cluster_admin 
ca_cluster_dev_role_name: ca_cluster_dev 
```
## Authors

- [@Casperscare](https://www.github.com/Casperscare)
- [@kellycj](https://www.github.com/kellycj)
- [@SN51-SYS](https://www.github.com/SN51-SYS)
- [@winer222](https://www.github.com/winer222)
- [@kaiuerlichs](https://www.github.com/kaiuerlichs)

