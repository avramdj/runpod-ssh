from pydantic import BaseModel, Field


class Port(BaseModel):
    ip: str | None = None
    is_ip_public: bool = Field(alias="isIpPublic")
    private_port: int | None = Field(alias="privatePort")
    public_port: int | None = Field(alias="publicPort")
    type: str


class GPU(BaseModel):
    id: str
    gpu_util_percent: float = Field(alias="gpuUtilPercent")
    memory_util_percent: float = Field(alias="memoryUtilPercent")


class Container(BaseModel):
    cpu_percent: float = Field(alias="cpuPercent")
    memory_percent: float = Field(alias="memoryPercent")


class Runtime(BaseModel):
    uptime_in_seconds: int = Field(alias="uptimeInSeconds")
    ports: list[Port]
    gpus: list[GPU]
    container: Container


class Pod(BaseModel):
    id: str
    name: str
    runtime: Runtime | None = None


class PodResponse(BaseModel):
    myself: dict[str, list[Pod]]
