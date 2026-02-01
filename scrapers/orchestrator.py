# -*- coding: utf-8 -*-
"""
Orquestrador de scraping com suporte a multiprocessing.
Coordena a extração de dados e gerencia arquivos parciais.
"""

import json
import os
import uuid
from concurrent.futures import ProcessPoolExecutor, as_completed
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

from api.fipe_client import FipeClient
from api.endpoints import VehicleType
from models.fipe_models import (
    Brand,
    ExtractionResult,
    FipeValue,
    Model,
    ReferencePeriod,
    YearModel
)
from scrapers.references import ReferenceScraper
from scrapers.brands import BrandScraper
from scrapers.models import ModelScraper
from scrapers.values import ValueScraper
from utils.config import Config
from utils.logger import setup_logger
from utils.file_handler import FileHandler


logger = setup_logger("orchestrator")


@dataclass
class ExtractionTask:
    """
    Representa uma tarefa de extração a ser executada em paralelo.
    """
    task_id: str
    period: Dict[str, Any]  # Serializado para multiprocessing
    brand: Dict[str, Any]   # Serializado para multiprocessing
    vehicle_type: int


def _extract_worker(task: ExtractionTask) -> Dict[str, Any]:
    """
    Worker function para extração em paralelo.
    Cada worker processa uma marca em um período.

    Args:
        task: Tarefa de extração

    Returns:
        Dict[str, Any]: Resultado da extração serializado
    """
    # Recria objetos a partir dos dicionários serializados
    period = ReferencePeriod(
        period=task.period["period"],
        code=task.period["code"]
    )

    brand = Brand(
        name=task.brand["name"],
        code=task.brand["code"],
        vehicle_type=task.brand["vehicle_type"],
        initial_period=task.brand.get("initial_period")
    )

    # Cria cliente e scrapers para este worker
    client = FipeClient()
    model_scraper = ModelScraper(client)
    value_scraper = ValueScraper(client)

    result = ExtractionResult()

    try:
        # Extrai modelos da marca
        models = model_scraper.extract_for_brand(period, brand)

        # Para cada modelo, extrai anos-modelo e valores
        for model in models:
            year_models = value_scraper.extract_year_models(period, model)

            for year_model in year_models:
                fipe_value = value_scraper.extract_fipe_value(period, year_model)

                if fipe_value:
                    # Adiciona ao resultado
                    result.year_models.append(year_model)
                    result.fipe_values.append(fipe_value)

                    # Atualiza código FIPE do modelo se necessário
                    if fipe_value.fipe_code and not model.fipe_code:
                        model.fipe_code = fipe_value.fipe_code

            # Adiciona modelo ao resultado
            if model.fipe_code:
                result.models.append(model)

        # Adiciona marca ao resultado
        result.brands.append(brand)

    except Exception as e:
        logger.error(f"Erro no worker {task.task_id}: {e}")
    finally:
        client.close()

    return result.to_dict()


