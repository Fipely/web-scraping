# -*- coding: utf-8 -*-
"""
Módulo de configuração do projeto.
Carrega variáveis de ambiente do arquivo .env e disponibiliza para o projeto.
"""

import os
from pathlib import Path
from dotenv import load_dotenv


# Carrega o arquivo .env da raiz do projeto
_project_root = Path(__file__).parent.parent
_env_path = _project_root / ".env"
load_dotenv(_env_path)


class Config:
    """
    Classe de configuração centralizada.
    Carrega todas as variáveis de ambiente necessárias para o projeto.
    """

    # URL base da API FIPE
    FIPE_BASE_URL: str = os.getenv("FIPE_BASE_URL", "https://veiculos.fipe.org.br/api/veiculos/")

    # Headers para requisições HTTP
    USER_AGENT: str = os.getenv(
        "USER_AGENT",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )
    REFERER: str = os.getenv("REFERER", "https://veiculos.fipe.org.br/")

    # Configurações de retry com exponential backoff
    MAX_RETRIES: int = int(os.getenv("MAX_RETRIES", "5"))
    INITIAL_BACKOFF: float = float(os.getenv("INITIAL_BACKOFF", "1.0"))
    MAX_BACKOFF: float = float(os.getenv("MAX_BACKOFF", "60.0"))
    BACKOFF_MULTIPLIER: float = float(os.getenv("BACKOFF_MULTIPLIER", "2.0"))
    REQUEST_TIMEOUT: int = int(os.getenv("REQUEST_TIMEOUT", "30"))
    DELAY_BETWEEN_REQUESTS: float = float(os.getenv("DELAY_BETWEEN_REQUESTS", "0.5"))

    # Configurações de processamento paralelo
    MAX_WORKERS: int = int(os.getenv("MAX_WORKERS", "4"))

    # Diretórios e arquivos de saída
    OUTPUT_DIR: str = os.getenv("OUTPUT_DIR", "output")
    PARTIAL_OUTPUT_DIR: str = os.getenv("PARTIAL_OUTPUT_DIR", "output/partial")
    FINAL_OUTPUT_FILE: str = os.getenv("FINAL_OUTPUT_FILE", "output/fipe_complete.json")

    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE: str = os.getenv("LOG_FILE", "output/fipe_scraper.log")

    @classmethod
    def get_headers(cls) -> dict:
        """
        Retorna os headers padrão para requisições HTTP.

        Returns:
            dict: Dicionário com os headers necessários
        """
        return {
            "User-Agent": cls.USER_AGENT,
            "Referer": cls.REFERER,
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Origin": "https://veiculos.fipe.org.br"
        }

    @classmethod
    def get_output_path(cls, filename: str) -> Path:
        """
        Retorna o caminho completo para um arquivo de saída.

        Args:
            filename: Nome do arquivo

        Returns:
            Path: Caminho completo do arquivo
        """
        return _project_root / cls.OUTPUT_DIR / filename

    @classmethod
    def get_partial_output_path(cls, filename: str) -> Path:
        """
        Retorna o caminho completo para um arquivo parcial de saída.

        Args:
            filename: Nome do arquivo

        Returns:
            Path: Caminho completo do arquivo parcial
        """
        return _project_root / cls.PARTIAL_OUTPUT_DIR / filename

    @classmethod
    def get_final_output_path(cls) -> Path:
        """
        Retorna o caminho completo para o arquivo final consolidado.

        Returns:
            Path: Caminho completo do arquivo final
        """
        return _project_root / cls.FINAL_OUTPUT_FILE

    @classmethod
    def get_log_path(cls) -> Path:
        """
        Retorna o caminho completo para o arquivo de log.

        Returns:
            Path: Caminho completo do arquivo de log
        """
        return _project_root / cls.LOG_FILE
