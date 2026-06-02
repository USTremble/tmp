CREATE TABLE IF NOT EXISTS public.roles
(
    role_id SERIAL,
    name character varying(32) NOT NULL,
    CONSTRAINT roles_pkey PRIMARY KEY (role_id)
);


CREATE TABLE IF NOT EXISTS public.users
(
    user_id SERIAL,
    username character varying(50) NOT NULL,
    password_hash text NOT NULL,
    telegram_id bigint,
    role_id integer NOT NULL,
    CONSTRAINT users_pkey PRIMARY KEY (user_id),
    CONSTRAINT users_username_key UNIQUE (username),
    CONSTRAINT users_role_id_fkey FOREIGN KEY (role_id)
        REFERENCES public.roles (role_id) ON DELETE NO ACTION
);

CREATE TABLE IF NOT EXISTS public.zones
(
    zone_id SERIAL,
    name character varying(32) NOT NULL,
    location character varying(50),
    responsible character varying(32),
    CONSTRAINT zones_pkey PRIMARY KEY (zone_id)
);


CREATE TABLE IF NOT EXISTS public.sensor_types
(
    type_id SERIAL,
    name character varying(32) NOT NULL,
    CONSTRAINT sensor_types_pkey PRIMARY KEY (type_id),
    CONSTRAINT sensor_types_name_key UNIQUE (name)
);

CREATE TABLE IF NOT EXISTS public.sensors
(
    sensor_id SERIAL,
    name character varying(32) NOT NULL,
    zone_id integer NOT NULL,
    type_id integer NOT NULL,
    serial_number character varying(50),
    last_inspection_date timestamp DEFAULT CURRENT_TIMESTAMP,
    status character varying(32) NOT NULL,
    CONSTRAINT sensors_pkey PRIMARY KEY (sensor_id),
    CONSTRAINT sensors_zone_id_fkey FOREIGN KEY (zone_id)
        REFERENCES public.zones (zone_id) ON DELETE CASCADE,
    CONSTRAINT sensors_type_id_fkey FOREIGN KEY (type_id)
        REFERENCES public.sensor_types (type_id) ON DELETE NO ACTION
);

CREATE TABLE IF NOT EXISTS public.sensor_history
(
    event_id SERIAL,
    sensor_id integer NOT NULL,
    user_id integer NOT NULL,
    event_type character varying(32) NOT NULL,
    event_date timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
    notes text,
    CONSTRAINT sensor_history_pkey PRIMARY KEY (event_id),
    CONSTRAINT sensor_history_sensor_id_fkey FOREIGN KEY (sensor_id)
        REFERENCES public.sensors (sensor_id) ON DELETE CASCADE,
    CONSTRAINT sensor_history_user_id_fkey FOREIGN KEY (user_id)
        REFERENCES public.users (user_id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS public.sensor_subscriptions
(
    sub_id SERIAL,
    user_id integer NOT NULL,
    zone_id integer NOT NULL,
    CONSTRAINT sensor_subscriptions_pkey PRIMARY KEY (sub_id),
    CONSTRAINT sensor_subscriptions_user_id_fkey FOREIGN KEY (user_id)
        REFERENCES public.users (user_id) ON DELETE CASCADE,
    CONSTRAINT sensor_subscriptions_zone_id_fkey FOREIGN KEY (zone_id)
        REFERENCES public.zones (zone_id) ON DELETE CASCADE
);

