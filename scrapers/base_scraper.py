# -*- coding: utf-8 -*-
"""
Classe base abstrata para scrapers.
Define a interface comum que todos os scrapers devem implementar.
"""

from abc import ABC, abstractmethod
from typing import Any, List

from api.fipe_client import FipeClient
from utils.logger import setup_logger


class BaseScraper(ABC):
    """
    Classe base abstrata para todos os scrapers.
    Define a interface comum e funcionalidades compartilhadas.
    """

    def __init__(self, client: FipeClient):
        """
        Inicializa o scraper com um cliente FIPE.

        Args:
            client: Cliente HTTP para comunicação com a API FIPE
        """
        self.client = client
        self.logger = setup_logger(self.__class__.__name__)

    @abstractmethod
    def extract(self, *args, **kwargs) -> Any:
        """
        Método principal de extração.
        Deve ser implementado por cada scraper específico.

        Returns:
            Any: Dados extraídos
        """
        pass

    def _log_progress(self, current: int, total: int, item_name: str) -> None:
        """
        Registra o progresso da extração.

        Args:
            current: Item atual
            total: Total de itens
            item_name: Nome do tipo de item sendo processado
        """
        percentage = (current / total * 100) if total > 0 else 0
        self.logger.info(
            f"Progresso {item_name}: {current}/{total} ({percentage:.1f}%)"
        )
