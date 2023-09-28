import os
import subprocess
from facade.ingress_controllers.ingress_controller_base import IngressControllerBase


class AWSIngressController(IngressControllerBase):
    def __init__(self, cluster_name, region, vpc_id=None):
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
        self._install_eksctl()
        self._create_oidc_provider()
        self._create_iam_policy()
        self._create_service_account()

    def _install_eksctl(self):
        # check if eksctl is installed
        try:
            subprocess.run("eksctl version", shell=True, check=True)
            return
        
        except Exception as e:
            # Install eksctl
            platform = "Linux_arm64"
            download_command = f'curl -sLO "https://github.com/eksctl-io/eksctl/releases/latest/download/eksctl_{platform}.tar.gz"'
            unzip_command = f'tar -xzf eksctl_{platform}.tar.gz -C /tmp && rm eksctl_{platform}.tar.gz'
            move_command = f'sudo mv /tmp/eksctl /usr/local/bin'

            subprocess.run(download_command, shell=True, check=True)
            subprocess.run(unzip_command, shell=True, check=True)
            subprocess.run(move_command, shell=True, check=True)

    def _create_oidc_provider(self):
        oidc_command = f'eksctl utils associate-iam-oidc-provider --cluster {self.cluster_name} --approve'
        subprocess.run(oidc_command, shell=True, check=True)
        print("Created OIDC provider")

    def _create_iam_policy(self):
        cwd = os.path.dirname(os.path.abspath(__file__))
        policy_path = os.path.join(cwd, "../../static/iam_policy.json")

        policy_command = f'aws iam create-policy --policy-name AWSLoadBalancerControllerIAMPolicy --policy-document file://{policy_path}'
        subprocess.run(policy_command, shell=True, check=True)
        print("Created IAM policy")

    def _create_service_account(self):
        account_id_command = 'aws sts get-caller-identity --query Account --output text'
        account_id = subprocess.check_output(account_id_command, shell=True).decode().strip()

        sa_command = f'eksctl create iamserviceaccount\
            --cluster {self.cluster_name}\
            --namespace kube-system\
            --name aws-load-balancer-controller\
            --attach-policy-arn arn:aws:iam::{account_id}:policy/AWSLoadBalancerControllerIAMPolicy\
            --override-existing-serviceaccounts\
            --approve'
        subprocess.run(sa_command, shell=True, check=True)
        print("Created service account")
