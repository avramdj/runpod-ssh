from pydantic import BaseModel, Field


class Port(BaseModel):
    ip: str | None = None
    is_ip_public: bool = Field(alias="isIpPublic")
    public_port: int | None = Field(alias="publicPort")


class Runtime(BaseModel):
    ports: list[Port]


class Pod(BaseModel):
    name: str
    runtime: Runtime | None = None


class PodResponse(BaseModel):
    myself: dict[str, list[Pod]]
