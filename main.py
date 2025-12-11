import heapq
from collections import defaultdict

class RouteOptimization:
    """
    Класс для оптимизации маршрутов между городами с учетом различных критериев.
    
    Поддерживает поиск оптимальных маршрутов по длине, времени и стоимости,
    а также выбор компромиссного маршрута на основе заданных приоритетов.
    """

    def __init__(self):
        """
        Инициализация системы оптимизации маршрутов.
        
        Создает необходимые структуры для хранения данных:
        - _route_cache: кэш для хранения параметров маршрутов
        - _road_index: индекс дорог для быстрого доступа к параметрам
        """
        self._route_cache = {}
        self._road_index = defaultdict(dict)

    def calculate(
            self,
            input_filename: str, # Путь к входному файлу с данными
            output_filename: str # Путь к выходному файлу с результатами
        ) -> None:
        """
        Выполняет расчет оптимальных маршрутов и сохраняет результаты.

        Выполняет полный цикл обработки:
        1. Парсинг входных данных
        2. Поиск оптимальных маршрутов
        3. Формирование компромиссного маршрута
        4. Запись результатов в файл
        """
    
        try:
            cities, roads, requests = self.parse_input(input_filename)
            output_lines = []

            city_to_id = {name: cid for cid, name in cities.items()}

            for start_name, end_name, priorities in requests:
                start_id = city_to_id[start_name]
                end_id = city_to_id[end_name]

                # Поиск оптимальных маршрутов по каждому критерию
                optimal_routes = {}
                weights = {'Д': 0, 'В': 1, 'С': 2}
                names = {'Д': 'ДЛИНА', 'В': 'ВРЕМЯ', 'С': 'СТОИМОСТЬ'}

                for crit, idx in weights.items():
                    route, _ = self.dijkstra(roads, start_id, end_id, idx)
                    optimal_routes[crit] = route

                # Формирование вывода для каждого оптимального маршрута
                for crit in ['Д', 'В', 'С']:
                    route = optimal_routes[crit]
                    if route:
                        city_names = [cities[cid] for cid in route]
                        length, time, cost = self.get_route_params(route)
                        line = f"{names[crit]}: {' -> '.join(city_names)} | Д={length}, В={time}, С={cost}"
                    else:
                        line = f"{names[crit]}: Маршрут не найден"
                    output_lines.append(line)

                # Поиск компромиссного маршрута
                compromise_route = self.find_compromise_route(roads, start_id, end_id, priorities)
                if compromise_route:
                    city_names = [cities[cid] for cid in compromise_route]
                    length, time, cost = self.get_route_params(compromise_route)
                    line = f"КОМПРОМИСС: {' -> '.join(city_names)} | Д={length}, В={time}, С={cost}"
                else:
                    line = "КОМПРОМИСС: Маршрут не найден"
                output_lines.append(line)

            # Запись результатов в файл
            with open(output_filename, 'w', encoding='utf-8') as f:
                f.write('\n'.join(output_lines))
        except Exception as e:
            # По условию ничего не делаем
            pass
        finally:
            # Очистка состояния
            self._route_cache.clear()
            self._road_index.clear()

    def parse_input(
            self,
            input_filename: str # Путь к входному файлу
        ) -> tuple:
        """
        Парсинг входных данных из файла.

        Возвращает кортеж с разбором данных:
        - cities: словарь городов {id: название}
        - roads: граф дорог
        - requests: список запросов на построение маршрутов
        """
        cities = {}
        roads = defaultdict(list)
        requests = []

        with open(input_filename, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        section = None
        for line in lines:
            line = line.strip()
            if not line:
                continue

            if line == '[CITIES]':
                section = 'cities'
                continue
            elif line == '[ROADS]':
                section = 'roads'
                continue
            elif line == '[REQUESTS]':
                section = 'requests'
                continue

            if section == 'cities':
                cid, name = line.split(': ', 1)
                cities[int(cid)] = name.strip()
            elif section == 'roads':
                parts = line.split(': ')
                cities_part = parts[0].strip()
                params_part = parts[1].strip()

                cid1, cid2 = map(int, cities_part.split(' - '))
                length, time, cost = map(int, params_part.split(', '))

                roads[cid1].append((cid2, length, time, cost))
                roads[cid2].append((cid1, length, time, cost))
            elif section == 'requests':
                route_part, priority_part = line.split(' | ')
                start, end = route_part.split(' -> ')
                priorities = priority_part[1:-1].split(',')

                requests.append((start, end, priorities))

        self.build_road_index(roads)

        return cities, roads, requests

    def build_road_index(
            self,
            graph: dict # Граф дорог для построения индекса
        ):
        """
        Создает индекс дорог для быстрого доступа к параметрам.

        Преобразует граф дорог в структуру, позволяющую получать параметры маршрута за O(1)
        """
        self._road_index = defaultdict(dict)
        for city in graph:
            for neighbor, length, time, cost in graph[city]:
                self._road_index[city][neighbor] = (length, time, cost)

    def dijkstra(
        self, 
        graph: dict, 
        start: int, 
        end: int, 
        weight_idx: int
    ) -> tuple[list[int], int]:
        """
        Оптимизированная версия алгоритма Дейкстры с использованием родительских указателей
        """
        pq = [(0, start)]
        visited = set()
        parent = {}  # Словарь для хранения родительских вершин
        distance = {start: 0}  # Словарь для хранения расстояний

        while pq:
            current_weight, current_node = heapq.heappop(pq)

            if current_node in visited:
                continue

            visited.add(current_node)

            if current_node == end:
                # Восстанавливаем путь из родительских указателей
                path = []
                while current_node is not None:
                    path.append(current_node)
                    current_node = parent.get(current_node)
                return path[::-1], current_weight

            for neighbor, length, time, cost in graph[current_node]:
                if neighbor in visited:
                    continue
                    
                weight = [length, time, cost][weight_idx]
                new_dist = current_weight + weight
                
                if neighbor not in distance or new_dist < distance[neighbor]:
                    distance[neighbor] = new_dist
                    parent[neighbor] = current_node
                    heapq.heappush(pq, (new_dist, neighbor))

        return None, None

    def get_route_params(
            self,
            route: list # Маршрут в виде списка ID городов
        ) -> tuple[int, int, int]:
        """
        Получение параметров маршрута.
        
        Возвращает кортеж с параметрами маршрута:
        - общая длина
        - общее время
        - общая стоимость
        """
        route_key = tuple(route)
        
        if route_key in self._route_cache:
            return self._route_cache[route_key]
        
        total_length = 0
        total_time = 0
        total_cost = 0
        
        # Используем созданный индекс для быстрого доступа
        for i in range(len(route) - 1):
            start = route[i]
            end = route[i + 1]
            
            # Получаем параметры за O(1)
            params = self._road_index[start].get(end)
            if params:
                length, time, cost = params
                total_length += length
                total_time += time
                total_cost += cost
            else:
                raise ValueError(f"Дорога между {start} и {end} не найдена")
        
        self._route_cache[route_key] = (total_length, total_time, total_cost)
        return total_length, total_time, total_cost

    def find_compromise_route(
            self,
            graph: dict,
            start_id: int,
            end_id: int,
            priorities: list
        ):
        """
        Поиск компромиссного маршрута между городами.
        
        Возвращает оптимальный маршрут, учитывающий заданные приоритеты.
        Если маршрут не найден, возвращает None.
        """

        # Поиск оптимальных маршрутов по каждому критерию
        routes = {}
        weights = {'Д': 0, 'В': 1, 'С': 2}
        
        for crit, idx in weights.items():
            route, _ = self.dijkstra(graph, start_id, end_id, idx)
            routes[crit] = route

        # Сбор уникальных маршрутов с кешированными параметрами
        candidate_routes = []
        seen = set()
        
        for crit in weights.keys():
            route = routes[crit]
            if route is None:
                continue
            route_tuple = tuple(route)
            if route_tuple not in seen:
                seen.add(route_tuple)
                # get_route_params использует кеш
                length, time, cost = self.get_route_params(route)
                candidate_routes.append({
                    'route': route,
                    'Д': length,
                    'В': time,
                    'С': cost
                })

        if not candidate_routes:
            return None

        # Последовательная фильтрация по приоритетам
        for crit in priorities:
            if not candidate_routes:
                break
            min_value = min(route[crit] for route in candidate_routes)
            candidate_routes = [
                route for route in candidate_routes 
                if route[crit] == min_value
            ]

        return candidate_routes[0]['route'] if candidate_routes else None

# Запуск
route_optimization = RouteOptimization()
route_optimization.calculate('input.txt', 'output.txt')
