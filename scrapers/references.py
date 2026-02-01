# -*- coding: utf-8 -*-
"""
Scraper para extração de períodos de referência da tabela FIPE.
"""

from typing import List, Optional, Tuple

from scrapers.base_scraper import BaseScraper
from api.fipe_client import FipeClient
from models.fipe_models import ReferencePeriod


class ReferenceScraper(BaseScraper):
    """
    Scraper responsável por extrair os períodos de referência disponíveis.
    """

    def extract(self) -> List[ReferencePeriod]:
        """
        Extrai todos os períodos de referência disponíveis na API FIPE.

        Returns:
            List[ReferencePeriod]: Lista de períodos de referência
        """
        self.logger.info("Iniciando extração de períodos de referência...")

        try:
            raw_data = self.client.get_reference_tables()
        except Exception as e:
            self.logger.error(f"Erro ao extrair períodos de referência: {e}")
            return []

        periods = []
        seen_periods = set()

        for item in raw_data:
            period = ReferencePeriod.from_api_response(item)

            # Evita duplicatas
            if period.period not in seen_periods:
                periods.append(period)
                seen_periods.add(period.period)

        self.logger.info(f"Extraídos {len(periods)} períodos de referência")
        return periods

    def filter_by_range(
        self,
        periods: List[ReferencePeriod],
        start_period: Optional[str] = None,
        end_period: Optional[str] = None
    ) -> List[ReferencePeriod]:
        """
        Filtra períodos por um intervalo de datas.

        Args:
            periods: Lista de períodos para filtrar
            start_period: Período inicial no formato MM/yyyy (opcional)
            end_period: Período final no formato MM/yyyy (opcional)

        Returns:
            List[ReferencePeriod]: Lista de períodos filtrados
        """
        if not start_period and not end_period:
            return periods

        def parse_period(period_str: str) -> Tuple[int, int]:
            """Converte MM/yyyy para (ano, mês) para comparação."""
            parts = period_str.split("/")
            if len(parts) == 2:
                return (int(parts[1]), int(parts[0]))
            return (0, 0)

        filtered = []

        start_tuple = parse_period(start_period) if start_period else (0, 0)
        end_tuple = parse_period(end_period) if end_period else (9999, 12)

        for period in periods:
            period_tuple = parse_period(period.period)

            if start_tuple <= period_tuple <= end_tuple:
                filtered.append(period)

        self.logger.info(
            f"Filtrados {len(filtered)} períodos de {len(periods)} "
            f"(início: {start_period}, fim: {end_period})"
        )

        return filtered

    def get_period_by_code(
        self,
        periods: List[ReferencePeriod],
        code: int
    ) -> Optional[ReferencePeriod]:
        """
        Busca um período pelo seu código.

        Args:
            periods: Lista de períodos
            code: Código do período

        Returns:
            Optional[ReferencePeriod]: Período encontrado ou None
        """
        for period in periods:
            if period.code == code:
                return period
        return None
