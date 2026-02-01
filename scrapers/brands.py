# -*- coding: utf-8 -*-
"""
Scraper para extração de marcas de veículos da tabela FIPE.
"""

from typing import Dict, List, Optional, Set

from scrapers.base_scraper import BaseScraper
from api.fipe_client import FipeClient
from api.endpoints import VehicleType
from models.fipe_models import Brand, ReferencePeriod


class BrandScraper(BaseScraper):
    """
    Scraper responsável por extrair as marcas de veículos.
    Identifica também o período inicial de cada marca.
    """

    def extract(
        self,
        periods: List[ReferencePeriod],
        vehicle_types: Optional[List[int]] = None
    ) -> List[Brand]:
        """
        Extrai todas as marcas para os tipos de veículos especificados.

        Args:
            periods: Lista de períodos de referência para buscar marcas
            vehicle_types: Lista de tipos de veículos (padrão: todos)

        Returns:
            List[Brand]: Lista de marcas extraídas
        """
        if vehicle_types is None:
            vehicle_types = VehicleType.all_types()

        self.logger.info(
            f"Iniciando extração de marcas para {len(periods)} períodos "
            f"e {len(vehicle_types)} tipos de veículos..."
        )

        # Dicionário para rastrear marcas e seus períodos iniciais
        # Chave: (nome_marca, tipo_veiculo), Valor: (brand, periodo_inicial)
        brands_dict: Dict[tuple, tuple] = {}

        # Ordena períodos do mais antigo para o mais recente
        # para identificar corretamente o período inicial de cada marca
        sorted_periods = sorted(periods, key=lambda p: p.period)

        total_iterations = len(sorted_periods) * len(vehicle_types)
        current_iteration = 0

        for period in sorted_periods:
            for vehicle_type_code in vehicle_types:
                current_iteration += 1
                vehicle_type_str = VehicleType.to_string(vehicle_type_code)

                try:
                    raw_brands = self.client.get_brands(
                        reference_table_code=period.code,
                        vehicle_type=vehicle_type_code
                    )
                except Exception as e:
                    self.logger.error(
                        f"Erro ao extrair marcas para período {period.period}, "
                        f"tipo {vehicle_type_str}: {e}"
                    )
                    continue

                for item in raw_brands:
                    brand = Brand.from_api_response(
                        data=item,
                        vehicle_type=vehicle_type_str,
                        initial_period=period.period
                    )

                    key = (brand.name, brand.vehicle_type)

                    # Só adiciona se for a primeira vez que vemos essa marca
                    # (como os períodos estão ordenados do mais antigo)
                    if key not in brands_dict:
                        brands_dict[key] = brand

                # Log de progresso a cada 10 iterações
                if current_iteration % 10 == 0:
                    self._log_progress(
                        current_iteration,
                        total_iterations,
                        "marcas"
                    )

        brands = list(brands_dict.values())
        self.logger.info(f"Extraídas {len(brands)} marcas únicas")

        return brands

    def extract_for_single_period(
        self,
        period: ReferencePeriod,
        vehicle_type: int
    ) -> List[Brand]:
        """
        Extrai marcas para um único período e tipo de veículo.

        Args:
            period: Período de referência
            vehicle_type: Código do tipo de veículo

        Returns:
            List[Brand]: Lista de marcas
        """
        vehicle_type_str = VehicleType.to_string(vehicle_type)

        self.logger.debug(
            f"Extraindo marcas para período {period.period}, "
            f"tipo {vehicle_type_str}"
        )

        try:
            raw_brands = self.client.get_brands(
                reference_table_code=period.code,
                vehicle_type=vehicle_type
            )
        except Exception as e:
            self.logger.error(f"Erro ao extrair marcas: {e}")
            return []

        brands = []
        seen = set()

        for item in raw_brands:
            brand = Brand.from_api_response(
                data=item,
                vehicle_type=vehicle_type_str,
                initial_period=period.period
            )

            key = (brand.name, brand.vehicle_type)
            if key not in seen:
                brands.append(brand)
                seen.add(key)

        return brands
