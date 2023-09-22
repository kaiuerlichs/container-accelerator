from util.tf_string_builder import TFStringBuilder


def generate_eks_modules(config):
    source = "terraform-aws-modules/eks/aws"
    version = "19.16.0"

    eks_config = {}
    eks_config["cluster_name"] = config["cluster_name"]
    eks_config["cluster_version"] = str(config["eks_version"]) if "eks_version" in config else "1.27"
    eks_config["subnets"] = ("aws_subnet.private_subnet[*].id", "ref")
    eks_config["vpc_id"] = ("aws_vpc.vpc.id", "ref")

    if (not config["fargate"] if "fargate" in config else True):
        eks_config["eks_managed_node_groups"] = {
            group["name"]: {
                "min_size": group["min_size"],
                "max_size": group["max_size"],
                "desired_capacity": group["desired_capacity"],
                "instance_type": group["instance_type"],
                "name": group["name"]
            } 
        for group in config["node_groups"]}

    else:
        eks_config["fargate_profiles"] = {
            "default": {
                "name": "default",
                "selectors": [{"namespace": ns} for ns in config["cluster_namespaces"]]
            }
        }

    return TFStringBuilder.generate_module("eks", source, version, eks_config)


def generate_k8s_namespaces(config):
    cluster_datapoint_config = {
        "name": ("module.eks.cluster_name", "ref")
    }
    k8s_provider_config = {
        "host": ("data.eks_cluster.cluster.endpoint", "ref"),
        "cluster_ca_certificate": ("base64decode(data.eks_cluster.cluster.certificate_authority.0.data)", "ref")
    }
    k8s_ns_configs = [{"metadata": {"name": ns}} for ns in config["cluster_namespaces"]]

    output = ""
    output += TFStringBuilder.generate_data("eks_cluster", "cluster", cluster_datapoint_config)
    output += TFStringBuilder.generate_provider("kubernetes", k8s_provider_config)
    
    for ns_config in k8s_ns_configs:
        output += TFStringBuilder.generate_resource("kubernetes_namespace", ns_config["metadata"]["name"], ns_config)

    return output


def generate_ingress_controller(config):
    match config["ingress_type"]:
        case "alb":
            return generate_alb_ingress_controller(config)
        case _:
            return ""


def generate_alb_ingress_controller(config):
    # Will be done in CA-39
    pass
