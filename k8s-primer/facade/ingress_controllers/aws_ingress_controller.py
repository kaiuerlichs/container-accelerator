import os
import logging
import subprocess
from facade.ingress_controllers.ingress_controller_base import IngressControllerBase


logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] (k8s-primer) %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)


class AWSIngressController(IngressControllerBase):
    """
    The AWS Ingress Controller class is used to install the AWS Load Balancer Controller
    into a EKS cluster using Helm
    """
    def __init__(self, cluster_name, region, vpc_id=None):
        """Constructor for the AWSIngressController class

        :param cluster_name: The name of the cluster to install into
        :param region: The AWS region the cluster is in
        :param vpc_id: The ID of the VPC the cluster is in, defaults to None
        """
        set_flags = {
            "clusterName": cluster_name,
            "region": region,
            "serviceAccount.create": "false",
            "serviceAccount.name": "aws-load-balancer-controller"
        }
        if vpc_id:
            set_flags["vpcId"] = vpc_id

        super().__init__(
            name="aws-load-balancer-controller",
            helm_repo="https://aws.github.io/eks-charts",
            helm_chart="aws-load-balancer-controller",
            set_flags=set_flags
        )

        self.cluster_name = cluster_name
        self.region = region

    def _pre_install_tasks(self):
        logger.info("Starting pre-install tasks")
        self._install_eksctl()
        self._create_oidc_provider()
        self._create_iam_policy()
        self._create_service_account()
        logger.info("Pre-install tasks complete")

    def _install_eksctl(self):
        # check if eksctl is installed
        try:
            subprocess.run("eksctl version", shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            logger.info("eksctl is already installed")
            return
        
        except Exception as e:
            # Install eksctl
            platform = "Linux_arm64"
            download_command = f'curl -sLO "https://github.com/eksctl-io/eksctl/releases/latest/download/eksctl_{platform}.tar.gz"'
            unzip_command = f'tar -xzf eksctl_{platform}.tar.gz -C /tmp && rm eksctl_{platform}.tar.gz'
            move_command = f'sudo mv /tmp/eksctl /usr/local/bin'

            try:
                subprocess.run(download_command, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                subprocess.run(unzip_command, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                subprocess.run(move_command, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                logger.info("eksctl installed successfully")
            except Exception as e:
                logger.exception("Failed to install eksctl")
                quit(1)

    def _create_oidc_provider(self):
        oidc_command = f'eksctl utils associate-iam-oidc-provider --cluster {self.cluster_name} --approve'

        try:
            subprocess.run(oidc_command, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            logger.info("OIDC provider for AWS ingress controller created successfully")
        except Exception as e:
            logger.exception("Failed to create OIDC provider for AWS ingress controller")
            quit(1)

    def _create_iam_policy(self):
        cwd = os.path.dirname(os.path.abspath(__file__))
        policy_path = os.path.join(cwd, "../../static/iam_policy.json")

        policy_command = f'aws iam create-policy --policy-name AWSLoadBalancerControllerIAMPolicy --policy-document file://{policy_path}'
        
        try:
            subprocess.run(policy_command, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            logger.info("IAM policy for AWS ingress controller created successfully")
        except Exception as e:
            logger.exception("Failed to create IAM policy for AWS ingress controller")
            quit(1)

    def _create_service_account(self):
        account_id_command = 'aws sts get-caller-identity --query Account --output text'
        account_id = subprocess.check_output(account_id_command, shell=True, stderr=subprocess.PIPE).decode().strip()

        sa_command = f'eksctl create iamserviceaccount\
            --cluster {self.cluster_name}\
            --namespace kube-system\
            --name aws-load-balancer-controller\
            --attach-policy-arn arn:aws:iam::{account_id}:policy/AWSLoadBalancerControllerIAMPolicy\
            --override-existing-serviceaccounts\
            --approve'
        
        try:
            subprocess.run(sa_command, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            logger.info("Service account for AWS ingress controller created successfully")
        except Exception as e:
            logger.exception("Failed to create service account for AWS ingress controller")
            quit(1)
