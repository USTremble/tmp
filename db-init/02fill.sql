INSERT INTO public.roles (name) VALUES ('Администратор'), ('Диспетчер');

INSERT INTO public.zones (name, location, responsible) VALUES 
('Главный цех', 'Сектор А', 'Петров А.В.'),
('Серверная', 'Этаж 2', 'Сидоров К.М.'),
('Подземная парковка', 'Уровень -1', 'Васильев П.П.');

INSERT INTO public.sensor_types (name) VALUES ('Вытяжка'), ('Приточка'), ('Датчик CO2'), ('Датчик дыма'), ('Датчик движения'), ('Датчик температуры'), ('Датчик влажности');

INSERT INTO public.sensors (name, zone_id, type_id, serial_number, status, last_inspection_date) VALUES 
('Вентилятор В-01', 1, 1, '100', 'active', '2021-01-01 10:00:00'), 
('Вентилятор В-02', 1, 1, '101', 'failure', '2026-04-01 12:00:00'),
('Кондиционер С-01', 2, 2, '200', 'active', CURRENT_TIMESTAMP),
('Газоанализатор G-01', 3, 3, '300', 'active', CURRENT_TIMESTAMP);

INSERT INTO public.users (username, password_hash, role_id) VALUES 
('admin', 'password_stub', 1);