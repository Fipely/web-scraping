# -*- coding: utf-8 -*-
"""
Modelos de dados para o projeto FIPE Scraper.
Classes que representam as entidades extraídas da API FIPE.
"""

from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Optional, Dict, Any, List


@dataclass
class ReferencePeriod:
    """
    Representa um período de referência da tabela FIPE.
    Contém apenas o mês/ano no formato MM/yyyy.
    """

    period: str  # Formato: MM/yyyy
    code: int = 0  # Código interno da API FIPE

    def __hash__(self):
        return hash(self.period)

    def __eq__(self, other):
        if not isinstance(other, ReferencePeriod):
            return False
        return self.period == other.period

    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário."""
        return asdict(self)

    @classmethod
    def from_api_response(cls, data: Dict[str, Any]) -> "ReferencePeriod":
        """
        Cria instância a partir da resposta da API.

        Args:
            data: Dados da API {"Codigo": 1, "Mes": "janeiro/2024"}

        Returns:
            ReferencePeriod: Instância criada
        """
        # Converte "janeiro/2024" para "01/2024"
        month_names = {
            "janeiro": "01", "fevereiro": "02", "março": "03",
            "abril": "04", "maio": "05", "junho": "06",
            "julho": "07", "agosto": "08", "setembro": "09",
            "outubro": "10", "novembro": "11", "dezembro": "12"
        }

        mes_str = data.get("Mes", "")
        parts = mes_str.split("/")

        if len(parts) == 2:
            month_name = parts[0].lower().strip()
            year = parts[1].strip()
            month_num = month_names.get(month_name, "01")
            period = f"{month_num}/{year}"
        else:
            period = mes_str

        return cls(
            period=period,
            code=data.get("Codigo", 0)
        )


@dataclass
class Brand:
    """
    Representa uma marca de veículos.
    """

    name: str
    code: int
    vehicle_type: str  # car, bike, truck
    initial_period: Optional[str] = None  # Primeiro período em que a marca apareceu

    def __hash__(self):
        return hash((self.name, self.vehicle_type))

    def __eq__(self, other):
        if not isinstance(other, Brand):
            return False
        return self.name == other.name and self.vehicle_type == other.vehicle_type

    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário."""
        return asdict(self)

    @classmethod
    def from_api_response(
        cls,
        data: Dict[str, Any],
        vehicle_type: str,
        initial_period: Optional[str] = None
    ) -> "Brand":
        """
        Cria instância a partir da resposta da API.

        Args:
            data: Dados da API {"Label": "FIAT", "Value": "21"}
            vehicle_type: Tipo do veículo (car, bike, truck)
            initial_period: Período inicial da marca (opcional)

        Returns:
            Brand: Instância criada
        """
        return cls(
            name=data.get("Label", ""),
            code=int(data.get("Value", 0)),
            vehicle_type=vehicle_type,
            initial_period=initial_period
        )


@dataclass
class Model:
    """
    Representa um modelo de veículo.
    """

    name: str
    code: int
    fipe_code: str  # Código FIPE (não depende do ano)
    brand: Brand
    vehicle_type: str  # car, bike, truck

    def __hash__(self):
        return hash((self.fipe_code, self.vehicle_type))

    def __eq__(self, other):
        if not isinstance(other, Model):
            return False
        return self.fipe_code == other.fipe_code and self.vehicle_type == other.vehicle_type

    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário, incluindo referência à marca."""
        result = {
            "name": self.name,
            "code": self.code,
            "fipe_code": self.fipe_code,
            "brand": self.brand.to_dict() if isinstance(self.brand, Brand) else self.brand,
            "vehicle_type": self.vehicle_type
        }
        return result

    @classmethod
    def from_api_response(
        cls,
        data: Dict[str, Any],
        brand: Brand,
        vehicle_type: str,
        fipe_code: str = ""
    ) -> "Model":
        """
        Cria instância a partir da resposta da API.

        Args:
            data: Dados da API {"Label": "UNO", "Value": "123"}
            brand: Marca do veículo
            vehicle_type: Tipo do veículo
            fipe_code: Código FIPE (se disponível)

        Returns:
            Model: Instância criada
        """
        return cls(
            name=data.get("Label", ""),
            code=int(data.get("Value", 0)),
            fipe_code=fipe_code,
            brand=brand,
            vehicle_type=vehicle_type
        )


@dataclass
class YearModel:
    """
    Representa um ano-modelo de um veículo.
    """

    description: str  # Ex: "2024 Gasolina"
    year_code: str    # Ex: "2024-1"
    authentication: str  # Código de autenticação único
    model: Model

    def __hash__(self):
        return hash(self.authentication)

    def __eq__(self, other):
        if not isinstance(other, YearModel):
            return False
        return self.authentication == other.authentication

    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário, incluindo referência ao modelo."""
        result = {
            "description": self.description,
            "year_code": self.year_code,
            "authentication": self.authentication,
            "model": self.model.to_dict() if isinstance(self.model, Model) else self.model
        }
        return result

    @classmethod
    def from_api_response(
        cls,
        data: Dict[str, Any],
        model: Model,
        authentication: str = ""
    ) -> "YearModel":
        """
        Cria instância a partir da resposta da API.

        Args:
            data: Dados da API {"Label": "2024 Gasolina", "Value": "2024-1"}
            model: Modelo do veículo
            authentication: Código de autenticação (se disponível)

        Returns:
            YearModel: Instância criada
        """
        return cls(
            description=data.get("Label", ""),
            year_code=data.get("Value", ""),
            authentication=authentication,
            model=model
        )


