"""
Utilidades para manejo de fechas con zona horaria de Venezuela.

Este módulo provee funciones para trabajar con datetime en la zona horaria
de Venezuela (UTC-4) de manera consistente en toda la aplicación.
"""
from datetime import datetime, timezone, timedelta


# Zona horaria de Venezuela (UTC-4)
# Usamos un timezone fijo ya que Venezuela no cambia por horario de verano
VENEZUELA_OFFSET = timedelta(hours=-4)
VENEZUELA_TZ = timezone(timedelta(hours=-4), name="America/Caracas")


def get_caracas_now() -> datetime:
    """
    Obtiene la fecha y hora actual en Caracas, Venezuela.

    Returns:
        datetime: Fecha/hora actual en Venezuela (UTC-4)
        Simplemente resta 4 horas a la hora UTC.

    Example:
        >>> from core.utils.datetime_utils import get_caracas_now
        >>> ahora = get_caracas_now()
        >>> print(ahora)
        2025-02-01 19:14:30
    """
    # Obtener hora UTC y restar 4 horas
    from datetime import timedelta
    utc_now = datetime.utcnow()
    caracas_now = utc_now - timedelta(hours=4)
    return caracas_now


def ensure_caracas_timezone(dt: datetime) -> datetime:
    """
    Asegura que un datetime tenga la zona horaria de Venezuela.

    Si el datetime no tiene timezone, se asume que es hora local de Venezuela
    y se le asigna la zona horaria correspondiente.

    Args:
        dt: datetime a procesar

    Returns:
        datetime: Con timezone de Venezuela

    Example:
        >>> from datetime import datetime
        >>> from core.utils.datetime_utils import ensure_caracas_timezone
        >>> dt = datetime(2025, 2, 1, 19, 14)
        >>> dt_tz = ensure_caracas_timezone(dt)
        >>> print(dt_tz)
        2025-02-01 19:14:00-04:00
    """
    if dt.tzinfo is None:
        # Si no tiene timezone, asumir que es hora de Venezuela
        return dt.replace(tzinfo=VENEZUELA_TZ)
    else:
        # Si ya tiene timezone, convertir a Venezuela
        return dt.astimezone(VENEZUELA_TZ)
