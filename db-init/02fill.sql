INSERT INTO public.roles (name) VALUES ('Администратор'), ('Диспетчер');

INSERT INTO public.zones (name, location, responsible) VALUES 
('Главный цех', 'Сектор А', 'Петров А.В.'),
('Серверная', 'Этаж 2', 'Сидоров К.М.'),
('Подземная парковка', 'Уровень -1', 'Васильев П.П.');

INSERT INTO public.sensor_types (name) VALUES ('Вытяжка'), ('Приточка'), ('Датчик CO2');

INSERT INTO public.sensors (name, zone_id, type_id, serial_number, status) VALUES 
('Вентилятор В-01', 1, 1, 'SN-100', 'active'),
('Вентилятор В-02', 1, 1, 'SN-101', 'failure'),
('Кондиционер С-01', 2, 2, 'SN-200', 'active'),
('Газоанализатор G-01', 3, 3, 'SN-300', 'active');

INSERT INTO public.users (username, password_hash, role_id) VALUES 
('admin', 'password_stub', 1);