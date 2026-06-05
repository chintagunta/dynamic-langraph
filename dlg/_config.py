from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, model_validator


class TelemetryConfig(BaseModel):
    enabled: bool
    provider: Literal["langsmith", "custom"]
    module_path: str | None = None
    class_name: str | None = None


class SettingsConfig(BaseModel):
    recursion_limit: int = 1000
    max_concurrency: int | None = None
    telemetry: TelemetryConfig | None = None


class SchemaRef(BaseModel):
    module_path: str
    class_name: str


class FieldSpec(BaseModel):
    type: str
    reducer: str | None = None


class StateDefinitionConfig(BaseModel):
    type: Literal["pydantic", "typed_dict", "dataclass"]
    module_path: str
    class_name: str
    input_schema: SchemaRef | None = None
    output_schema: SchemaRef | None = None
    context_schema: SchemaRef | None = None
    fields: dict[str, FieldSpec] | None = None
    use_messages_preset: bool = False


class RetryPolicyConfig(BaseModel):
    max_attempts: int = 3
    initial_interval: float = 1.0
    backoff_factor: float = 2.0
    retryable_exceptions: list[str] = Field(default_factory=list)


class HandlerRef(BaseModel):
    module_path: str
    function_name: str


class SubgraphRef(BaseModel):
    module_path: str
    graph_name: str


class CachePolicyConfig(BaseModel):
    ttl: float | None = None
    key_func: str | None = None


class NodeConfig(BaseModel):
    name: str
    handler: HandlerRef | None = None
    subgraph: SubgraphRef | None = None
    retry_policy: RetryPolicyConfig | None = None
    timeout_seconds: float | None = None
    interrupt_before: bool = False
    interrupt_after: bool = False
    cache_policy: CachePolicyConfig | None = None
    fallback_node: str | None = None
    send_api: bool = False

    @model_validator(mode="after")
    def check_handler_or_subgraph(self) -> NodeConfig:
        if self.handler is None and self.subgraph is None:
            raise ValueError(f"Node '{self.name}' must have either 'handler' or 'subgraph'")
        if self.handler is not None and self.subgraph is not None:
            raise ValueError(f"Node '{self.name}' cannot have both 'handler' and 'subgraph'")
        return self


class StaticEdge(BaseModel):
    from_node: str = Field(alias="from")
    to_node: str = Field(alias="to")

    model_config = {"populate_by_name": True}


class ConditionalEdge(BaseModel):
    from_node: str = Field(alias="from")
    router: HandlerRef | None = None
    path_map: dict[str, str] | None = None
    send_router: HandlerRef | None = None

    model_config = {"populate_by_name": True}


class EdgeConfig(BaseModel):
    entry_point: str
    static_edges: list[StaticEdge] = Field(default_factory=list)
    conditional_edges: list[ConditionalEdge] = Field(default_factory=list)


class CheckpointerConfig(BaseModel):
    type: Literal["memory", "sqlite", "custom"]
    module_path: str | None = None
    class_name: str | None = None
    db_path: str | None = None


class CacheConfig(BaseModel):
    enabled: bool
    type: Literal["memory", "custom"]
    module_path: str | None = None
    class_name: str | None = None


class SecurityConfig(BaseModel):
    allowed_module_prefixes: list[str] = Field(default_factory=list)


class GlobalDefaultsConfig(BaseModel):
    retry_policy: RetryPolicyConfig | None = None
    timeout_seconds: float | None = None


class GraphConfig(BaseModel):
    graph_id: str
    version: str
    settings: SettingsConfig = Field(default_factory=SettingsConfig)
    state_definition: StateDefinitionConfig
    global_defaults: GlobalDefaultsConfig = Field(default_factory=GlobalDefaultsConfig)
    checkpointer: CheckpointerConfig | None = None
    cache: CacheConfig | None = None
    nodes: list[NodeConfig]
    edges: EdgeConfig
    security: SecurityConfig | None = None
