"""
Excepciones personalizadas de SocioAI.
Permite distinguir errores de negocio de errores técnicos.
"""
from __future__ import annotations


class SocioAIError(Exception):
    """Base para todas las excepciones de SocioAI."""
    pass


class ClienteNoEncontradoError(SocioAIError):
    """El cliente solicitado no existe en el repositorio."""
    def __init__(self, cliente: str) -> None:
        self.cliente = cliente
        super().__init__(f"Cliente no encontrado: '{cliente}'")


class PerfilInvalidoError(SocioAIError):
    """El perfil del cliente existe pero tiene estructura inválida."""
    def __init__(self, cliente: str, detalle: str = "") -> None:
        self.cliente = cliente
        msg = f"Perfil inválido para '{cliente}'"
        if detalle:
            msg += f": {detalle}"
        super().__init__(msg)


class TBNoEncontradoError(SocioAIError):
    """No se encontró el Trial Balance del cliente."""
    def __init__(self, cliente: str) -> None:
        self.cliente = cliente
        super().__init__(f"Trial Balance no encontrado para '{cliente}'")


class TBInvalidoError(SocioAIError):
    """El TB existe pero no se puede procesar."""
    def __init__(self, cliente: str, detalle: str = "") -> None:
        self.cliente = cliente
        msg = f"TB inválido para '{cliente}'"
        if detalle:
            msg += f": {detalle}"
        super().__init__(msg)


class MaterialidadNoDefinidaError(SocioAIError):
    """No se ha definido materialidad para el cliente."""
    def __init__(self, cliente: str) -> None:
        self.cliente = cliente
        super().__init__(
            f"Materialidad no definida para '{cliente}'. "
            "Use sugerir_materialidad() primero."
        )


class AreaNoEncontradaError(SocioAIError):
    """El código L/S solicitado no existe en el TB del cliente."""
    def __init__(self, cliente: str, codigo_ls: str) -> None:
        self.cliente = cliente
        self.codigo_ls = codigo_ls
        super().__init__(
            f"Área L/S '{codigo_ls}' no encontrada para '{cliente}'"
        )


class LLMError(SocioAIError):
    """Error al llamar al modelo de lenguaje."""
    def __init__(self, detalle: str = "") -> None:
        msg = "Error en llamada al LLM"
        if detalle:
            msg += f": {detalle}"
        super().__init__(msg)


class ConfiguracionError(SocioAIError):
    """Error de configuración del sistema."""
    pass
