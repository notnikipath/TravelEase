from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    service_name: str = "service"
    service_port: int = 8500
    jwt_secret: str = "travelease-dev-secret"

    gateway_url: str = "http://api-gateway:8500"
    search_service_url: str = "http://search-service:8501"
    booking_service_url: str = "http://booking-service:8502"
    content_service_url: str = "http://content-service:8503"
    pricing_service_url: str = "http://pricing-service:8504"
    loyalty_service_url: str = "http://loyalty-service:8505"
    analytics_service_url: str = "http://analytics-service:8506"
    notification_service_url: str = "http://notification-service:8507"

    redis_url: str = "redis://redis:6379/0"
    rabbitmq_url: str = "amqp://guest:guest@rabbitmq:5672/"
    elasticsearch_url: str = "http://elasticsearch:9200"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")
