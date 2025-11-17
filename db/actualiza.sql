-- ==========================================
-- ACTUALIZA.SQL - PRACTICA 3
-- Extiende el schema de la Práctica 2
-- ==========================================

-- ==========================================
-- 1. NUEVOS CAMPOS REQUERIDOS POR LA P3
-- ==========================================

-- País y descuento del cliente
ALTER TABLE clientes
    ADD COLUMN IF NOT EXISTS pais VARCHAR(100),
    ADD COLUMN IF NOT EXISTS descuento_percent NUMERIC(5,2) NOT NULL DEFAULT 0;

-- Stock y valoración media de las películas
ALTER TABLE peliculas
    ADD COLUMN IF NOT EXISTS stock INT NOT NULL DEFAULT 100,
    ADD COLUMN IF NOT EXISTS valoracion_media NUMERIC(4,2) NOT NULL DEFAULT 0;

-- Fecha de pago en transacciones
ALTER TABLE transacciones
    ADD COLUMN IF NOT EXISTS fecha_pago TIMESTAMP;


-- ==========================================
-- 2. TABLAS PARA GESTIÓN DE CARRITO
-- ==========================================

-- Carritos de compra
CREATE TABLE IF NOT EXISTS carritos (
    id SERIAL PRIMARY KEY,
    cliente_id INT NOT NULL REFERENCES clientes(id),
    estado VARCHAR(20) NOT NULL DEFAULT 'ABIERTO',  -- ABIERTO / PAGADO / CANCELADO
    total DECIMAL(10,2) NOT NULL DEFAULT 0
);

-- Películas dentro de cada carrito
CREATE TABLE IF NOT EXISTS carrito_peliculas (
    id SERIAL PRIMARY KEY,
    carrito_id INT NOT NULL REFERENCES carritos(id) ON DELETE CASCADE,
    pelicula_id INT NOT NULL REFERENCES peliculas(id),
    cantidad INT NOT NULL CHECK (cantidad > 0),
    precio_unitario DECIMAL(10,2) NOT NULL
);


-- ==========================================
-- 3. FUNCION AUXILIAR: RECALCULAR TOTAL CARRITO
-- ==========================================

CREATE OR REPLACE FUNCTION recalc_total_carrito(p_carrito_id INT)
RETURNS VOID AS $$
BEGIN
    UPDATE carritos
    SET total = COALESCE(
        (
            SELECT SUM(cantidad * precio_unitario)
            FROM carrito_peliculas
            WHERE carrito_id = p_carrito_id
        ),
        0
    )
    WHERE id = p_carrito_id;
END;
$$ LANGUAGE plpgsql;


-- ==========================================
-- 4. TRIGGERS SOBRE CARRITO_PELICULAS
--    (STOCK + TOTAL)
-- ==========================================

-- INSERT: resta stock y recalcula total
CREATE OR REPLACE FUNCTION trg_carrito_peliculas_insert_fn()
RETURNS TRIGGER AS $$
BEGIN
    -- Restar stock de la película
    UPDATE peliculas
    SET stock = stock - NEW.cantidad
    WHERE id = NEW.pelicula_id;

    -- Recalcular total del carrito
    PERFORM recalc_total_carrito(NEW.carrito_id);

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE TRIGGER trg_carrito_peliculas_insert
AFTER INSERT ON carrito_peliculas
FOR EACH ROW
EXECUTE FUNCTION trg_carrito_peliculas_insert_fn();


-- UPDATE: devuelve stock antiguo, resta el nuevo y recalcula total
CREATE OR REPLACE FUNCTION trg_carrito_peliculas_update_fn()
RETURNS TRIGGER AS $$
BEGIN
    -- Devolver stock por la cantidad antigua
    UPDATE peliculas
    SET stock = stock + OLD.cantidad
    WHERE id = OLD.pelicula_id;

    -- Restar stock por la cantidad nueva
    UPDATE peliculas
    SET stock = stock - NEW.cantidad
    WHERE id = NEW.pelicula_id;

    -- Recalcular total del carrito
    PERFORM recalc_total_carrito(NEW.carrito_id);

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE TRIGGER trg_carrito_peliculas_update
AFTER UPDATE ON carrito_peliculas
FOR EACH ROW
EXECUTE FUNCTION trg_carrito_peliculas_update_fn();


-- DELETE: devuelve stock y recalcula total
CREATE OR REPLACE FUNCTION trg_carrito_peliculas_delete_fn()
RETURNS TRIGGER AS $$
BEGIN
    -- Devolver stock
    UPDATE peliculas
    SET stock = stock + OLD.cantidad
    WHERE id = OLD.pelicula_id;

    -- Recalcular total del carrito
    PERFORM recalc_total_carrito(OLD.carrito_id);

    RETURN OLD;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE TRIGGER trg_carrito_peliculas_delete
AFTER DELETE ON carrito_peliculas
FOR EACH ROW
EXECUTE FUNCTION trg_carrito_peliculas_delete_fn();


-- ==========================================
-- 5. TRIGGER DE PAGO DE CARRITO
--    (DESCUENTO + SALDO + TRANSACCIONES)
-- ==========================================

