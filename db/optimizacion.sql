-- ==========================================
-- OPTIMIZACION.SQL - PRACTICA 3
-- Índices para mejorar /estadisticaVentas/<año>/<pais>
-- ==========================================

-- Supuesta consulta en la API:
-- SELECT t.id, t.cliente_id, c.nombre, c.pais,
--        t.pelicula_id, t.monto, t.fecha_pago
-- FROM transacciones t
-- JOIN clientes c ON t.cliente_id = c.id
-- WHERE EXTRACT(YEAR FROM t.fecha_pago) = :anio
--   AND c.pais = :pais;


-- ==========================================
-- 1. ÍNDICE SOBRE EL PAÍS DEL CLIENTE
-- ==========================================

CREATE INDEX IF NOT EXISTS idx_clientes_pais
ON clientes(pais);


-- ==========================================
-- 2. ÍNDICE SOBRE LA FECHA DE PAGO
-- ==========================================

CREATE INDEX IF NOT EXISTS idx_transacciones_fecha_pago
ON transacciones(fecha_pago);


-- ==========================================
-- 3. ÍNDICE COMPUESTO CLIENTE + FECHA
--    (Útil para joins frecuentes por cliente_id
--     filtrando además por año de fecha_pago)
-- ==========================================

CREATE INDEX IF NOT EXISTS idx_transacciones_cliente_fecha
ON transacciones(cliente_id, fecha_pago);
