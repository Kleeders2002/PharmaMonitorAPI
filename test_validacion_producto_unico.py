"""
Script de prueba para validar que solo se puede monitorear un producto a la vez.

Este script demuestra la nueva validación que impide crear un ProductoMonitoreado
si ya existe uno activo (con fecha_finalizacion_monitoreo == None).
"""
from sqlmodel import Session, create_engine, select
from core.models.productomonitoreado import ProductoMonitoreado
from core.models.productofarmaceutico import ProductoFarmaceutico
from core.repositories.producto_monitoreado_repository import create_producto_monitoreado
from core.ports.registro_port import RegistroPort
from fastapi import HTTPException
import os
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

def test_validacion_producto_unico():
    """Prueba la validación de producto único activo."""

    # Crear motor de base de datos para pruebas
    DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:pass@localhost/testdb")
    engine = create_engine(DATABASE_URL)

    print("=" * 70)
    print("TEST: Validación de Producto Monitoreado Único")
    print("=" * 70)

    with Session(engine) as session:
        # Verificar si ya existe un producto activo
        stmt = select(ProductoMonitoreado).where(
            ProductoMonitoreado.fecha_finalizacion_monitoreo == None
        )
        producto_activo = session.exec(stmt).first()

        if producto_activo:
            print(f"\n✅ Ya existe un producto activo:")
            print(f"   ID: {producto_activo.id}")
            print(f"   ID Producto: {producto_activo.id_producto}")
            print(f"   Ubicación: {producto_activo.localizacion}")
            print(f"   Inicio: {producto_activo.fecha_inicio_monitoreo}")

            # Intentar crear un segundo producto monitoreado
            print("\n⚠️  Intentando crear un segundo producto monitoreado...")

            # Crear un producto farmacéutico de prueba
            nuevo_producto = ProductoMonitoreado(
                id_producto=1,  # Ajustar según BD
                localizacion="Ubicación de prueba",
                cantidad=10
            )

            # Mock de dependencias necesarias
            class MockRegistro:
                def registrar(self, **kwargs):
                    pass

            class MockUser:
                id = 1
                nombre = "Usuario Test"
                rol = "admin"

            try:
                create_producto_monitoreado(
                    session=session,
                    producto_monitoreado=nuevo_producto,
                    registro=MockRegistro(),
                    current_user=MockUser()
                )
                print("❌ ERROR: La validación NO funcionó. Se permitió crear un segundo producto.")
                return False

            except HTTPException as e:
                print("✅ VALIDACIÓN EXITOSA:")
                print(f"   Status Code: {e.status_code}")
                print(f"   Detalle: {e.detail}")
                return True

        else:
            print("\n⚠️  No hay productos con monitoreo activo en la base de datos.")
            print("   No se puede probar la validación sin un producto activo.")
            print("\n💡 Para probar:")
            print("   1. Activa el monitoreo de un producto (POST /productosmonitoreados/)")
            print("   2. Ejecuta este script nuevamente")
            print("   3. Debería rechazar la creación de un segundo producto")
            return None

if __name__ == "__main__":
    try:
        resultado = test_validacion_producto_unico()
        print("\n" + "=" * 70)
        if resultado is True:
            print("RESULTADO: ✅ La validación funciona correctamente")
        elif resultado is False:
            print("RESULTADO: ❌ La validación NO está funcionando")
        else:
            print("RESULTADO: ⚠️  Prueba no ejecutada (sin datos)")
        print("=" * 70)
    except Exception as e:
        print(f"\n❌ Error en el test: {str(e)}")
        import traceback
        traceback.print_exc()
