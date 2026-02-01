# -*- coding: utf-8 -*-
"""
Módulo utilitário para manipulação de arquivos JSON.
Responsável por salvar dados parciais e consolidar arquivos.
"""

import json
import os
from pathlib import Path
from typing import Any, Dict, List

from utils.config import Config
from utils.logger import setup_logger


logger = setup_logger("file_handler")


class FileHandler:
    """
    Classe responsável pela manipulação de arquivos JSON.
    Salva dados parciais e consolida múltiplos arquivos.
    """

    @staticmethod
    def ensure_directory(path: Path) -> None:
        """
        Garante que o diretório existe, criando se necessário.

        Args:
            path: Caminho do diretório
        """
        path.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def save_partial(data: Dict[str, Any], filename: str) -> Path:
        """
        Salva dados em um arquivo JSON parcial.

        Args:
            data: Dados a serem salvos
            filename: Nome do arquivo (sem caminho)

        Returns:
            Path: Caminho do arquivo salvo
        """
        output_path = Config.get_partial_output_path(filename)
        FileHandler.ensure_directory(output_path.parent)

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        logger.info(f"Arquivo parcial salvo: {output_path}")
        return output_path

    @staticmethod
    def load_partial(filename: str) -> Dict[str, Any]:
        """
        Carrega dados de um arquivo JSON parcial.

        Args:
            filename: Nome do arquivo (sem caminho)

        Returns:
            Dict[str, Any]: Dados carregados
        """
        input_path = Config.get_partial_output_path(filename)

        if not input_path.exists():
            logger.warning(f"Arquivo parcial não encontrado: {input_path}")
            return {}

        with open(input_path, "r", encoding="utf-8") as f:
            return json.load(f)

    @staticmethod
    def list_partial_files() -> List[Path]:
        """
        Lista todos os arquivos parciais no diretório de saída.

        Returns:
            List[Path]: Lista de caminhos dos arquivos parciais
        """
        partial_dir = Path(Config.PARTIAL_OUTPUT_DIR)

        if not partial_dir.exists():
            return []

        return list(partial_dir.glob("*.json"))

    @staticmethod
    def consolidate_partials() -> Path:
        """
        Consolida todos os arquivos parciais em um único arquivo final.

        Returns:
            Path: Caminho do arquivo consolidado
        """
        partial_files = FileHandler.list_partial_files()

        if not partial_files:
            logger.warning("Nenhum arquivo parcial encontrado para consolidação")
            return Config.get_final_output_path()

        # Estrutura consolidada
        consolidated = {
            "reference_periods": [],
            "brands": [],
            "models": [],
            "year_models": [],
            "fipe_values": []
        }

        # Conjuntos para evitar duplicatas
        seen_periods = set()
        seen_brands = set()
        seen_models = set()
        seen_year_models = set()
        seen_fipe_values = set()

        for partial_file in partial_files:
            logger.info(f"Processando arquivo parcial: {partial_file}")

            try:
                with open(partial_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
            except json.JSONDecodeError as e:
                logger.error(f"Erro ao ler arquivo {partial_file}: {e}")
                continue

            # Consolida períodos de referência
            for period in data.get("reference_periods", []):
                period_key = period.get("period")
                if period_key and period_key not in seen_periods:
                    seen_periods.add(period_key)
                    consolidated["reference_periods"].append(period)

            # Consolida marcas
            for brand in data.get("brands", []):
                brand_key = (brand.get("name"), brand.get("vehicle_type"))
                if brand_key[0] and brand_key not in seen_brands:
                    seen_brands.add(brand_key)
                    consolidated["brands"].append(brand)

            # Consolida modelos
            for model in data.get("models", []):
                model_key = (model.get("fipe_code"), model.get("vehicle_type"))
                if model_key[0] and model_key not in seen_models:
                    seen_models.add(model_key)
                    consolidated["models"].append(model)

            # Consolida anos-modelo
            for year_model in data.get("year_models", []):
                year_key = (
                    year_model.get("authentication"),
                    year_model.get("model", {}).get("fipe_code") if isinstance(year_model.get("model"), dict) else year_model.get("model")
                )
                if year_key[0] and year_key not in seen_year_models:
                    seen_year_models.add(year_key)
                    consolidated["year_models"].append(year_model)

            # Consolida valores FIPE
            for fipe_value in data.get("fipe_values", []):
                value_key = (
                    fipe_value.get("year_model", {}).get("authentication") if isinstance(fipe_value.get("year_model"), dict) else fipe_value.get("year_model"),
                    fipe_value.get("reference_period")
                )
                if value_key[0] and value_key not in seen_fipe_values:
                    seen_fipe_values.add(value_key)
                    consolidated["fipe_values"].append(fipe_value)

        # Ordena os dados
        consolidated["reference_periods"].sort(
            key=lambda x: x.get("period", ""),
            reverse=True
        )
        consolidated["brands"].sort(
            key=lambda x: (x.get("vehicle_type", ""), x.get("name", ""))
        )
        consolidated["models"].sort(
            key=lambda x: (x.get("vehicle_type", ""), x.get("brand", {}).get("name", "") if isinstance(x.get("brand"), dict) else "", x.get("name", ""))
        )

        # Salva arquivo final
        output_path = Config.get_final_output_path()
        FileHandler.ensure_directory(output_path.parent)

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(consolidated, f, ensure_ascii=False, indent=2)

        logger.info(f"Arquivo consolidado salvo: {output_path}")
        logger.info(f"Total de períodos: {len(consolidated['reference_periods'])}")
        logger.info(f"Total de marcas: {len(consolidated['brands'])}")
        logger.info(f"Total de modelos: {len(consolidated['models'])}")
        logger.info(f"Total de anos-modelo: {len(consolidated['year_models'])}")
        logger.info(f"Total de valores FIPE: {len(consolidated['fipe_values'])}")

        return output_path

    @staticmethod
    def cleanup_partials() -> None:
        """
        Remove todos os arquivos parciais após consolidação.
        """
        partial_files = FileHandler.list_partial_files()

        for partial_file in partial_files:
            try:
                os.remove(partial_file)
                logger.debug(f"Arquivo parcial removido: {partial_file}")
            except OSError as e:
                logger.warning(f"Erro ao remover arquivo {partial_file}: {e}")

        logger.info(f"Removidos {len(partial_files)} arquivos parciais")
