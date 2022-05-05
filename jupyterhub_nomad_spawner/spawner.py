import asyncio
import hashlib

from aiohttp import ClientSession
from consul.aio import Consul as AsyncConsul
from jupyterhub.spawner import Spawner
from pydantic import AnyHttpUrl, BaseModel, BaseSettings
from tenacity import retry, stop_after_attempt, wait_fixed
from traitlets import default

from jupyterhub_nomad_spawner.job_factory import create_job


class CreateJobResponse(BaseModel):
    EvalCreateIndex: int
    EvalID: str
    Index: int
    JobModifyIndex: int
    KnownLeader: bool
    LastContact: int
    Warnings: str


class NomadSettings(BaseSettings):
    nomad_addr: AnyHttpUrl = "http://localhost:4646"
    consul_addr_host: str = "localhost"
    consul_addr_port: int = 8500


class NomadSpawner(Spawner):
    @default("ip")
    def _default_ip(self):
        return "192.168.0.52"

    @default("port")
    def _default_port(self):
        return 8888

    async def start(self):

        self.settings = NomadSettings()

        self.log.warning("starting...., %s", str(self.get_env()))
        try:

            user_name = hashlib.sha1(self.user.name.encode('utf-8')).hexdigest()[:10]
            env = { **self.get_env()}
            del env["PATH"]
            del env["PYTHONPATH"]


            args = self.get_args()
            job_hcl = create_job(username=user_name, env=env, args=args)
            payload = {
                "Canonicalize": True,
                "JobHCL": job_hcl,
            }
            print(job_hcl)
            async with ClientSession() as session:

                async with session.post(
                    f"{self.settings.nomad_addr}/v1/jobs/parse", json=payload
                ) as response:
                    json_job = await response.json()
                    self.log.info(f"json_job: {json_job}")
                    self.job_id = json_job["ID"]
                    self.job_name = json_job["Name"]


                async with session.post(
                    f"{self.settings.nomad_addr}/v1/jobs",
                    json={
                        "EnforceIndex": False,
                        "PreserveCounts": True,
                        "PolicyOverride": False,
                        "JobModifyIndex": 0,
                        "Job": json_job,
                    },
                ) as response:
                    text = await response.text()
                    result = await response.json()
                    job_response: CreateJobResponse = CreateJobResponse.parse_obj(
                        result
                    )

                await self._ensure_running(session)

            self.service_name = f"{self.job_id}-notebook"
            service_data = await self.service()
        except Exception as e:
            self.log.exception("Failed to start")
            print(f"Could not start: {str(e)}")
            raise e
        return service_data

    async def _ensure_running(self, session: ClientSession):
        while True:
            try:
                status = await self._job_status(session)
            except Exception as e:
                print(e)
            if status == "running":
                break
            if status == "dead":
                raise Exception(f"Job (id={self.job_id}) is dead already")
            else:
                asyncio.sleep(5)

    async def _job_status(self, session: ClientSession) -> str:
        async with session.get(
            f"{self.settings.nomad_addr}/v1/job/{self.job_id}"
        ) as response:
            job_detail = await response.json()
            return job_detail["Status"]

    @retry(wait=wait_fixed(3), stop=stop_after_attempt(5))
    async def service(self):
        
        consul = AsyncConsul(
            host=self.settings.consul_addr_host,
            port=self.settings.consul_addr_port,
        )
        (index, nodes) = await consul.health.service(self.service_name)

        address = nodes[0]["Service"]["Address"]
        port = nodes[0]["Service"]["Port"]

        # address = "host.docker.internal"
        return (address, port)

    async def poll(self):
        try:
            async with ClientSession() as session:
                status = await self._job_status(session)

            running = status == "running"
            if not running:
                self.log.warning(
                    "jupyter notebook not running (%s): %s", self.job_name, status
                )
                return status
            return None
        except Exception as e:
            self.log.exception("Failed to poll")
            print(f"Could not poll: {str(e)}")
            return -1#str(e)

    async def stop(self):
        async with ClientSession() as session:
            async with session.delete(
                f"{self.settings.nomad_addr}/v1/job/{self.job_id}"
            ) as response:
                response.raise_for_status()
                self.clear_state()

    def get_state(self):
        """get the current state"""
        state = super().get_state()
        state["job_id"] = self.job_id
        state["job_name"] = self.job_name
        state["service_name"] = self.service_name

        return state

    def load_state(self, state):
        """load state from the database"""
        super().load_state(state)
        if "job_id" in state:
            self.job_id = state["job_id"]
        if "job_name" in state:
            self.job_name = state["job_name"]
        if "service_name" in state:
            self.service_name = state["service_name"]

    def clear_state(self):
        """clear any state (called after shutdown)"""
        super().clear_state()
        self.job_id = None
        self.job_name = None
        self.service_name = None

    