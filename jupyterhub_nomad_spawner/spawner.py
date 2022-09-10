import asyncio
import hashlib
import os
import ssl
import typing as t
from typing import Dict, Optional, Tuple, Union

from httpx import AsyncClient
from jupyterhub.spawner import Spawner
from pydantic import BaseModel
from tenacity import retry, stop_after_attempt, wait_fixed
from traitlets import Bool
from traitlets import Callable as TCallable
from traitlets import Dict as TDict
from traitlets import Int as TInt
from traitlets import List as TList
from traitlets import Unicode
from traitlets import Union as TUnion
from traitlets import default

from jupyterhub_nomad_spawner.consul.consul_service import (
    ConsulService,
    ConsulServiceConfig,
    ConsulTLSConfig,
)
from jupyterhub_nomad_spawner.job_factory import JobData, JobVolumeData, create_job
from jupyterhub_nomad_spawner.job_options_factory import create_form
from jupyterhub_nomad_spawner.nomad.nomad_service import (
    NomadService,
    NomadServiceConfig,
    NomadTLSConfig,
)


class CreateJobResponse(BaseModel):
    EvalCreateIndex: int
    EvalID: str
    Index: int
    JobModifyIndex: int
    KnownLeader: bool
    LastContact: int
    Warnings: str


class NomadSpawner(Spawner):
    # Nomad
    nomad_addr = Unicode(
        help="""
        The nomad address to use.
        """
    ).tag(config=True)

    @default("nomad_addr")
    def _default_nomad_addr(self):
        self.log.warning("nomad_addr not set, using default")
        return os.environ.get("NOMAD_ADDR", "http://localhost:4646")

    nomad_token = Unicode(
        help="""
        The nomad token
        """
    ).tag(config=True)

    @default("nomad_token")
    def _nomad_token_default(self):
        return os.environ.get("NOMAD_TOKEN", "")

    nomad_ca_cert = Unicode(
        help="""

        """
    ).tag(config=True)

    @default("nomad_ca_cert")
    def _nomad_ca_cert_default(self):
        return os.environ.get("NOMAD_CA_CERT", "")

    nomad_ca_path = Unicode(
        help="""
        """
    ).tag(config=True)

    @default("nomad_ca_path")
    def _nomad_ca_path_default(self):
        return os.environ.get("NOMAD_CA_PATH", "")

    nomad_client_cert = Unicode(
        help="""
        """
    ).tag(config=True)

    @default("nomad_client_cert")
    def _nomad_client_cert_default(self):
        return os.environ.get("NOMAD_CLIENT_CERT", "")

    nomad_client_key = Unicode(
        help="""
        """
    ).tag(config=True)

    @default("nomad_client_key")
    def _nomad_client_key_default(self):
        return os.environ.get("NOMAD_CLIENT_KEY", "")

    nomad_tls_server_name = Unicode(
        help="""
        """
    ).tag(config=True)

    @default("nomad_tls_server_name")
    def _nomad_tls_server_name_default(self):
        return os.environ.get("NOMAD_TLS_SERVER_NAME", "")

    nomad_tls_skip_verify = Bool(
        help="""
        """
    ).tag(config=True)

    @default("nomad_tls_skip_verify")
    def _nomad_tls_skip_verify_default(self):
        verify = os.environ.get("NOMAD_TLS_SKIP_VERIFY", "")
        return verify.lower() in ("yes", "true", "t", "1")

    # Consul
    consul_http_addr = Unicode(
        help="""
        The consul address to use.
        """
    ).tag(config=True)

    @default("consul_http_addr")
    def _default_consul_http_addr(self):
        return os.environ.get("CONSUL_HTTP_ADDR", "http://localhost:8500")

    consul_http_token = Unicode(
        help="""
        The consul token
        """
    ).tag(config=True)

    @default("consul_http_token")
    def _consul_http_token_default(self):
        return os.environ.get("CONSUL_HTTP_TOKEN", "")

    consul_ca_cert = Unicode(
        help="""

        """
    ).tag(config=True)

    @default("consul_ca_cert")
    def _consul_ca_cert_default(self):
        return os.environ.get("CONSUL_CA_CERT", "")

    consul_ca_path = Unicode(
        help="""
        """
    ).tag(config=True)

    @default("consul_ca_path")
    def _consul_ca_path_default(self):
        return os.environ.get("CONSUL_CA_PATH", "")

    consul_client_cert = Unicode(
        help="""
        """
    ).tag(config=True)

    @default("consul_client_cert")
    def _consul_client_cert_default(self):
        return os.environ.get("CONSUL_CLIENT_CERT", "")

    consul_client_key = Unicode(
        help="""
        """
    ).tag(config=True)

    @default("consul_client_key")
    def _consul_client_key_default(self):
        return os.environ.get("CONSUL_CLIENT_KEY", "")

    consul_tls_server_name = Unicode(
        help="""
        """
    ).tag(config=True)

    @default("consul_tls_server_name")
    def _consul_tls_server_name_default(self):
        return os.environ.get("CONSUL_TLS_SERVER_NAME", "")

    consul_tls_skip_verify = Bool(
        help="""
        """
    ).tag(config=True)

    @default("consul_tls_skip_verify")
    def _consul_tls_skip_verify_default(self):
        verify = os.environ.get("CONSUL_TLS_SKIP_VERIFY", "")
        return verify.lower() in ("yes", "true", "t", "1")

    @default("ip")
    def _default_ip(self):
        return "0.0.0.0"

    @default("port")
    def _default_port(self):
        return 8888

    @default("env_keep")
    def _default_env_keep(self):
        return [
            "CONDA_ROOT",
            "CONDA_DEFAULT_ENV",
            "VIRTUAL_ENV",
            "LANG",
            "LC_ALL",
            "JUPYTERHUB_SINGLEUSER_APP",
        ]

    common_images = TList(
        help="""
        A list of images that are pre selectable
        """
    ).tag(config=True)

    @default("common_images")
    def _default_common_images(self) -> t.List[str]:
        return [
            "jupyter/base-notebook",
            "jupyter/scipy-notebook",
            "jupyter/datascience-notebook",
            "jupyter/tensorflow-notebook",
            "jupyter/minimal-notebook",
        ]

    datacenters = TList(
        help="""
        The list of available datacenters
        """
    ).tag(config=True)

    csi_plugin_ids = TList(
        help="""
        A list of CSI Plugins.

        """
    ).tag(config=True)

    @default("csi_plugin_ids")
    def _default_csi_plugin_ids(self) -> t.List[str]:
        return []

    base_job_name = Unicode(
        help="""
        The base name of the job. Will be concated with -<notebook_id>
        """
    ).tag(config=True)

    @default("base_job_name")
    def _default_base_job_name(self):
        return "jupyterhub-notebook"

    @property
    def job_name(self) -> str:
        if self.notebook_id:
            return f"{self.base_job_name}-{self.notebook_id}"
        raise ValueError("notebook_id is not set")

    base_csi_volume_name = Unicode(
        help="""
        The base name of the csi volume. Will be concated with -<notebook_id>
    """
    ).tag(config=True)

    @default("base_csi_volume_name")
    def _default_base_csi_volume_name(self):
        return "jupyterhub-notebook"

    csi_volume_parameters = TUnion(
        [TCallable(), TDict()],
        help="""
        When a CSI Volume is used, calculate the extra parameters
        def csi_volume_parameters(spawner):
            if spawner.user_options["volume_csi_plugin_id"] == "rocketduck-csi-plugin":
                return {
                    "gid" : 1000,
                    "uid" : 1000,
                    "mode" : "770"
                }
            else:
                return None
        c.NomadSpawner.csi_volume_parameters = csi_volume_parameters
        """,
    ).tag(config=True)

    vault_policies = TUnion(
        [TCallable(), TList()],
        help="""
        When a list of vault policies or a callable that returns a list
        def vault_policies(spawner):
            return [
                "my-vault-policy", f"user-policy-{spawner.user.name}"
            ]
        c.NomadSpawner.vault_policies = vault_policies
        """,
    ).tag(config=True)

    csi_capacity = TInt(
        help="""
        The min csi capacity in bytes
        e.g.

        c.NomadSpawner.csi_capacity = 13421772
        """,
    ).tag(config=True)

    @property
    def csi_volume_name(self) -> str:
        if self.notebook_id:
            return f"{self.base_csi_volume_name}-{self.notebook_id}"
        raise ValueError("notebook_id is not set")

    @property
    def service_name(self) -> str:
        if self.notebook_id:
            return f"{self.job_name}"
        raise ValueError("notebook_id is not set")

    async def start(self):

        nomad_service_config = build_nomad_config_from_options(self)
        nomad_httpx_client = build_nomad_httpx_client(nomad_service_config)
        nomad_service = NomadService(client=nomad_httpx_client, log=self.log)

        consul_service_config = build_consul_config_from_options(self)
        consul_httpx_client = build_consul_httpx_client(consul_service_config)
        consul_service = ConsulService(client=consul_httpx_client, log=self.log)

        try:

            notebook_id: str = hashlib.sha1(
                f"{self.user.name}:{self.name}".encode("utf-8")
            ).hexdigest()[:10]
            self.notebook_id = notebook_id
            self.log.info("server name: %s", self.name)
            env = self.get_env()
            args = self.get_args()

            volume_data: Optional[JobVolumeData] = None

            if self.user_options.get("volume_type", None):
                volume_data = await self.create_job_volume_data(nomad_service)

            policies: TList[str] = []
            if callable(self.vault_policies):
                policies = self.vault_policies(self)
            elif self.vault_policies:
                policies = self.vault_policies

            job_hcl = create_job(
                JobData(
                    job_name=self.job_name,
                    username=self.user.name,
                    notebook_name=self.name,
                    service_name=self.service_name,
                    env=env,
                    args=args,
                    image=self.user_options["image"],
                    datacenters=self.user_options["datacenters"],
                    memory=self.user_options["memory"],
                    volume_data=volume_data,
                    policies=policies,
                )
            )

            await nomad_service.schedule_job(job_hcl)
            await self._ensure_running(nomad_service=nomad_service)

            service_data = await self.service(consul_service)
        except Exception as e:
            self.log.exception("Failed to start")
            raise e

        finally:
            if nomad_httpx_client is not None:
                await nomad_httpx_client.aclose()
            if consul_httpx_client is not None:
                await consul_httpx_client.aclose()
        return service_data

    async def create_job_volume_data(self, nomad_service: NomadService):
        volume_type = self.user_options["volume_type"]
        self.log.info("Configuring volume of type: %s", volume_type)

        if volume_type == "csi":
            volume_id = self.csi_volume_name
            parameters = self._get_csi_extra_parameters()

            min_size: Optional[int] = self.csi_capacity
            await nomad_service.create_volume(
                id=volume_id,
                plugin_id=self.user_options["volume_csi_plugin_id"],
                parameters=parameters,
                min_size=min_size,
            )
            volume_data = JobVolumeData(
                type="csi",
                destination=self.user_options["volume_destination"],
                source=volume_id,
            )
        elif volume_type == "host":
            volume_data = JobVolumeData(
                type="host",
                destination=self.user_options["volume_destination"],
                source=self.user_options["volume_source"],
            )

        return volume_data

    def _get_csi_extra_parameters(self) -> Optional[Dict]:
        parameters: Optional[Dict] = None
        if callable(self.csi_volume_parameters):
            parameters = self.csi_volume_parameters(self)
        else:
            parameters = self.csi_volume_parameters
        return parameters

    async def _ensure_running(self, nomad_service: NomadService):
        while True:
            try:
                status = await nomad_service.job_status(self.job_name)
            except Exception:
                self.log.exception("Failed to get job status")
            if status == "running":
                break
            elif status == "dead":
                raise Exception(f"Job (name={self.job_name}) is dead already")
            else:
                self.log.info("Waiting for %s...", self.job_name)
                await asyncio.sleep(5)

    @retry(wait=wait_fixed(3), stop=stop_after_attempt(5))
    async def service(self, consul_service: ConsulService):

        self.log.info("Getting service %s from consul", self.service_name)
        nodes = await consul_service.health_service(self.service_name)

        address = nodes[0]["Service"]["Address"]
        port = nodes[0]["Service"]["Port"]

        # address = "host.docker.internal"
        return (address, port)

    async def poll(self):

        nomad_httpx_client = build_nomad_httpx_client(
            build_nomad_config_from_options(self)
        )

        nomad_service = NomadService(client=nomad_httpx_client, log=self.log)
        try:
            status = await nomad_service.job_status(self.job_name)

            running = status == "running"
            if not running:
                self.log.warning(
                    "jupyter notebook not running (%s): %s", self.job_name, status
                )
                return status
            return None
        except Exception:
            self.log.exception("Failed to poll")
            return -1
        finally:
            if nomad_httpx_client:
                await nomad_httpx_client.aclose()

    async def stop(self):

        nomad_service_config = build_nomad_config_from_options(self)
        nomad_httpx_client = build_nomad_httpx_client(nomad_service_config)
        nomad_service = NomadService(client=nomad_httpx_client, log=self.log)

        try:
            await nomad_service.delete_job(self.job_name)
            self.clear_state()
        except Exception:
            self.log.exception("Failed to stop")
        finally:
            if nomad_httpx_client is not None:
                await nomad_httpx_client.aclose()

    def get_state(self):
        """get the current state"""
        state = super().get_state()
        state["notebook_id"] = self.notebook_id

        return state

    def load_state(self, state):
        """load state from the database"""
        super().load_state(state)
        if "notebook_id" in state:
            self.notebook_id = state["notebook_id"]

    def clear_state(self):
        """clear any state (called after shutdown)"""
        super().clear_state()
        self.notebook_id = None

    @property
    def options_form(self) -> str:
        """return the options for the form"""

        return create_form(
            datacenters=self.datacenters,
            common_images=self.common_images,
            memory_limit=self.memory_limit_in_mb,
            csi_plugin_ids=self.csi_plugin_ids,
        )

    @property
    def memory_limit_in_mb(self) -> Optional[int]:
        return self.mem_limit / (1024 * 1024) if self.mem_limit else None

    def options_from_form(self, formdata):
        options = {}
        options["image"] = formdata["image"][0]
        options["datacenters"] = formdata["datacenters"]
        options["memory"] = int(formdata["memory"][0])
        options["volume_type"] = formdata["volume_type"][0]
        options["volume_source"] = formdata.get("volume_source", [None])[0]
        options["volume_destination"] = formdata.get("volume_destination", [None])[0]
        options["volume_csi_plugin_id"] = formdata.get("volume_csi_plugin_id", [None])[
            0
        ]

        if self.memory_limit_in_mb and self.memory_limit_in_mb <= options["memory"]:
            err = f"Only {self.memory_limit_in_mb} allowed"
            raise Exception(err)
        if not all(x in self.datacenters for x in options["datacenters"]):
            err = f"Invalid Datacenters list {options['datacenters']}"
            raise Exception(err)
        if (
            options["volume_type"] == "csi"
            and options["volume_csi_plugin_id"] not in self.csi_plugin_ids
        ):
            err = f"Invalid CSI Plugin {options['volume_csi_plugin_id']}"
            raise Exception(err)

        return options


