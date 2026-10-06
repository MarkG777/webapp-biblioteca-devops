# Uso de herramientas de IA

Este proyecto se desarrolló con ayuda de **Claude** (Anthropic), un asistente de IA, usado desde Claude Code en VS Code.

## Para qué se usó

- Resolver errores de código: por ejemplo, la prueba de Jest que fallaba por un id repetido, el bloqueo de llaves foráneas en SQLite y los errores de compilación de LaTeX.
- Resolver errores de configuración: Docker Desktop, el Security Group de EC2, el workflow de GitHub Actions y los secretos del repositorio.
- Explicar conceptos que yo no dominaba, como EC2, Docker Hub, SSH, pruebas con Jest y cobertura de código.
- Redactar borradores de documentación técnica (este README y los reportes), que yo revisé y ajusté.

## Qué hice yo

- Definí qué se quería construir y en qué orden: la API, las pruebas, el pipeline y el despliegue.
- Ejecuté cada comando, revisé su salida y decidí si lo aceptaba.
- Probé la API en local y en la instancia EC2 antes de dar algo por terminado.
- Configuré los secretos en GitHub y la instancia en AWS, y verifiqué en cada paso que los resultados fueran los esperados.
- Entendí el flujo completo antes de subir cambios. Cuando algo no quedaba claro, lo pregunté y lo comprobé con la documentación oficial.

## Criterio

La IA me explicó y me ayudó a corregir errores, pero no sustituyó el entendimiento de lo que hace cada parte del proyecto. Las decisiones de diseño (por ejemplo, usar Jest para los endpoints y pytest para la cobertura del código Python, o mantener las IPs y llaves fuera del repositorio) las tomé yo y puedo justificarlas.
