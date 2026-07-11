from kubernetes import client, config
from kubernetes.config.config_exception import ConfigException

from app.core import Settings, logger
from app.models import Job, JobTask, Sample


class JobLauncher:
    def __init__(self, settings: Settings):
        self.settings = settings

    def _values(self, job: Job, sample: Sample, task: JobTask) -> dict:
        return {
            "taskId": str(task.id),
            "taskType": task.task_type.value,
            "backendCallbackUrl": self.settings.backend_callback_url,
            "s3EndpointUrl": self.settings.s3_endpoint_url,
            "s3BucketName": self.settings.s3_bucket_name,
            "objectKey": sample.object_name,
            "sha256": sample.sha256,
        }

    def launch_task(self, job: Job, sample: Sample, task: JobTask) -> None:
        logger.info(
            "[noop] launch task_id=%s type=%s values=%s",
            task.id,
            task.task_type,
            self._values(job, sample, task),
        )

    def launch_job(self, job: Job, sample: Sample, tasks: list[JobTask]) -> None:
        for task in tasks:
            self.launch_task(job, sample, task)


class K8sJobLauncher(JobLauncher):
    def __init__(self, settings: Settings):
        super().__init__(settings)
        try:
            config.load_incluster_config()
        except ConfigException:
            config.load_kube_config()

    def launch_task(self, job: Job, sample: Sample, task: JobTask) -> None:
        custom_api = client.CustomObjectsApi()
        values = self._values(job, sample, task)
        release_name = f"job-run-{task.task_type.value}-{task.id}"

        job_manifest = {
            "apiVersion": "helm.toolkit.fluxcd.io/v2",
            "kind": "HelmRelease",
            "metadata": {
                "name": release_name,
                "namespace": self.settings.jobs_namespace,
            },
            "spec": {
                "interval": "1m",
                "chart": {
                    "spec": {
                        "chart": "charts/job-to-run",
                        "sourceRef": {
                            "kind": "GitRepository",
                            "name": "flux-system",
                            "namespace": "flux-system",
                        },
                    }
                },
                "values": values,
            },
        }

        custom_api.create_namespaced_custom_object(
            group="helm.toolkit.fluxcd.io",
            version="v2",
            namespace=self.settings.jobs_namespace,
            plural="helmreleases",
            body=job_manifest,
        )
        logger.info("launched HelmRelease=%s task_id=%s", release_name, task.id)


def build_job_launcher(settings: Settings) -> JobLauncher:
    if settings.job_launcher == "k8s":
        return K8sJobLauncher(settings)
    return JobLauncher(settings)
