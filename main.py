# -*- coding: utf-8 -*-
"""
FIPE Web Scraper - Ponto de entrada principal.

Este módulo fornece a classe principal FipeScraper que orquestra toda a
extração de dados da tabela FIPE.

Uso:
    from main import FipeScraper

    # Extrai todos os dados
    scraper = FipeScraper()
    scraper.run()

    # Extrai período específico para carros
    scraper = FipeScraper(
        start_period="01/2024",
        end_period="06/2024",
        vehicle_types=["car"]
    )
    scraper.run()
"""

import json
from pathlib import Path
from typing import List, Optional

from scrapers.orchestrator import Orchestrator
from models.fipe_models import ExtractionResult
from utils.config import Config
from utils.logger import setup_logger
from utils.file_handler import FileHandler


logger = setup_logger("main")


class FipeScraper:
    """
    Classe principal para extração de dados da tabela FIPE.

    Esta classe encapsula toda a lógica de extração, incluindo:
    - Consulta de períodos de referência
    - Extração de marcas, modelos e anos-modelo
    - Consulta de valores FIPE
    - Processamento paralelo com multiprocessing
    - Persistência em arquivos JSON

    Attributes:
        start_period: Período inicial no formato MM/yyyy
        end_period: Período final no formato MM/yyyy
        vehicle_types: Lista de tipos de veículos (car, bike, truck)
    """

    def __init__(
        self,
        start_period: Optional[str] = None,
        end_period: Optional[str] = None,
        vehicle_types: Optional[List[str]] = None,
        use_multiprocessing: bool = True
    ):
        """
        Inicializa o scraper FIPE.

        Args:
            start_period: Período inicial no formato MM/yyyy (ex: "01/2024").
                         Se None, usa o período mais antigo disponível.
            end_period: Período final no formato MM/yyyy (ex: "12/2024").
                       Se None, usa o período mais recente disponível.
            vehicle_types: Lista de tipos de veículos a extrair.
                          Valores válidos: "car", "bike", "truck".
                          Se None, extrai todos os tipos.
            use_multiprocessing: Se True, usa multiprocessing para extração paralela.
                                Se False, executa sequencialmente (mais lento, mas mais estável).

        Raises:
            ValueError: Se o formato dos períodos for inválido.
            ValueError: Se algum tipo de veículo for inválido.

        Example:
            >>> # Extrai todos os dados disponíveis
            >>> scraper = FipeScraper()

            >>> # Extrai apenas carros do primeiro semestre de 2024
            >>> scraper = FipeScraper(
            ...     start_period="01/2024",
            ...     end_period="06/2024",
            ...     vehicle_types=["car"]
            ... )
        """
        # Valida formato dos períodos
        if start_period:
            self._validate_period_format(start_period)
        if end_period:
            self._validate_period_format(end_period)

        # Valida tipos de veículos
        if vehicle_types:
            valid_types = {"car", "bike", "truck", "carro", "moto", "caminhao", "caminhão"}
            for vt in vehicle_types:
                if vt.lower() not in valid_types:
                    raise ValueError(
                        f"Tipo de veículo inválido: {vt}. "
                        f"Valores válidos: car, bike, truck"
                    )

        self.start_period = start_period
        self.end_period = end_period
        self.vehicle_types = vehicle_types
        self.use_multiprocessing = use_multiprocessing

        logger.info(
            f"FipeScraper inicializado: "
            f"período={start_period or 'início'} a {end_period or 'atual'}, "
            f"tipos={vehicle_types or 'todos'}, multiprocessing={use_multiprocessing}"
        )

    def _validate_period_format(self, period: str) -> None:
        """
        Valida o formato de um período (MM/yyyy).

        Args:
            period: Período a validar

        Raises:
            ValueError: Se o formato for inválido
        """
        if not period:
            return

        parts = period.split("/")

        if len(parts) != 2:
            raise ValueError(
                f"Formato de período inválido: {period}. "
                f"Use o formato MM/yyyy (ex: 01/2024)"
            )

        month, year = parts

        try:
            month_int = int(month)
            year_int = int(year)

            if not (1 <= month_int <= 12):
                raise ValueError(f"Mês inválido: {month}")

            if year_int < 2000 or year_int > 2100:
                raise ValueError(f"Ano inválido: {year}")

        except ValueError as e:
            if "inválido" in str(e).lower():
                raise
            raise ValueError(
                f"Formato de período inválido: {period}. "
                f"Use o formato MM/yyyy (ex: 01/2024)"
            )

    def run(self) -> ExtractionResult:
        """
        Executa a extração completa de dados da FIPE.

        Este método:
        1. Consulta os períodos de referência disponíveis
        2. Extrai todas as marcas para cada tipo de veículo
        3. Para cada marca, extrai modelos e anos-modelo
        4. Consulta valores FIPE para cada combinação
        5. Salva os dados em arquivos JSON parciais
        6. Consolida tudo no arquivo final

        Returns:
            ExtractionResult: Objeto contendo todos os dados extraídos

        Raises:
            Exception: Se ocorrer erro crítico durante a extração

        Example:
            >>> scraper = FipeScraper(start_period="01/2024")
            >>> result = scraper.run()
            >>> print(f"Extraídos {len(result.brands)} marcas")
        """
        logger.info("=" * 60)
        logger.info("Iniciando extração de dados da FIPE")
        logger.info("=" * 60)

        # Cria diretórios de saída
        self._ensure_output_directories()

        # Cria e executa o orquestrador
        orchestrator = Orchestrator(
            start_period=self.start_period,
            end_period=self.end_period,
            vehicle_types=self.vehicle_types,
            use_multiprocessing=self.use_multiprocessing
        )

        result = orchestrator.run()

        # Salva resultado final
        self._save_final_result(result)

        logger.info("=" * 60)
        logger.info("Extração concluída com sucesso!")
        logger.info(f"Períodos: {len(result.reference_periods)}")
        logger.info(f"Marcas: {len(result.brands)}")
        logger.info(f"Modelos: {len(result.models)}")
        logger.info(f"Anos-modelo: {len(result.year_models)}")
        logger.info(f"Valores FIPE: {len(result.fipe_values)}")
        logger.info("=" * 60)

        return result

    def _ensure_output_directories(self) -> None:
        """
        Garante que os diretórios de saída existem.
        """
        output_dir = Path(Config.OUTPUT_DIR)
        partial_dir = Path(Config.PARTIAL_OUTPUT_DIR)

        output_dir.mkdir(parents=True, exist_ok=True)
        partial_dir.mkdir(parents=True, exist_ok=True)

        logger.debug(f"Diretórios de saída criados: {output_dir}, {partial_dir}")

    def _save_final_result(self, result: ExtractionResult) -> None:
        """
        Salva o resultado final em arquivo JSON.

        Args:
            result: Resultado da extração
        """
        output_path = Config.get_final_output_path()

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(result.to_dict(), f, ensure_ascii=False, indent=2)

        logger.info(f"Resultado final salvo em: {output_path}")

    @staticmethod
    def finalize() -> None:
        """
        Consolida todos os arquivos parciais no arquivo final.

        Use este método quando a extração foi interrompida e você
        deseja consolidar os dados já extraídos.

        Example:
            >>> FipeScraper.finalize()
        """
        logger.info("Consolidando arquivos parciais...")
        FileHandler.consolidate_partials()
        logger.info("Consolidação concluída")


# Ponto de entrada para execução direta
if __name__ == "__main__":
    # Exemplo de uso: extrai dados do período atual para todos os tipos
    scraper = FipeScraper()
    scraper.run()
