
from aiohttp import ClientSession


async def launch_job(job_hcl:str):
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