import logging
import subprocess


logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] (k8s-primer) %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)


class IngressControllerBase:
    """
    The IngressControllerBase class defines a common interface for all Ingress Controller
    classes to implement, and provides install via Helm and pre-install tasks
    """
    def __init__(self, 
                 name: str,
                 helm_repo: str, 
                 helm_chart: str,
                 namespace: str = "kube-system",
                 chart_version: str = None,
                 set_flags: dict = None
                 ):
        """Constructor for the IngressControllerBase class

        :param name: The name of the Ingress Controller deployment in the cluster
        :param helm_repo: The repo to install the Helm chart from
        :param helm_chart: The name of the Helm chart to install
        :param namespace: The namespace to install into, defaults to "kube-system"
        :param chart_version: The version number of the helm chart, defaults to None
        :param set_flags: A list of --set attributes to add to the Helm install, defaults to None
        """
        self.name = name
        self.namespace = namespace
        self.helm_repo = helm_repo
        self.helm_chart = helm_chart
        self.chart_version = chart_version
        self.set_flags = set_flags

    def install(self):
        """
        Installs the Ingress Controller into the cluster
        """
        self._pre_install_tasks()
        self._helm_install()

    def _pre_install_tasks(self):
        """
        Override this function definition in the inheriting class to perform any pre-install tasks
        """
        pass

    def _helm_install(self):
        logger.info(f"Installing {self.name}")
        helm_command = f"helm install {self.name} {self.helm_chart}\
                        --repo {self.helm_repo}\
                        -n {self.namespace}"

        if self.chart_version:
            helm_command += f" --version {self.chart_version}"

        if self.set_flags and self.set_flags != {}:
            for key, value in self.set_flags.items():
                helm_command += f" --set {key}={value}"

        try:
            subprocess.run(helm_command, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            logger.info(f"{self.name} installed successfully")
        except Exception as e:
            logger.exception(f"Failed to install {self.name}")
            quit(1)
