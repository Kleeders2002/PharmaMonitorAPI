from sqlmodel import SQLModel

class DashboardMetricsRead(SQLModel):
    usuarios_registrados: int
    productos_inventario: int
    alertas_activas: int
    monitoreos_activos: int