-- init.sql
-- Se ejecuta al iniciar el contenedor la primera vez
-- Lanza schema.sql, populate.sql y actualiza.sql en ese orden

\i '/sql/schema.sql'
\i '/sql/populate.sql'
\i '/sql/actualiza.sql'
