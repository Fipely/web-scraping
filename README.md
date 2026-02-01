# FIPE Web Scraper

Projeto Python para extração de dados da Tabela FIPE (Fundação Instituto de Pesquisas Econômicas) através de engenharia reversa da API.

## 📋 Descrição

Este scraper extrai dados da tabela FIPE (https://veiculos.fipe.org.br/) de forma automatizada, incluindo:

- **Períodos de referência**: Todos os meses/anos disponíveis na base
- **Marcas**: Todas as marcas de veículos com seu período inicial
- **Modelos**: Modelos de cada marca com código FIPE
- **Anos-modelo**: Variantes de ano e combustível de cada modelo
- **Valores FIPE**: Preço médio de cada veículo

### Tipos de Veículos Suportados

- 🚗 **Carros e Utilitários Pequenos** (`car`)
- 🏍️ **Motos** (`bike`)
- 🚚 **Caminhões e Micro Ônibus** (`truck`)

## 🚀 Instalação

### Requisitos

- Python 3.8+
- pip

### Passos

1. Clone o repositório:
```bash
git clone <url-do-repositorio>
cd web-scraping
```

2. Crie um ambiente virtual (recomendado):
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate  # Windows
```

3. Instale as dependências:
```bash
pip install -r requirements.txt
```

4. Configure o arquivo `.env` (opcional):
```bash
cp .env.example .env
# Edite conforme necessário
```

## 💻 Uso

### Uso Básico

```python
from main import FipeScraper

# Extrai todos os dados disponíveis
scraper = FipeScraper()
result = scraper.run()

print(f"Marcas extraídas: {len(result.brands)}")
print(f"Modelos extraídos: {len(result.models)}")
print(f"Valores FIPE: {len(result.fipe_values)}")
```

### Extração por Período

```python
from main import FipeScraper

# Extrai apenas o primeiro semestre de 2024
scraper = FipeScraper(
    start_period="01/2024",
    end_period="06/2024"
)
result = scraper.run()
```

### Extração por Tipo de Veículo

```python
from main import FipeScraper

# Extrai apenas carros
scraper = FipeScraper(vehicle_types=["car"])
result = scraper.run()

# Extrai carros e motos
scraper = FipeScraper(vehicle_types=["car", "bike"])
result = scraper.run()
```

### Combinando Filtros

```python
from main import FipeScraper

# Extrai motos do ano de 2024
scraper = FipeScraper(
    start_period="01/2024",
    end_period="12/2024",
    vehicle_types=["bike"]
)
result = scraper.run()
```

### Consolidação de Arquivos Parciais

Se a extração for interrompida, você pode consolidar os dados já extraídos:

```python
from main import FipeScraper

FipeScraper.finalize()
```

## 📁 Estrutura do Projeto

```
web-scraping/
├── main.py                 # Ponto de entrada principal
├── .env                    # Configurações de ambiente
├── requirements.txt        # Dependências do projeto
├── README.md              # Documentação
│
├── api/                    # Módulo de comunicação com API
│   ├── __init__.py
│   ├── endpoints.py       # Constantes dos endpoints
│   └── fipe_client.py     # Cliente HTTP com retry
│
├── models/                 # Modelos de dados
│   ├── __init__.py
│   └── fipe_models.py     # Dataclasses das entidades
│
├── scrapers/               # Scrapers especializados
│   ├── __init__.py
│   ├── base_scraper.py    # Classe base abstrata
│   ├── references.py      # Scraper de períodos
│   ├── brands.py          # Scraper de marcas
│   ├── models.py          # Scraper de modelos
│   ├── values.py          # Scraper de valores
│   └── orchestrator.py    # Coordenador multiprocessing
│
├── utils/                  # Utilitários
│   ├── __init__.py
│   ├── config.py          # Configurações do .env
│   ├── logger.py          # Sistema de logging
│   └── file_handler.py    # Manipulação de arquivos
│
└── output/                 # Diretório de saída
    ├── partial/           # Arquivos JSON parciais
    └── fipe_complete.json # Arquivo final consolidado
```

## 📊 Estrutura dos Dados

### ReferencePeriod (Período de Referência)
```json
{
  "period": "01/2024",
  "code": 308
}
```

### Brand (Marca)
```json
{
  "name": "FIAT",
  "code": 21,
  "vehicle_type": "car",
  "initial_period": "01/2002"
}
```

### Model (Modelo)
```json
{
  "name": "UNO MILLE 1.0 Fire/ F.Flex/ ECONOMY 4p",
  "code": 4886,
  "fipe_code": "001267-4",
  "brand": { "name": "FIAT", "..." },
  "vehicle_type": "car"
}
```

### YearModel (Ano-Modelo)
```json
{
  "description": "2024 Gasolina",
  "year_code": "2024-1",
  "authentication": "abc123xyz",
  "model": { "name": "UNO MILLE", "..." }
}
```

### FipeValue (Valor FIPE)
```json
{
  "year_model": { "..." },
  "average_price": "R$ 35.000,00",
  "query_timestamp": "2024-01-15T10:30:00",
  "reference_period": "01/2024",
  "fipe_code": "001267-4",
  "fuel": "Gasolina"
}
```

## ⚙️ Configurações

O arquivo `.env` permite customizar:

| Variável | Descrição | Padrão |
|----------|-----------|--------|
| `FIPE_BASE_URL` | URL base da API | `https://veiculos.fipe.org.br/api/veiculos/` |
| `MAX_RETRIES` | Tentativas em caso de erro | `5` |
| `INITIAL_BACKOFF` | Delay inicial (segundos) | `1.0` |
| `MAX_BACKOFF` | Delay máximo (segundos) | `60.0` |
| `DELAY_BETWEEN_REQUESTS` | Delay entre requisições | `0.5` |
| `MAX_WORKERS` | Workers paralelos | `4` |
| `OUTPUT_DIR` | Diretório de saída | `output` |
| `LOG_LEVEL` | Nível de log | `INFO` |

## 🔧 Tratamento de Erros

O scraper implementa:

- **Retry com Exponential Backoff**: Retenta requisições com delay crescente
- **Rate Limiting**: Aguarda entre requisições para evitar bloqueios
- **Timeout**: 30 segundos por requisição
- **Arquivos Parciais**: Salva progresso para recuperação

## 📝 Logs

Os logs são salvos em `output/fipe_scraper.log` e exibidos no console:

```
2024-01-15 10:30:00 | INFO     | main | FipeScraper inicializado
2024-01-15 10:30:01 | INFO     | references | Extraídos 308 períodos
2024-01-15 10:30:05 | WARNING  | fipe_client | Rate limit atingido, aguardando...
2024-01-15 10:31:00 | INFO     | orchestrator | Extração concluída
```

## 🤝 Contribuição

1. Fork o projeto
2. Crie uma branch: `git checkout -b feature/nova-funcionalidade`
3. Commit suas mudanças: `git commit -m 'Adiciona nova funcionalidade'`
4. Push para a branch: `git push origin feature/nova-funcionalidade`
5. Abra um Pull Request

## 📄 Licença

Este projeto é para fins educacionais. Respeite os termos de uso do site da FIPE.

## ⚠️ Aviso

Este scraper faz múltiplas requisições à API da FIPE. Use com responsabilidade para evitar sobrecarga no servidor. Recomenda-se ajustar o `DELAY_BETWEEN_REQUESTS` e `MAX_WORKERS` conforme necessário.
