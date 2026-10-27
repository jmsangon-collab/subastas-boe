# Análisis de subastas concluidas (Sevilla) — 2026-10-17

1. Histórico robusto: `buscar` acepta rango de fecha fin y el histórico parte el rango
   cuando el BOE responde "búsqueda excesiva"; guarda `estado_portal` (PC/FS).
   Prueba: Sevilla/vivienda/FS devuelve ids en vez de "[!] demasiado amplia".
2. Puja máxima: `pujas()` lee "Puja máxima de la subasta" (texto suelto).
   Prueba: SUB-AT-2026-25R4186001911 -> 172.411,93 €.
3. Rastreo: `python run.py historico --provincias 41` (reanudable, solo pide lo que falta).
   Prueba: recuento de concluidas de Sevilla en la BD ~ recuento del portal.
4. Análisis (script en scratchpad): % adjudicación sobre valor, desiertas, por subtipo,
   tipo de subasta (AEAT/judicial), municipio, tramo de precio y año.
5. Commit + push de código y BD antes de las 03:15 UTC (CI escribe la misma BD).
