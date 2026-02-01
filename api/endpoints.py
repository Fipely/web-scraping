# -*- coding: utf-8 -*-
"""
Constantes dos endpoints da API FIPE.
"""


class Endpoints:
    """
    Classe com os endpoints da API FIPE.
    Todos os endpoints utilizam método POST.
    """

    # Endpoint para consultar tabelas de referência (períodos disponíveis)
    REFERENCE_TABLES = "ConsultarTabelaDeReferencia"

    # Endpoint para consultar marcas disponíveis
    BRANDS = "ConsultarMarcas"

    # Endpoint para consultar modelos de uma marca
    MODELS = "ConsultarModelos"

    # Endpoint para consultar anos-modelo de um modelo
    YEAR_MODELS = "ConsultarAnoModelo"

    # Endpoint para consultar valor FIPE completo
    FIPE_VALUE = "ConsultarValorComTodosParametros"


class VehicleType:
    """
    Códigos dos tipos de veículos na API FIPE.
    """

    CAR = 1      # Carros e Utilitários Pequenos
    BIKE = 2     # Motos
    TRUCK = 3    # Caminhões e Micro Ônibus

    @classmethod
    def from_string(cls, vehicle_type: str) -> int:
        """
        Converte string para código do tipo de veículo.

        Args:
            vehicle_type: Tipo do veículo em string (car, bike, truck)

        Returns:
            int: Código do tipo de veículo

        Raises:
            ValueError: Se o tipo de veículo for inválido
        """
        mapping = {
            "car": cls.CAR,
            "carro": cls.CAR,
            "bike": cls.BIKE,
            "moto": cls.BIKE,
            "truck": cls.TRUCK,
            "caminhao": cls.TRUCK,
            "caminhão": cls.TRUCK
        }

        normalized = vehicle_type.lower().strip()

        if normalized not in mapping:
            raise ValueError(
                f"Tipo de veículo inválido: {vehicle_type}. "
                f"Valores válidos: {list(mapping.keys())}"
            )

        return mapping[normalized]

    @classmethod
    def to_string(cls, vehicle_code: int) -> str:
        """
        Converte código para string do tipo de veículo.

        Args:
            vehicle_code: Código do tipo de veículo

        Returns:
            str: Nome do tipo de veículo em inglês
        """
        mapping = {
            cls.CAR: "car",
            cls.BIKE: "bike",
            cls.TRUCK: "truck"
        }

        return mapping.get(vehicle_code, "unknown")

    @classmethod
    def all_types(cls) -> list:
        """
        Retorna lista com todos os tipos de veículos.

        Returns:
            list: Lista de códigos de tipos de veículos
        """
        return [cls.CAR, cls.BIKE, cls.TRUCK]
