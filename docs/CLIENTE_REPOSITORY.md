## 📖 Cliente Repository - Guía Rápida

### ✅ Implementado

Archivo: `infra/repositories/cliente_repository.py`

5 funciones simples para acceder a datos de clientes:

### 📋 Funciones

#### 1. **cargar_perfil(cliente: str) -> dict**
```python
from infra.repositories.cliente_repository import cargar_perfil

perfil = cargar_perfil("cliente_demo")
print(perfil)  # {'nombre': '...', 'sector': '...', ...}
```

#### 2. **cargar_tb(cliente: str) -> pd.DataFrame**
```python
from infra.repositories.cliente_repository import cargar_tb

tb = cargar_tb("cliente_demo")
print(tb.shape)  # (500, 3)
print(tb.head())
```

#### 3. **cargar_hallazgos(cliente: str) -> list**
```python
from infra.repositories.cliente_repository import cargar_hallazgos

hallazgos = cargar_hallazgos("cliente_demo")
print(len(hallazgos))  # 3
```

#### 4. **cargar_patrones(cliente: str) -> list**
```python
from infra.repositories.cliente_repository import cargar_patrones

patrones = cargar_patrones("cliente_demo")
print(patrones)  # [...]
```

#### 5. **guardar_materialidad(cliente: str, data: dict) -> bool**
```python
from infra.repositories.cliente_repository import guardar_materialidad

data = {
    "revenue_threshold": 5000000,
    "profit_threshold": 500000
}
exito = guardar_materialidad("cliente_demo", data)
# Guarda en: data/clientes/cliente_demo/materialidad.yaml
```

### 🛡️ Manejo de Errores

- Si un archivo **no existe** → retorna vacío (`{}`, `[]`, `pd.DataFrame()`)
- Si ocurre un **error** → imprime mensaje y retorna vacío
- **Nunca rompe la ejecución**

### 🌍 Estructura de carpetas esperada

```
data/clientes/cliente_demo/
├── perfil.yaml
├── tb.xlsx
├── hallazgos_previos.yaml
├── patrones.yaml
└── materialidad.yaml (creado por guardar_materialidad)
```

### 🧪 Prueba Rápida

```bash
python test_cliente_repo_demo.py
```

### 📌 Notas

- Usa `yaml` y `pandas` (asegúrate de tener instaladas: `pip install pyyaml pandas`)
- Las rutas se calculan automáticamente desde la ubicación del archivo
- Soporta múltiples clientes: `cargar_perfil("bf_holding_2025")`
- Encoding UTF-8 para caracteres especiales
