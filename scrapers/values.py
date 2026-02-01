# -*- coding: utf-8 -*-
"""
Scraper para extração de valores FIPE dos veículos.
Inclui extração de anos-modelo e valores completos.
"""

from typing import Dict, List, Optional, Tuple

from scrapers.base_scraper import BaseScraper
from api.fipe_client import FipeClient
from api.endpoints import VehicleType
from models.fipe_models import (
    Brand,
    Model,
    YearModel,
    FipeValue,
    ReferencePeriod
)


class ValueScraper(BaseScraper):
    """
    Scraper responsável por extrair anos-modelo e valores FIPE.
    """

    def extract_year_models(
        self,
        period: ReferencePeriod,
        model: Model
    ) -> List[YearModel]:
        """
        Extrai os anos-modelo disponíveis para um modelo específico.

        Args:
            period: Período de referência
            model: Modelo do veículo

        Returns:
            List[YearModel]: Lista de anos-modelo
        """
        brand = model.brand if isinstance(model.brand, Brand) else None

        if not brand:
            self.logger.error(
                f"Modelo {model.name} não possui marca válida"
            )
            return []

        vehicle_type_code = VehicleType.from_string(model.vehicle_type)

        self.logger.debug(
            f"Extraindo anos-modelo para {brand.name} {model.name}"
        )

        try:
            raw_years = self.client.get_year_models(
                reference_table_code=period.code,
                vehicle_type=vehicle_type_code,
                brand_code=brand.code,
                model_code=model.code
            )
        except Exception as e:
            self.logger.error(
                f"Erro ao extrair anos-modelo de {model.name}: {e}"
            )
            return []

        year_models = []

        for item in raw_years:
            year_model = YearModel.from_api_response(
                data=item,
                model=model,
                authentication=""  # Será preenchido com o código FIPE
            )
            year_models.append(year_model)

        return year_models

    def extract_fipe_value(
        self,
        period: ReferencePeriod,
        year_model: YearModel
    ) -> Optional[FipeValue]:
        """
        Extrai o valor FIPE para um ano-modelo específico.

        Args:
            period: Período de referência
            year_model: Ano-modelo do veículo

        Returns:
            Optional[FipeValue]: Valor FIPE ou None em caso de erro
        """
        model = year_model.model if isinstance(year_model.model, Model) else None

        if not model:
            self.logger.error(
                f"Ano-modelo {year_model.description} não possui modelo válido"
            )
            return None

        brand = model.brand if isinstance(model.brand, Brand) else None

        if not brand:
            self.logger.error(
                f"Modelo {model.name} não possui marca válida"
            )
            return None

        vehicle_type_code = VehicleType.from_string(model.vehicle_type)

        self.logger.debug(
            f"Extraindo valor FIPE para {brand.name} {model.name} "
            f"{year_model.description}"
        )

        try:
            response = self.client.get_fipe_value(
                reference_table_code=period.code,
                vehicle_type=vehicle_type_code,
                brand_code=brand.code,
                model_code=model.code,
                year_model=year_model.year_code
            )
        except Exception as e:
            self.logger.error(
                f"Erro ao extrair valor FIPE de {model.name} "
                f"{year_model.description}: {e}"
            )
            return None

        # Atualiza o ano-modelo com a autenticação
        authentication = response.get("Autenticacao", "")
        year_model.authentication = authentication

        # Atualiza o código FIPE do modelo se ainda não tiver
        fipe_code = response.get("CodigoFipe", "")
        if fipe_code and not model.fipe_code:
            model.fipe_code = fipe_code

        fipe_value = FipeValue.from_api_response(
            data=response,
            year_model=year_model,
            reference_period=period.period
        )

        return fipe_value

    def extract(
        self,
        period: ReferencePeriod,
        models: List[Model]
    ) -> Tuple[List[YearModel], List[FipeValue]]:
        """
        Extrai anos-modelo e valores FIPE para uma lista de modelos.

        Args:
            period: Período de referência
            models: Lista de modelos

        Returns:
            Tuple[List[YearModel], List[FipeValue]]: Anos-modelo e valores FIPE
        """
        self.logger.info(
            f"Iniciando extração de valores FIPE para {len(models)} modelos "
            f"no período {period.period}..."
        )

        all_year_models = []
        all_fipe_values = []

        seen_year_models: set = set()
        seen_fipe_values: set = set()

        for idx, model in enumerate(models, 1):
            # Extrai anos-modelo
            year_models = self.extract_year_models(period, model)

            for year_model in year_models:
                # Extrai valor FIPE para cada ano-modelo
                fipe_value = self.extract_fipe_value(period, year_model)

                if fipe_value:
                    # Evita duplicatas de anos-modelo
                    year_key = year_model.authentication
                    if year_key and year_key not in seen_year_models:
                        all_year_models.append(year_model)
                        seen_year_models.add(year_key)

                    # Evita duplicatas de valores FIPE
                    value_key = (
                        fipe_value.year_model.authentication
                        if isinstance(fipe_value.year_model, YearModel)
                        else "",
                        fipe_value.reference_period
                    )
                    if value_key[0] and value_key not in seen_fipe_values:
                        all_fipe_values.append(fipe_value)
                        seen_fipe_values.add(value_key)

            # Log de progresso a cada 10 modelos
            if idx % 10 == 0:
                self._log_progress(idx, len(models), "valores FIPE")

        self.logger.info(
            f"Extraídos {len(all_year_models)} anos-modelo e "
            f"{len(all_fipe_values)} valores FIPE"
        )

        return all_year_models, all_fipe_values

    def extract_for_brand(
        self,
        period: ReferencePeriod,
        brand: Brand,
        models: List[Model]
    ) -> Tuple[List[YearModel], List[FipeValue]]:
        """
        Extrai valores FIPE para todos os modelos de uma marca.

        Args:
            period: Período de referência
            brand: Marca dos veículos
            models: Lista de modelos da marca

        Returns:
            Tuple[List[YearModel], List[FipeValue]]: Anos-modelo e valores FIPE
        """
        # Filtra modelos da marca
        brand_models = [
            m for m in models
            if isinstance(m.brand, Brand) and m.brand.name == brand.name
        ]

        return self.extract(period, brand_models)
