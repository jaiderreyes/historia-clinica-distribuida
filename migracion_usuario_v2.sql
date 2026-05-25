-- Migracion: agregar columnas faltantes a la tabla usuario
-- Ejecutar en los 3 nodos si las tablas ya existen
-- Es seguro ejecutar multiples veces (IF NOT EXISTS)

ALTER TABLE usuario ADD COLUMN IF NOT EXISTS tipo_documento         VARCHAR(10);
ALTER TABLE usuario ADD COLUMN IF NOT EXISTS unidad_edad            VARCHAR(5)  DEFAULT '1';
ALTER TABLE usuario ADD COLUMN IF NOT EXISTS fhir_patient_id        VARCHAR(64);
ALTER TABLE usuario ADD COLUMN IF NOT EXISTS created_at             TIMESTAMP   DEFAULT NOW();
ALTER TABLE usuario ADD COLUMN IF NOT EXISTS updated_at             TIMESTAMP   DEFAULT NOW();
