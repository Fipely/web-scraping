# Guia de Uso - FIPE Web Scraper

Este documento explica como instalar, configurar e utilizar o FIPE Web Scraper para extrair dados da tabela FIPE.

---

## 📦 Instalação

### 1. Pré-requisitos

- **Python 3.8+** instalado no sistema
- **Git** (opcional, para clonar o repositório)

### 2. Clonar o Repositório (se necessário)

```bash
git clone <url-do-repositorio>
cd web-scraping
```

### 3. Criar Ambiente Virtual

O ambiente virtual isola as dependências do projeto, evitando conflitos com outros projetos Python.

```bash
# Criar o ambiente virtual na pasta .venv
python3 -m venv venv

# Ou, se preferir usar .venv como nome:
python3 -m venv .venv
```

### 4. Ativar o Ambiente Virtual

**Linux / macOS:**
```bash
source venv/bin/activate
```

**Windows (PowerShell):**
```powershell
.\venv\Scripts\Activate.ps1
```

**Windows (CMD):**
```cmd
.\venv\Scripts\activate.bat
```

> 💡 **Dica:** Quando o ambiente virtual está ativo, você verá `(venv)` no início do prompt do terminal.

### 5. Instalar Dependências

Com o ambiente virtual ativo, instale as dependências:

```bash
pip install -r requirements.txt
```

As dependências instaladas são:
- `requests` - Cliente HTTP para chamadas à API
- `python-dotenv` - Carrega variáveis do arquivo `.env`
- `tenacity` - Implementa retry com exponential backoff
- `pydantic` - Validação de dados (opcional, mas instalado)

### 6. Configurar Variáveis de Ambiente

Copie o arquivo de exemplo e ajuste conforme necessário:

```bash
cp .env.example .env
```

Edite o `.env` se precisar ajustar configurações (veja seção de Configuração abaixo).

---

## 🚀 Como Usar

### Uso Básico via Python

```python
from main import FipeScraper

# Extrai TODOS os dados disponíveis (pode demorar muito!)
scraper = FipeScraper()
result = scraper.run()
```

### Extração por Período

Especifique um intervalo de datas no formato `MM/yyyy`:

```python
from main import FipeScraper

# Extrai apenas dados de janeiro a junho de 2025
scraper = FipeScraper(
    start_period="01/2025",
    end_period="06/2025"
)
result = scraper.run()
```

### Extração por Tipo de Veículo

Filtre por tipo de veículo:
- `"car"` - Carros e Utilitários Pequenos
- `"bike"` - Motos
- `"truck"` - Caminhões e Micro Ônibus

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

# Extrai motos de janeiro de 2025
scraper = FipeScraper(
    start_period="01/2025",
    end_period="01/2025",
    vehicle_types=["bike"]
)
result = scraper.run()
```

### Modo Sequencial (Mais Estável)

Se encontrar problemas com multiprocessing, use o modo sequencial:

```python
from main import FipeScraper

scraper = FipeScraper(
    start_period="01/2025",
    end_period="01/2025",
    vehicle_types=["car"],
    use_multiprocessing=False  # Executa de forma sequencial
)
result = scraper.run()
```

### Executar via Linha de Comando

```bash
# Certifique-se que o ambiente virtual está ativo
source venv/bin/activate

# Execute o script principal
python main.py

# Ou execute o script de teste
python test_scraper.py
```

---

## 📁 Onde os Dados são Salvos

### Estrutura de Arquivos de Saída

```
output/
├── fipe_complete.json     # Arquivo final com todos os dados consolidados
├── fipe_scraper.log       # Logs de execução
└── partial/               # Arquivos parciais (durante extração)
    ├── batch_0.json
    ├── batch_1.json
    └── ...
```

### Arquivo Principal: `fipe_complete.json`

Este é o arquivo final que contém todos os dados extraídos. Estrutura:

```json
{
  "reference_periods": [
    {"period": "01/2025", "code": 308}
  ],
  "brands": [
    {"name": "FIAT", "code": 21, "vehicle_type": "car", "initial_period": "01/2002"}
  ],
  "models": [
    {
      "name": "UNO MILLE 1.0",
      "code": 4886,
      "fipe_code": "001267-4",
      "brand": {"name": "FIAT", "..."},
      "vehicle_type": "car"
    }
  ],
  "year_models": [
    {
      "description": "2024 Gasolina",
      "year_code": "2024-1",
      "authentication": "abc123xyz",
      "model": {"..."}
    }
  ],
  "fipe_values": [
    {
      "year_model": {"..."},
      "average_price": "R$ 35.000,00",
      "query_timestamp": "2025-01-15T10:30:00",
      "reference_period": "01/2025",
      "fipe_code": "001267-4",
      "fuel": "Gasolina"
    }
  ]
}
```

### Arquivos Parciais

Durante a extração, dados são salvos em `output/partial/` para evitar perda de progresso. Caso a extração seja interrompida, você pode consolidar os parciais:

```python
from main import FipeScraper

