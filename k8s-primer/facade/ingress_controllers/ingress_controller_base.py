import subprocess


class IngressControllerBase:
    def __init__(self, 
                 name: str,
                 helm_repo: str, 
                 helm_chart: str,
                 namespace: str = "kube-system",
                 chart_version: str = None,
                 set_flags: dict = None
                 ):
        self.name = name
        self.namespace = namespace
        self.helm_repo = helm_repo
        self.helm_chart = helm_chart
        self.chart_version = chart_version
        self.set_flags = set_flags

    def install(self):
        self._pre_install_tasks()
        self._helm_install()

    def _pre_install_tasks(self):
        pass

    def _helm_install(self):
        helm_command = f"helm install {self.name} {self.helm_chart}\
                        --repo {self.helm_repo}\
                        -n {self.namespace}"

        if self.chart_version:
            helm_command += f" --version {self.chart_version}"

        if self.set_flags and self.set_flags != {}:
            for key, value in self.set_flags.items():
                helm_command += f" --set {key}={value}"

        subprocess.run(helm_command, shell=True, check=True)
