"""
Esquemas Pydantic para comunicación bidireccional con NodeMCU.

Nueva arquitectura:
- NodeMCU → Backend (POST /nodemcu/data con sensores)
- Backend → NodeMCU (RESPONSE: {"led_color": "verde|amarillo|rojo"})
"""
from typing import Optional
from pydantic import BaseModel, Field, field_validator


class NodeMCUDataSchema(BaseModel):
    """
    Datos enviados desde el NodeMCU al backend.

    Todos los campos son opcionales porque los sensores pueden fallar
    individualmente.
    """
    temperatura: Optional[float] = Field(None, description="Temperatura en °C")
    humedad: Optional[float] = Field(None, description="Humedad relativa en %")
    lux: Optional[float] = Field(None, description="Nivel de luz en lux")
    presion: Optional[float] = Field(None, description="Presión atmosférica en hPa")

    @field_validator('humedad')
    @classmethod
    def validar_humedad(cls, v: Optional[float]) -> Optional[float]:
        """Valida que la humedad esté en un rango razonable (0-100%)"""
        if v is not None:
            if v < 0 or v > 100:
                print(f"⚠️  Humedad imposible recibida: {v}% - Rechazando")
                return None
        return v

    @field_validator('temperatura')
    @classmethod
    def validar_temperatura(cls, v: Optional[float]) -> Optional[float]:
        """Valida que la temperatura esté en un rango razonable (-40 a 80°C)"""
        if v is not None:
            if v < -40 or v > 80:
                print(f"⚠️  Temperatura imposible recibida: {v}°C - Rechazando")
                return None
        return v

    @field_validator('lux')
    @classmethod
    def validar_lux(cls, v: Optional[float]) -> Optional[float]:
        """Valida que el lux esté en un rango razonable (0 a 100,000)"""
        if v is not None:
            if v < 0 or v > 100000:
                print(f"⚠️  Lux imposible recibido: {v} - Rechazando")
                return None
        return v

    @field_validator('presion')
    @classmethod
    def validar_presion(cls, v: Optional[float]) -> Optional[float]:
        """Valida que la presión esté en un rango razonable (300 a 1100 hPa)"""
        if v is not None:
            if v < 300 or v > 1100:
                print(f"⚠️  Presión imposible recibida: {v} hPa - Rechazando")
                return None
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "temperatura": 5.2,
                "humedad": 65.0,
                "lux": 150.0,
                "presion": 1013.0
            }
        }


class LEDResponseSchema(BaseModel):
    """
    Respuesta del backend al NodeMCU con el comando LED.

    El NodeMCU debe usar este color para configurar el LED RGB.
    """
    led_color: str = Field(..., description="Color del LED: 'verde', 'amarillo', o 'rojo'")
    status: str = Field(..., description="Mensaje de estado para debugging")

    class Config:
        json_schema_extra = {
            "example": {
                "led_color": "verde",
                "status": "Datos procesados correctamente"
            }
        }