@dataclass
class FipeValue:
    """
    Representa um valor FIPE consultado.
    """

    year_model: YearModel
    average_price: str  # Preço médio formatado (ex: "R$ 50.000,00")
    query_timestamp: str  # Timestamp da consulta
    reference_period: str  # Mês de referência (MM/yyyy)
    fipe_code: str = ""  # Código FIPE
    fuel: str = ""  # Tipo de combustível

    def __hash__(self):
        return hash((
            self.year_model.authentication if isinstance(self.year_model, YearModel) else self.year_model,
            self.reference_period
        ))

    def __eq__(self, other):
        if not isinstance(other, FipeValue):
            return False
        year_model_eq = (
            self.year_model.authentication == other.year_model.authentication
            if isinstance(self.year_model, YearModel) and isinstance(other.year_model, YearModel)
            else self.year_model == other.year_model
        )
        return year_model_eq and self.reference_period == other.reference_period

    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário, incluindo referência ao ano-modelo."""
        result = {
            "year_model": self.year_model.to_dict() if isinstance(self.year_model, YearModel) else self.year_model,
            "average_price": self.average_price,
            "query_timestamp": self.query_timestamp,
            "reference_period": self.reference_period,
            "fipe_code": self.fipe_code,
            "fuel": self.fuel
        }
        return result

    @classmethod
    def from_api_response(
        cls,
        data: Dict[str, Any],
        year_model: YearModel,
        reference_period: str
    ) -> "FipeValue":
        """
        Cria instância a partir da resposta da API.

        Args:
            data: Dados da API completa
            year_model: Ano-modelo do veículo
            reference_period: Período de referência

        Returns:
            FipeValue: Instância criada
        """
        return cls(
            year_model=year_model,
            average_price=data.get("Valor", ""),
            query_timestamp=datetime.now().isoformat(),
            reference_period=reference_period,
            fipe_code=data.get("CodigoFipe", ""),
            fuel=data.get("Combustivel", "")
        )


@dataclass
class ExtractionResult:
    """
    Resultado de uma extração completa.
    Agrupa todos os dados extraídos.
    """

    reference_periods: List[ReferencePeriod] = field(default_factory=list)
    brands: List[Brand] = field(default_factory=list)
    models: List[Model] = field(default_factory=list)
    year_models: List[YearModel] = field(default_factory=list)
    fipe_values: List[FipeValue] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário."""
        return {
            "reference_periods": [p.to_dict() for p in self.reference_periods],
            "brands": [b.to_dict() for b in self.brands],
            "models": [m.to_dict() for m in self.models],
            "year_models": [y.to_dict() for y in self.year_models],
            "fipe_values": [v.to_dict() for v in self.fipe_values]
        }

    def merge(self, other: "ExtractionResult") -> None:
        """
        Mescla dados de outro resultado, evitando duplicatas.

        Args:
            other: Outro resultado de extração
        """
        # Usa sets para evitar duplicatas
        existing_periods = set(self.reference_periods)
        existing_brands = set(self.brands)
        existing_models = set(self.models)
        existing_years = set(self.year_models)
        existing_values = set(self.fipe_values)

        for period in other.reference_periods:
            if period not in existing_periods:
                self.reference_periods.append(period)
                existing_periods.add(period)

        for brand in other.brands:
            if brand not in existing_brands:
                self.brands.append(brand)
                existing_brands.add(brand)

        for model in other.models:
            if model not in existing_models:
                self.models.append(model)
                existing_models.add(model)

        for year_model in other.year_models:
            if year_model not in existing_years:
                self.year_models.append(year_model)
                existing_years.add(year_model)

        for value in other.fipe_values:
            if value not in existing_values:
                self.fipe_values.append(value)
                existing_values.add(value)
