from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    # Database
    database_url: str = "postgresql+asyncpg://jicgeo:devpass@localhost:5432/jicgeo"

    # Environment
    environment: str = "development"

    # Climate API
    climate_api_ttl_seconds: int = 600  # CLI-07: default 10 minutes

    # Risk index
    segment_length_m: float = 100.0  # RUT-01: default segment size
    max_gradient_plausible: float = 0.75  # RUT-10: spike detection threshold
    minetti_domain_min: float = -0.45  # MET-01: Minetti valid domain
    minetti_domain_max: float = 0.45
    climate_cost_cap: float = 3.0  # GRF-10: max climate multiplier

    # AHP weights for risk score (RIE-01) — must sum to 1.0
    ahp_metabolic_cost: float = 0.35
    ahp_velocity_degradation: float = 0.25
    ahp_climate_stress: float = 0.25
    ahp_terrain_friction: float = 0.15

    @property
    def is_development(self) -> bool:
        return self.environment == "development"


settings = Settings()
