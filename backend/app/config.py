from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8', extra='ignore')

    app_name: str = 'CRM Prom API'
    database_url: str
    admin_user: str
    admin_pass: str
    secret_key: str
    cors_origin: str = '*'
    prom_api_token: str | None = None
    prom_api_base_url: str = 'https://my.prom.ua/api/v1'
    prom_products_endpoint: str = '/products/list'
    prom_orders_endpoint: str = '/orders/list'
    prom_page_size: int = 100
    prom_max_pages: int = 50

    r2_account_id: str | None = None
    r2_access_key_id: str | None = None
    r2_secret_access_key: str | None = None
    r2_bucket: str | None = None
    r2_endpoint: str | None = None


settings = Settings()
