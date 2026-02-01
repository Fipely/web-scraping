# -*- coding: utf-8 -*-
"""
Scraper para extração de modelos de veículos da tabela FIPE.
"""

from typing import Dict, List, Optional, Tuple

from scrapers.base_scraper import BaseScraper
from api.fipe_client import FipeClient
from api.endpoints import VehicleType
from models.fipe_models import Brand, Model, ReferencePeriod


class ModelScraper(BaseScraper):
    """
    Scraper responsável por extrair os modelos de veículos.
    """

    def extract(
        self,
        period: ReferencePeriod,
        brands: List[Brand]
    ) -> List[Model]:
        """
        Extrai todos os modelos para as marcas especificadas.

        Args:
            period: Período de referência
            brands: Lista de marcas para buscar modelos

        Returns:
            List[Model]: Lista de modelos extraídos
        """
        self.logger.info(
            f"Iniciando extração de modelos para {len(brands)} marcas "
            f"no período {period.period}..."
        )

        models = []
        seen_models: set = set()

        for idx, brand in enumerate(brands, 1):
            brand_models = self.extract_for_brand(period, brand)

            for model in brand_models:
                key = (model.fipe_code, model.vehicle_type)
                if key not in seen_models:
                    models.append(model)
                    seen_models.add(key)

            # Log de progresso a cada 5 marcas
            if idx % 5 == 0:
                self._log_progress(idx, len(brands), "modelos por marca")

        self.logger.info(f"Extraídos {len(models)} modelos únicos")
        return models

    def extract_for_brand(
        self,
        period: ReferencePeriod,
        brand: Brand
    ) -> List[Model]:
        """
        Extrai modelos para uma marca específica.

        Args:
            period: Período de referência
            brand: Marca para buscar modelos

        Returns:
            List[Model]: Lista de modelos da marca
        """
        vehicle_type_code = VehicleType.from_string(brand.vehicle_type)

        self.logger.debug(
            f"Extraindo modelos da marca {brand.name} ({brand.vehicle_type})"
        )

        try:
            response = self.client.get_models(
                reference_table_code=period.code,
                vehicle_type=vehicle_type_code,
                brand_code=brand.code
            )
        except Exception as e:
            self.logger.error(
                f"Erro ao extrair modelos da marca {brand.name}: {e}"
            )
            return []

        models = []
        raw_models = response.get("Modelos", [])

        for item in raw_models:
            # O código FIPE completo será obtido quando consultarmos o valor
            # Por enquanto, usamos um placeholder
            model = Model.from_api_response(
                data=item,
                brand=brand,
                vehicle_type=brand.vehicle_type,
                fipe_code=""  # Será preenchido depois
            )
            models.append(model)

        return models

    def get_models_with_fipe_codes(
        self,
        period: ReferencePeriod,
        brand: Brand,
        models: List[Model]
    ) -> List[Model]:
        """
        Atualiza os modelos com seus códigos FIPE.
        Requer consulta de valor para obter o código FIPE.

        Args:
            period: Período de referência
            brand: Marca dos modelos
            models: Lista de modelos sem código FIPE

        Returns:
            List[Model]: Lista de modelos com código FIPE atualizado
        """
        vehicle_type_code = VehicleType.from_string(brand.vehicle_type)
        updated_models = []

        for model in models:
            try:
                # Busca os anos-modelo para obter um ano e consultar o valor
                years_response = self.client.get_year_models(
                    reference_table_code=period.code,
                    vehicle_type=vehicle_type_code,
                    brand_code=brand.code,
                    model_code=model.code
                )

                if not years_response:
                    self.logger.warning(
                        f"Nenhum ano-modelo encontrado para {model.name}"
                    )
                    updated_models.append(model)
                    continue

                # Usa o primeiro ano disponível para consultar o código FIPE
                first_year = years_response[0]

                value_response = self.client.get_fipe_value(
                    reference_table_code=period.code,
                    vehicle_type=vehicle_type_code,
                    brand_code=brand.code,
                    model_code=model.code,
                    year_model=first_year.get("Value", "")
                )

                # Extrai o código FIPE da resposta
                fipe_code = value_response.get("CodigoFipe", "")

                # Cria novo modelo com código FIPE
                updated_model = Model(
                    name=model.name,
                    code=model.code,
                    fipe_code=fipe_code,
                    brand=model.brand,
                    vehicle_type=model.vehicle_type
                )
                updated_models.append(updated_model)

            except Exception as e:
                self.logger.error(
                    f"Erro ao obter código FIPE para {model.name}: {e}"
                )
                updated_models.append(model)

        return updated_models
