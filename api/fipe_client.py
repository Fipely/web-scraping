# -*- coding: utf-8 -*-
"""
Cliente HTTP para comunicação com a API FIPE.
Implementa retry com exponential backoff e rate limiting.
"""

import time
from typing import Any, Dict, Optional

import requests
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log
)

from utils.config import Config
from utils.logger import setup_logger
from api.endpoints import Endpoints


logger = setup_logger("fipe_client")


class FipeClientError(Exception):
    """Exceção base para erros do cliente FIPE."""
    pass


class FipeRateLimitError(FipeClientError):
    """Exceção para quando o rate limit é atingido."""
    pass


class FipeRequestError(FipeClientError):
    """Exceção para erros de requisição."""
    pass


class FipeClient:
    """
    Cliente para comunicação com a API FIPE.
    Implementa retry com exponential backoff para lidar com bloqueios.
    """

    def __init__(self):
        """
        Inicializa o cliente com as configurações do ambiente.
        """
        self.base_url = Config.FIPE_BASE_URL
        self.headers = Config.get_headers()
        self.timeout = Config.REQUEST_TIMEOUT
        self.delay = Config.DELAY_BETWEEN_REQUESTS
        self._last_request_time = 0
        self._session = requests.Session()
        self._session.headers.update(self.headers)

    def _wait_for_rate_limit(self) -> None:
        """
        Aguarda o tempo necessário para respeitar o rate limit.
        """
        elapsed = time.time() - self._last_request_time

        if elapsed < self.delay:
            sleep_time = self.delay - elapsed
            time.sleep(sleep_time)

        self._last_request_time = time.time()

    @retry(
        stop=stop_after_attempt(Config.MAX_RETRIES),
        wait=wait_exponential(
            multiplier=Config.BACKOFF_MULTIPLIER,
            min=Config.INITIAL_BACKOFF,
            max=Config.MAX_BACKOFF
        ),
        retry=retry_if_exception_type((
            FipeRateLimitError,
            requests.exceptions.ConnectionError,
            requests.exceptions.Timeout
        )),
        before_sleep=before_sleep_log(logger, log_level=20)  # INFO level
    )
    def _make_request(
        self,
        endpoint: str,
        payload: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Realiza uma requisição POST para a API FIPE.

        Args:
            endpoint: Nome do endpoint
            payload: Dados para enviar no corpo da requisição

        Returns:
            Dict[str, Any]: Resposta da API

        Raises:
            FipeRateLimitError: Se o rate limit for atingido
            FipeRequestError: Se houver erro na requisição
        """
        self._wait_for_rate_limit()

        url = f"{self.base_url}{endpoint}"

        try:
            response = self._session.post(
                url,
                json=payload or {},
                timeout=self.timeout
            )

            # Verifica rate limit (status 429 ou mensagem de erro específica)
            if response.status_code == 429:
                logger.warning(f"Rate limit atingido no endpoint {endpoint}")
                raise FipeRateLimitError("Rate limit atingido")

            # Verifica outros erros HTTP
            if response.status_code != 200:
                logger.error(
                    f"Erro HTTP {response.status_code} no endpoint {endpoint}: "
                    f"{response.text[:200]}"
                )

                # Se for erro de servidor, tenta novamente
                if response.status_code >= 500:
                    raise FipeRateLimitError(f"Erro de servidor: {response.status_code}")

                raise FipeRequestError(
                    f"Erro HTTP {response.status_code}: {response.text[:200]}"
                )

            # Tenta parsear o JSON
            try:
                data = response.json()
            except ValueError as e:
                logger.error(f"Erro ao parsear JSON do endpoint {endpoint}: {e}")
                raise FipeRequestError(f"Resposta inválida: {response.text[:200]}")

            # Verifica se há erro na resposta da API
            if isinstance(data, dict) and "erro" in data:
                error_msg = data.get("erro", "Erro desconhecido")
                logger.warning(f"Erro na API FIPE: {error_msg}")

                # Alguns erros indicam rate limiting
                if "timeout" in error_msg.lower() or "blocked" in error_msg.lower():
                    raise FipeRateLimitError(error_msg)

                raise FipeRequestError(error_msg)

            return data

        except requests.exceptions.Timeout:
            logger.warning(f"Timeout na requisição para {endpoint}")
            raise
        except requests.exceptions.ConnectionError as e:
            logger.warning(f"Erro de conexão para {endpoint}: {e}")
            raise

    def get_reference_tables(self) -> list:
        """
        Obtém todas as tabelas de referência (períodos) disponíveis.

        Returns:
            list: Lista de períodos de referência
                  [{"Codigo": 1, "Mes": "janeiro/2024"}, ...]
        """
        logger.info("Consultando tabelas de referência...")
        return self._make_request(Endpoints.REFERENCE_TABLES)

    def get_brands(
        self,
        reference_table_code: int,
        vehicle_type: int
    ) -> list:
        """
        Obtém todas as marcas para um tipo de veículo em um período.

        Args:
            reference_table_code: Código da tabela de referência
            vehicle_type: Código do tipo de veículo (1=carro, 2=moto, 3=caminhão)

        Returns:
            list: Lista de marcas [{"Label": "FIAT", "Value": "21"}, ...]
        """
        logger.debug(
            f"Consultando marcas - Ref: {reference_table_code}, Tipo: {vehicle_type}"
        )

        payload = {
            "codigoTabelaReferencia": reference_table_code,
            "codigoTipoVeiculo": vehicle_type
        }

        return self._make_request(Endpoints.BRANDS, payload)

    def get_models(
        self,
        reference_table_code: int,
        vehicle_type: int,
        brand_code: int
    ) -> Dict[str, Any]:
        """
        Obtém todos os modelos de uma marca.

        Args:
            reference_table_code: Código da tabela de referência
            vehicle_type: Código do tipo de veículo
            brand_code: Código da marca

        Returns:
            Dict: {"Modelos": [...], "Anos": [...]}
        """
        logger.debug(
            f"Consultando modelos - Ref: {reference_table_code}, "
            f"Tipo: {vehicle_type}, Marca: {brand_code}"
        )

        payload = {
            "codigoTabelaReferencia": reference_table_code,
            "codigoTipoVeiculo": vehicle_type,
            "codigoMarca": brand_code
        }

        return self._make_request(Endpoints.MODELS, payload)

    def get_year_models(
        self,
        reference_table_code: int,
        vehicle_type: int,
        brand_code: int,
        model_code: int
    ) -> list:
        """
        Obtém todos os anos-modelo de um modelo específico.

        Args:
            reference_table_code: Código da tabela de referência
            vehicle_type: Código do tipo de veículo
            brand_code: Código da marca
            model_code: Código do modelo

        Returns:
            list: Lista de anos-modelo [{"Label": "2024", "Value": "2024-1"}, ...]
        """
        logger.debug(
            f"Consultando anos-modelo - Modelo: {model_code}"
        )

        payload = {
            "codigoTabelaReferencia": reference_table_code,
            "codigoTipoVeiculo": vehicle_type,
            "codigoMarca": brand_code,
            "codigoModelo": model_code
        }

        return self._make_request(Endpoints.YEAR_MODELS, payload)

    def get_fipe_value(
        self,
        reference_table_code: int,
        vehicle_type: int,
        brand_code: int,
        model_code: int,
        year_model: str,
        fuel_type_code: int = 1
    ) -> Dict[str, Any]:
        """
        Obtém o valor FIPE de um veículo específico.

        Args:
            reference_table_code: Código da tabela de referência
            vehicle_type: Código do tipo de veículo
            brand_code: Código da marca
            model_code: Código do modelo
            year_model: Código do ano-modelo (ex: "2024-1")
            fuel_type_code: Código do tipo de combustível (padrão: 1)

        Returns:
            Dict: Dados completos do valor FIPE
        """
        logger.debug(
            f"Consultando valor FIPE - Modelo: {model_code}, Ano: {year_model}"
        )

        # Separa ano e combustível do código
        year_parts = year_model.split("-")
        ano_modelo = year_parts[0]
        tipo_combustivel = int(year_parts[1]) if len(year_parts) > 1 else fuel_type_code

        payload = {
            "codigoTabelaReferencia": reference_table_code,
            "codigoTipoVeiculo": vehicle_type,
            "codigoMarca": brand_code,
            "codigoModelo": model_code,
            "anoModelo": ano_modelo,
            "codigoTipoCombustivel": tipo_combustivel,
            "tipoConsulta": "tradicional"
        }

        return self._make_request(Endpoints.FIPE_VALUE, payload)

    def close(self) -> None:
        """
        Fecha a sessão HTTP.
        """
        self._session.close()
        logger.debug("Sessão HTTP fechada")

    def __enter__(self):
        """Permite uso com context manager."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Fecha a sessão ao sair do context manager."""
        self.close()
