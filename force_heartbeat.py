import asyncio
from heartbeat_engine import HeartbeatEngine
from logger_pro import setup_logger

log = setup_logger('heartbeat_test')

async def force_test():
    log.info("=== FORZANDO LATIDO DE PRUEBA (TEST DE INTEGRACIÓN) ===")
    engine = HeartbeatEngine()
    
    # Forzamos ejecución ignorando el tiempo
    for task in engine.tasks:
        log.info(f"Probando capacidad de ejecución para: {task['id']}")
        await engine.run_task(task)
    
    log.info("=== TEST COMPLETADO: EL SISTEMA ES CAPAZ DE AUTO-EJECUTARSE ===")

if __name__ == "__main__":
    asyncio.run(force_test())