def build_nomad_config_from_options(options: NomadSpawner) -> NomadServiceConfig:
    return NomadServiceConfig(
        nomad_addr=options.nomad_addr,
        nomad_token=options.nomad_token,
        tls_config=NomadTLSConfig(
            ca_cert=options.nomad_ca_cert,
            ca_path=options.nomad_ca_path,
            client_cert=options.nomad_client_cert,
            client_key=options.nomad_client_key,
            skip_verify=options.nomad_tls_skip_verify,
            tls_server_name=options.nomad_tls_server_name,
        )
        if options.nomad_client_key
        else None,
    )


def build_consul_config_from_options(options: NomadSpawner) -> ConsulServiceConfig:
    return ConsulServiceConfig(
        consul_http_addr=options.consul_http_addr,
        consul_http_token=options.consul_http_token,
        tls_config=ConsulTLSConfig(
            ca_cert=options.consul_ca_cert,
            ca_path=options.consul_ca_path,
            client_cert=options.consul_client_cert,
            client_key=options.consul_client_key,
            skip_verify=options.consul_tls_skip_verify,
            tls_server_name=options.consul_tls_server_name,
        )
        if options.consul_client_key
        else None,
    )


def build_nomad_httpx_client(config: NomadServiceConfig) -> AsyncClient:

    verify: Union[bool, ssl.SSLContext] = True
    cert: Optional[Tuple[str, str]] = None
    if config.tls_config:
        cert = (
            str(config.tls_config.client_cert.resolve()),
            str(config.tls_config.client_key.resolve()),
        )

        if not config.tls_config.skip_verify and config.tls_config.ca_cert:
            ca_cert = config.tls_config.ca_cert.resolve()
            context = ssl.create_default_context()
            context.load_verify_locations(cafile=ca_cert)
            verify = context
        else:
            verify = False
    client = AsyncClient(
        base_url=config.nomad_addr,
        verify=verify,
        cert=cert,
        headers={"X-Nomad-Token": config.nomad_token} if config.nomad_token else None,
    )
    return client


def build_consul_httpx_client(config: ConsulServiceConfig) -> AsyncClient:

    verify: Union[bool, ssl.SSLContext] = True
    cert: Optional[Tuple[str, str]] = None
    if config.tls_config:
        cert = (
            str(config.tls_config.client_cert.resolve()),
            str(config.tls_config.client_key.resolve()),
        )

        if not config.tls_config.skip_verify and config.tls_config.ca_cert:
            ca_cert = config.tls_config.ca_cert.resolve()
            context = ssl.create_default_context()
            context.load_verify_locations(cafile=ca_cert)
            verify = context
        else:
            verify = False
    client = AsyncClient(
        base_url=config.consul_http_addr,
        verify=verify,
        cert=cert,
        headers={"X-Consul-Token": config.consul_http_token}
        if config.consul_http_token
        else None,
    )
    return client