# Consolida arquivos parciais no arquivo final
FipeScraper.finalize()
```

### Arquivo de Log: `fipe_scraper.log`

Contém registros detalhados da execução:

```
2025-01-15 10:30:00 | INFO     | main | FipeScraper inicializado
2025-01-15 10:30:01 | INFO     | ReferenceScraper | Extraídos 302 períodos
2025-01-15 10:30:05 | WARNING  | fipe_client | Rate limit atingido, aguardando...
2025-01-15 10:31:00 | INFO     | orchestrator | Extração concluída
```

---

## ⚙️ Configuração

### Arquivo `.env`

| Variável | Descrição | Valor Padrão |
|----------|-----------|--------------|
| `FIPE_BASE_URL` | URL base da API FIPE | `https://veiculos.fipe.org.br/api/veiculos/` |
| `MAX_RETRIES` | Número máximo de tentativas em caso de erro | `5` |
| `INITIAL_BACKOFF` | Delay inicial entre retries (segundos) | `2.0` |
| `MAX_BACKOFF` | Delay máximo entre retries (segundos) | `120.0` |
| `BACKOFF_MULTIPLIER` | Multiplicador do delay (exponencial) | `2.0` |
| `REQUEST_TIMEOUT` | Timeout por requisição (segundos) | `30` |
| `DELAY_BETWEEN_REQUESTS` | Delay entre requisições (segundos) | `1.5` |
| `MAX_WORKERS` | Número de workers paralelos | `4` |
| `OUTPUT_DIR` | Diretório de saída | `output` |
| `PARTIAL_OUTPUT_DIR` | Diretório de arquivos parciais | `output/partial` |
| `FINAL_OUTPUT_FILE` | Caminho do arquivo final | `output/fipe_complete.json` |
| `LOG_LEVEL` | Nível de log (DEBUG, INFO, WARNING, ERROR) | `INFO` |
| `LOG_FILE` | Caminho do arquivo de log | `output/fipe_scraper.log` |

### Ajustando para Evitar Bloqueios

Se estiver recebendo muitos erros de rate limit, aumente os delays:

```env
DELAY_BETWEEN_REQUESTS=3.0
INITIAL_BACKOFF=5.0
MAX_WORKERS=2
```

---

## 📊 Dados Extraídos

### ReferencePeriod (Período de Referência)
- `period`: Mês/ano no formato MM/yyyy
- `code`: Código interno da FIPE

### Brand (Marca)
- `name`: Nome da marca (ex: "FIAT", "Honda")
- `code`: Código da marca na API
- `vehicle_type`: Tipo de veículo (car, bike, truck)
- `initial_period`: Primeiro período em que a marca aparece

### Model (Modelo)
- `name`: Nome do modelo
- `code`: Código do modelo na API
- `fipe_code`: Código FIPE do modelo
- `brand`: Referência à marca
- `vehicle_type`: Tipo de veículo

### YearModel (Ano-Modelo)
- `description`: Descrição (ex: "2024 Gasolina")
- `year_code`: Código do ano (ex: "2024-1")
- `authentication`: Código de autenticação único
- `model`: Referência ao modelo

### FipeValue (Valor FIPE)
- `year_model`: Referência ao ano-modelo
- `average_price`: Preço médio formatado (ex: "R$ 35.000,00")
- `query_timestamp`: Data/hora da consulta
- `reference_period`: Período de referência
- `fipe_code`: Código FIPE
- `fuel`: Tipo de combustível

---

## ❓ Solução de Problemas

### Erro: "Rate limit atingido"

O servidor da FIPE bloqueia requisições muito frequentes. Soluções:
1. Aumente `DELAY_BETWEEN_REQUESTS` no `.env`
2. Reduza `MAX_WORKERS` para 1 ou 2
3. Aguarde alguns minutos e tente novamente

### Erro de Multiprocessing

Se encontrar erros relacionados a multiprocessing:
```python
scraper = FipeScraper(use_multiprocessing=False)
```

### Ambiente Virtual não Ativa

Verifique se você está usando o comando correto para seu sistema operacional (veja seção de instalação).

### Dependências não Instaladas

```bash
# Certifique-se que o ambiente virtual está ativo
source venv/bin/activate

# Reinstale as dependências
pip install -r requirements.txt
```

---

## 📝 Exemplos Completos

### Exemplo 1: Extração Simples de Carros

```python
#!/usr/bin/env python3
from main import FipeScraper

# Extrai carros do mês atual
scraper = FipeScraper(
    start_period="02/2026",
    end_period="02/2026",
    vehicle_types=["car"],
    use_multiprocessing=False
)

result = scraper.run()

print(f"Marcas extraídas: {len(result.brands)}")
print(f"Modelos extraídos: {len(result.models)}")
print(f"Valores FIPE: {len(result.fipe_values)}")
```

### Exemplo 2: Processando os Dados Extraídos

```python
import json

# Carrega o arquivo JSON gerado
with open("output/fipe_complete.json", "r", encoding="utf-8") as f:
    data = json.load(f)

# Lista todas as marcas de carros
carros = [b for b in data["brands"] if b["vehicle_type"] == "car"]
print(f"Marcas de carros: {len(carros)}")
for marca in carros[:10]:
    print(f"  - {marca['name']}")

# Busca valores de um modelo específico
fipe_code = "001267-4"
valores = [v for v in data["fipe_values"] if v.get("fipe_code") == fipe_code]
print(f"\nValores para código FIPE {fipe_code}:")
for v in valores:
    print(f"  {v['reference_period']}: {v['average_price']}")
```

---

## 🔗 Links Úteis

- **Site FIPE**: https://veiculos.fipe.org.br/
- **Documentação Python venv**: https://docs.python.org/3/library/venv.html
