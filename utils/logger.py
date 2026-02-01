# -*- coding: utf-8 -*-
"""
Módulo de logging do projeto.
Configura o sistema de logs padronizados para monitoramento.
"""

import logging
import sys
from pathlib import Path
from typing import Optional

from utils.config import Config


def setup_logger(
    name: str = "fipe_scraper",
    log_level: Optional[str] = None,
    log_file: Optional[Path] = None
) -> logging.Logger:
    """
    Configura e retorna um logger padronizado.

    Args:
        name: Nome do logger
        log_level: Nível de log (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Caminho para o arquivo de log

    Returns:
        logging.Logger: Logger configurado
    """
    # Usa valores padrão do Config se não especificados
    if log_level is None:
        log_level = Config.LOG_LEVEL
    if log_file is None:
        log_file = Config.get_log_path()

    # Cria o diretório de logs se não existir
    log_file.parent.mkdir(parents=True, exist_ok=True)

    # Configura o logger
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, log_level.upper()))

    # Evita adicionar handlers duplicados
    if logger.handlers:
        return logger

    # Formato do log
    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # Handler para arquivo
    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setFormatter(formatter)
    file_handler.setLevel(getattr(logging, log_level.upper()))
    logger.addHandler(file_handler)

    # Handler para console
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    console_handler.setLevel(getattr(logging, log_level.upper()))
    logger.addHandler(console_handler)

    return logger


# Logger padrão do projeto
logger = setup_logger()