CREATE OR REPLACE FUNCTION trg_carrito_pagar_fn()
RETURNS TRIGGER AS $$
DECLARE
    v_descuento NUMERIC(5,2);
    v_total_original DECIMAL(10,2);
    v_total_con_descuento DECIMAL(10,2);
    r_item RECORD;
BEGIN
    -- Solo actuamos cuando el carrito pasa a PAGADO
    IF OLD.estado <> 'PAGADO' AND NEW.estado = 'PAGADO' THEN

        -- =======================================
        -- SLEEP para estudiar bloqueos/deadlocks
        -- Mientras dura este pg_sleep, en otra
        -- sesión puedes:
        --   * consultar al cliente
        --   * intentar cambiar su descuento
        --   * provocar deadlocks, etc.
        -- =======================================
        PERFORM pg_sleep(10);  -- 10 segundos (ajusta si quieres)

        -- Obtener descuento del cliente
        SELECT descuento_percent
        INTO v_descuento
        FROM clientes
        WHERE id = NEW.cliente_id;

        -- Total original del carrito (ya calculado por triggers de carrito_peliculas)
        v_total_original := NEW.total;

        -- Aplicar descuento
        v_total_con_descuento := v_total_original * (1 - v_descuento / 100.0);

        -- Actualizar saldo del cliente
        UPDATE clientes
        SET saldo = saldo - v_total_con_descuento
        WHERE id = NEW.cliente_id;

        -- Crear transacciones por cada película del carrito
        FOR r_item IN
            SELECT pelicula_id, cantidad, precio_unitario
            FROM carrito_peliculas
            WHERE carrito_id = NEW.id
        LOOP
            INSERT INTO transacciones (cliente_id, pelicula_id, monto, fecha, fecha_pago)
            VALUES (
                NEW.cliente_id,
                r_item.pelicula_id,
                r_item.cantidad * r_item.precio_unitario * (1 - v_descuento / 100.0),
                NOW(),
                NOW()
            );
        END LOOP;
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;


CREATE OR REPLACE TRIGGER trg_carrito_pagar
AFTER UPDATE ON carritos
FOR EACH ROW
EXECUTE FUNCTION trg_carrito_pagar_fn();


-- ==========================================
-- 6. PROCEDURE + TRIGGER PARA VALORACION MEDIA
-- ==========================================

-- Procedure para recalcular la valoración media de una película
CREATE OR REPLACE PROCEDURE recalcula_valoracion_pelicula(p_pelicula_id INT)
LANGUAGE plpgsql AS $$
DECLARE
    v_media NUMERIC(4,2);
BEGIN
    SELECT AVG(puntuacion)::NUMERIC(4,2)
    INTO v_media
    FROM valoraciones
    WHERE pelicula_id = p_pelicula_id;

    UPDATE peliculas
    SET valoracion_media = COALESCE(v_media, 0)
    WHERE id = p_pelicula_id;
END;
$$;


-- Función de trigger sobre valoraciones
CREATE OR REPLACE FUNCTION trg_valoraciones_cambio_fn()
RETURNS TRIGGER AS $$
DECLARE
    v_pelicula_id INT;
BEGIN
    IF TG_OP = 'INSERT' OR TG_OP = 'UPDATE' THEN
        v_pelicula_id := NEW.pelicula_id;
    ELSE
        v_pelicula_id := OLD.pelicula_id;
    END IF;

    CALL recalcula_valoracion_pelicula(v_pelicula_id);

    IF TG_OP = 'DELETE' THEN
        RETURN OLD;
    ELSE
        RETURN NEW;
    END IF;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE TRIGGER trg_valoraciones_cambio
AFTER INSERT OR UPDATE OR DELETE ON valoraciones
FOR EACH ROW
EXECUTE FUNCTION trg_valoraciones_cambio_fn();


-- ==========================================
-- QUITAR ON DELETE CASCADE DE TABLAS LIGADAS A CLIENTES
-- (para estudiar borraPais y las FK a mano)
-- ==========================================

-- cliente_pelicula: eliminar FK con CASCADE y crearla sin CASCADE
ALTER TABLE cliente_pelicula
    DROP CONSTRAINT IF EXISTS cliente_pelicula_cliente_id_fkey;

ALTER TABLE cliente_pelicula
    ADD CONSTRAINT cliente_pelicula_cliente_id_fkey
    FOREIGN KEY (cliente_id) REFERENCES clientes(id);

-- valoraciones
ALTER TABLE valoraciones
    DROP CONSTRAINT IF EXISTS valoraciones_cliente_id_fkey;

ALTER TABLE valoraciones
    ADD CONSTRAINT valoraciones_cliente_id_fkey
    FOREIGN KEY (cliente_id) REFERENCES clientes(id);

-- transacciones
ALTER TABLE transacciones
    DROP CONSTRAINT IF EXISTS transacciones_cliente_id_fkey;

ALTER TABLE transacciones
    ADD CONSTRAINT transacciones_cliente_id_fkey
    FOREIGN KEY (cliente_id) REFERENCES clientes(id);
