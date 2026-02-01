#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de teste para o FIPE Web Scraper.
Executa uma extração limitada para validar o funcionamento.
"""

import json
import sys
from pathlib import Path

# Adiciona o diretório do projeto ao path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from main import FipeScraper
from utils.config import Config


def main():
    """Executa teste de extração."""
    print("=" * 60)
    print("TESTE: FIPE Web Scraper")
    print("=" * 60)

    # Configura extração limitada (apenas fevereiro/2026 e carros)
    # Usa modo sequencial para evitar problemas com multiprocessing
    scraper = FipeScraper(
        start_period="01/2001",
        end_period="01/2001",
        vehicle_types=["bike"],
        use_multiprocessing=False  # Modo sequencial para teste
    )

    # Executa extração
    print("\nIniciando extração...")
    result = scraper.run()

    # Mostra resultados
    print("\n" + "=" * 60)
    print("RESULTADOS")
    print("=" * 60)
    print(f"Períodos: {len(result.reference_periods)}")
    print(f"Marcas: {len(result.brands)}")
    print(f"Modelos: {len(result.models)}")
    print(f"Anos-modelo: {len(result.year_models)}")
    print(f"Valores FIPE: {len(result.fipe_values)}")

    # Verifica arquivo de saída
    output_path = Config.get_final_output_path()
    if output_path.exists():
        print(f"\nArquivo JSON gerado: {output_path}")
        print(f"Tamanho: {output_path.stat().st_size / 1024:.2f} KB")

        # Mostra estrutura do JSON
        with open(output_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            print(f"\nEstrutura do JSON:")
            for key, value in data.items():
                print(f"  - {key}: {len(value)} itens")
    else:
        print(f"\nARQUIVO NÃO ENCONTRADO: {output_path}")

    print("\n" + "=" * 60)
    print("TESTE CONCLUÍDO COM SUCESSO!")
    print("=" * 60)

    return 0


if __name__ == "__main__":
    sys.exit(main())
