# Histórico de concluidas: Huelva y Málaga — estado 2026-10-27 21:50 UTC

Hecho:
- Puja máxima de concluidas (`refresh --concluidas`) y parser de "ha recibido alguna puja". Commit 52afcf4.
- Histórico de Sevilla parcial: vivienda PC completo (539), vivienda FS 2.220 de 5.051. Commit 729d024.
  El proceso lo mató Claude Code por poca memoria del equipo, no por el script.
- Huelva (21): vivienda PC completo (208); vivienda FS 887 de 1.883. Málaga (29): vivienda PC 240 de 431.
  Ritmo ~6,4 s por ficha (~560 por tanda de 60 min). Sin captcha; algún ConnectionError que se reintenta solo.
- Análisis listo en `privado/hu_ma.py` (zonas Aracena/Ronda de `privado/sierra.py`, costa HU/MA,
  Málaga capital aparte; marcas VH/NUDA/CUOTA). Uso: `python privado/hu_ma.py [tope]`.

Pendiente:
1. Histórico de Huelva (21) y Málaga (29): `python -u run.py historico --provincias 29 --max-minutos 120`
   y luego `--provincias 21`. Reanudable; repetir hasta que no salgan "nuevas". Falta: HU vivienda FS (~1.000),
   MA vivienda PC (~190) y FS, y solar/finca_rustica de ambas. Prueba: recuento de concluidas por provincia.
   Después: `python privado/hu_ma.py` y presentar activas y vendidas por zona.
2. Completar Sevilla FS: `python -u run.py historico --provincias 41`.
3. Antes de cada push: fusionar la BD local con la del CI (el CI escribe la misma BD a las 03:15 UTC).
   Fusión por SQL: base = BD remota (`git show origin/master:data/subastas.db`), insertar filas que solo
   están en local y rellenar con COALESCE las columnas nulas en remoto. Regenerar visor
   (`python run.py viewer --no-abrir`) y commitear BD + `web_publicar/index.html`.
   Ojo: las filas que en local pasaron a 'concluida' y en remoto siguen activas se copian enteras desde local
   (COALESCE no cambia el estado). Parar el rastreo antes de fusionar y apartar cualquier `subastas.db-journal`.
4. Subastas con varios lotes (609 concluidas sin dato): el portal da una puja por lote y la BD guarda una
   fila por subasta. Cambio de modelo pendiente de decidir.