class Orchestrator:
    """
    Orquestrador de extração de dados da FIPE.
    Coordena scrapers e gerencia processamento paralelo ou sequencial.
    """

    def __init__(
        self,
        start_period: Optional[str] = None,
        end_period: Optional[str] = None,
        vehicle_types: Optional[List[str]] = None,
        use_multiprocessing: bool = True
    ):
        """
        Inicializa o orquestrador.

        Args:
            start_period: Período inicial no formato MM/yyyy (opcional)
            end_period: Período final no formato MM/yyyy (opcional)
            vehicle_types: Lista de tipos de veículos (car, bike, truck) (opcional)
            use_multiprocessing: Se True, usa multiprocessing; se False, executa sequencialmente
        """
        self.start_period = start_period
        self.end_period = end_period
        self.use_multiprocessing = use_multiprocessing

        # Converte tipos de veículos para códigos
        if vehicle_types:
            self.vehicle_type_codes = [
                VehicleType.from_string(vt) for vt in vehicle_types
            ]
        else:
            self.vehicle_type_codes = VehicleType.all_types()

        self.max_workers = Config.MAX_WORKERS

        logger.info(
            f"Orquestrador inicializado: período={start_period}-{end_period}, "
            f"tipos={vehicle_types or 'todos'}, workers={self.max_workers}, "
            f"multiprocessing={use_multiprocessing}"
        )

    def run(self) -> ExtractionResult:
        """
        Executa a extração completa de dados.

        Returns:
            ExtractionResult: Resultado consolidado da extração
        """
        logger.info("Iniciando extração de dados da FIPE...")

        # 1. Extrai períodos de referência
        with FipeClient() as client:
            reference_scraper = ReferenceScraper(client)
            all_periods = reference_scraper.extract()

            # Filtra por intervalo se especificado
            periods = reference_scraper.filter_by_range(
                all_periods,
                self.start_period,
                self.end_period
            )

        if not periods:
            logger.warning("Nenhum período encontrado para extração")
            return ExtractionResult()

        logger.info(f"Serão processados {len(periods)} períodos de referência")

        # 2. Para cada período, extrai marcas e cria tarefas
        tasks = []

        # Usamos apenas o período mais recente para obter as marcas
        # (para identificar o período inicial, processamos todos depois)
        latest_period = max(periods, key=lambda p: p.period)

        with FipeClient() as client:
            brand_scraper = BrandScraper(client)

            for vehicle_type_code in self.vehicle_type_codes:
                brands = brand_scraper.extract_for_single_period(
                    latest_period,
                    vehicle_type_code
                )

                logger.info(
                    f"Encontradas {len(brands)} marcas para tipo "
                    f"{VehicleType.to_string(vehicle_type_code)}"
                )

                # Cria tarefas para cada combinação marca + período
                for brand in brands:
                    for period in periods:
                        task = ExtractionTask(
                            task_id=str(uuid.uuid4())[:8],
                            period=period.to_dict(),
                            brand=brand.to_dict(),
                            vehicle_type=vehicle_type_code
                        )
                        tasks.append(task)

        logger.info(f"Criadas {len(tasks)} tarefas de extração")

        # 3. Executa extração em paralelo ou sequencialmente
        final_result = ExtractionResult()
        final_result.reference_periods = periods

        if self.use_multiprocessing:
            # Processa em lotes para evitar sobrecarga de memória
            batch_size = self.max_workers * 2

            for batch_idx in range(0, len(tasks), batch_size):
                batch = tasks[batch_idx:batch_idx + batch_size]
                batch_results = self._process_batch(batch, batch_idx, len(tasks))

                # Mescla resultados do lote
                for result_dict in batch_results:
                    batch_result = self._dict_to_result(result_dict)
                    final_result.merge(batch_result)

                # Salva arquivo parcial do lote
                partial_filename = f"batch_{batch_idx // batch_size}.json"
                FileHandler.save_partial(
                    {"batch": batch_idx, "data": final_result.to_dict()},
                    partial_filename
                )
        else:
            # Modo sequencial: processa uma tarefa por vez
            for idx, task in enumerate(tasks):
                logger.info(f"Processando tarefa {idx + 1}/{len(tasks)}")
                result_dict = _extract_worker(task)
                result = self._dict_to_result(result_dict)
                final_result.merge(result)

        logger.info(
            f"Extração concluída: {len(final_result.brands)} marcas, "
            f"{len(final_result.models)} modelos, "
            f"{len(final_result.year_models)} anos-modelo, "
            f"{len(final_result.fipe_values)} valores FIPE"
        )

        return final_result

    def _process_batch(
        self,
        tasks: List[ExtractionTask],
        batch_start: int,
        total_tasks: int
    ) -> List[Dict[str, Any]]:
        """
        Processa um lote de tarefas em paralelo.

        Args:
            tasks: Lista de tarefas do lote
            batch_start: Índice inicial do lote
            total_tasks: Total de tarefas

        Returns:
            List[Dict[str, Any]]: Resultados do lote
        """
        results = []

        logger.info(
            f"Processando lote {batch_start // len(tasks) + 1}: "
            f"tarefas {batch_start + 1}-{batch_start + len(tasks)} de {total_tasks}"
        )

        with ProcessPoolExecutor(max_workers=self.max_workers) as executor:
            # Submete todas as tarefas
            future_to_task = {
                executor.submit(_extract_worker, task): task
                for task in tasks
            }

            # Coleta resultados conforme completam
            for future in as_completed(future_to_task):
                task = future_to_task[future]

                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    logger.error(
                        f"Erro na tarefa {task.task_id}: {e}"
                    )

        return results

    def _dict_to_result(self, data: Dict[str, Any]) -> ExtractionResult:
        """
        Converte dicionário para ExtractionResult.

        Args:
            data: Dicionário com dados

        Returns:
            ExtractionResult: Objeto de resultado
        """
        result = ExtractionResult()

        # Converte períodos
        for p_dict in data.get("reference_periods", []):
            period = ReferencePeriod(
                period=p_dict.get("period", ""),
                code=p_dict.get("code", 0)
            )
            result.reference_periods.append(period)

        # Converte marcas
        brand_cache = {}
        for b_dict in data.get("brands", []):
            brand = Brand(
                name=b_dict.get("name", ""),
                code=b_dict.get("code", 0),
                vehicle_type=b_dict.get("vehicle_type", ""),
                initial_period=b_dict.get("initial_period")
            )
            result.brands.append(brand)
            brand_cache[(brand.name, brand.vehicle_type)] = brand

        # Converte modelos
        model_cache = {}
        for m_dict in data.get("models", []):
            # Recupera marca
            brand_dict = m_dict.get("brand", {})
            brand_key = (brand_dict.get("name", ""), brand_dict.get("vehicle_type", ""))
            brand = brand_cache.get(brand_key)

            if not brand:
                brand = Brand(
                    name=brand_dict.get("name", ""),
                    code=brand_dict.get("code", 0),
                    vehicle_type=brand_dict.get("vehicle_type", ""),
                    initial_period=brand_dict.get("initial_period")
                )

            model = Model(
                name=m_dict.get("name", ""),
                code=m_dict.get("code", 0),
                fipe_code=m_dict.get("fipe_code", ""),
                brand=brand,
                vehicle_type=m_dict.get("vehicle_type", "")
            )
            result.models.append(model)
            model_cache[(model.fipe_code, model.vehicle_type)] = model

        # Converte anos-modelo
        year_model_cache = {}
        for y_dict in data.get("year_models", []):
            # Recupera modelo
            model_dict = y_dict.get("model", {})
            model_key = (model_dict.get("fipe_code", ""), model_dict.get("vehicle_type", ""))
            model = model_cache.get(model_key)

            if not model:
                # Cria modelo se não existe no cache
                brand_dict = model_dict.get("brand", {})
                brand = Brand(
                    name=brand_dict.get("name", ""),
                    code=brand_dict.get("code", 0),
                    vehicle_type=brand_dict.get("vehicle_type", ""),
                    initial_period=brand_dict.get("initial_period")
                )
                model = Model(
                    name=model_dict.get("name", ""),
                    code=model_dict.get("code", 0),
                    fipe_code=model_dict.get("fipe_code", ""),
                    brand=brand,
                    vehicle_type=model_dict.get("vehicle_type", "")
                )

            year_model = YearModel(
                description=y_dict.get("description", ""),
                year_code=y_dict.get("year_code", ""),
                authentication=y_dict.get("authentication", ""),
                model=model
            )
            result.year_models.append(year_model)
            year_model_cache[year_model.authentication] = year_model

        # Converte valores FIPE
        for v_dict in data.get("fipe_values", []):
            # Recupera ano-modelo
            year_dict = v_dict.get("year_model", {})
            auth = year_dict.get("authentication", "")
            year_model = year_model_cache.get(auth)

            if not year_model:
                # Cria ano-modelo se não existe no cache
                model_dict = year_dict.get("model", {})
                brand_dict = model_dict.get("brand", {})
                brand = Brand(
                    name=brand_dict.get("name", ""),
                    code=brand_dict.get("code", 0),
                    vehicle_type=brand_dict.get("vehicle_type", ""),
                    initial_period=brand_dict.get("initial_period")
                )
                model = Model(
                    name=model_dict.get("name", ""),
                    code=model_dict.get("code", 0),
                    fipe_code=model_dict.get("fipe_code", ""),
                    brand=brand,
                    vehicle_type=model_dict.get("vehicle_type", "")
                )
                year_model = YearModel(
                    description=year_dict.get("description", ""),
                    year_code=year_dict.get("year_code", ""),
                    authentication=auth,
                    model=model
                )

            fipe_value = FipeValue(
                year_model=year_model,
                average_price=v_dict.get("average_price", ""),
                query_timestamp=v_dict.get("query_timestamp", ""),
                reference_period=v_dict.get("reference_period", ""),
                fipe_code=v_dict.get("fipe_code", ""),
                fuel=v_dict.get("fuel", "")
            )
            result.fipe_values.append(fipe_value)

        return result

    def finalize(self) -> None:
        """
        Consolida todos os arquivos parciais no arquivo final.
        """
        logger.info("Finalizando e consolidando arquivos parciais...")
        FileHandler.consolidate_partials()
        logger.info("Consolidação concluída")
