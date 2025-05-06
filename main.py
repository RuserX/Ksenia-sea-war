import pygame
import numpy as np
import random
import sys

# запускаем pygame
pygame.init()


# настройки игрового поля
GRID_SIZE = 8  # поле x на x клеток
CELL_SIZE = 40  # размер одной клетки
MARGIN = 60  # отступ от края окна

# задаем размеры окна
WINDOW_HEIGHT = 800  # высота окна
WINDOW_WIDTH = 1000  # ширина окна


def calculate_ships_for_grid(grid_size):
    """
    Рассчитывает допустимое количество кораблей для заданного размера поля.
    Размер поля определяет максимальный размер корабля и их количество.
    Обязательно добавляются однопалубные корабли.
    """
    # Определяем максимальный размер корабля в зависимости от размера поля
    if grid_size <= 6:
        max_ship_size = 2
    elif grid_size <= 8:
        max_ship_size = 3
    else:
        max_ship_size = 4

    # Рассчитываем максимальное количество клеток под корабли (примерно 25% поля)
    total_cells = grid_size * grid_size
    max_ship_cells = int(total_cells * 0.25)

    ships = {}
    current_cells = 0

    # Распределяем корабли по размерам
    for size in range(max_ship_size, 0, -1):
        # Количество кораблей зависит от их размера и размера поля
        if size == 4:
            count = 1
        elif size == 3:
            count = grid_size // 3
        elif size == 2:
            count = grid_size // 2
        else:  # для однопалубных
            count = grid_size // 2 + 1

        # Проверяем, не превысим ли лимит клеток
        new_cells = size * count
        if current_cells + new_cells <= max_ship_cells:
            ships[size] = count
            current_cells += new_cells
        else:
            # Если превышаем, берем меньшее количество
            remaining_cells = max_ship_cells - current_cells
            possible_count = remaining_cells // size
            if possible_count > 0:
                ships[size] = possible_count
                current_cells += possible_count * size

    # Убеждаемся, что есть хотя бы один однопалубный корабль
    if 1 not in ships:
        ships[1] = 1

    return ships


# автоматически рассчитываем корабли для заданного размера поля
SHIPS = calculate_ships_for_grid(GRID_SIZE)
print(f"Размер поля: {GRID_SIZE}x{GRID_SIZE}")
print(f"Расстановка кораблей: {SHIPS}")

# задаем разные цвета, которые будем использовать
WHITE = (255, 255, 255)  # белый для фона
BLACK = (0, 0, 0)  # черный для сетки
GRAY = (128, 128, 128)  # серый для промахов
RED = (255, 0, 0)  # красный для попаданий
BLUE = (0, 0, 255)  # синий для кораблей
GREEN = (0, 255, 0)  # зеленый пока не используется, может пригодится

# значения для клеток поля
EMPTY = 0  # пустая клетка
SHIP = 1  # клетка с кораблем
MISS = 2  # клетка с промахом
HIT = 3  # клетка с попаданием


class BattleshipGame:
    def __init__(self):
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption("Морской бой")
        self.font = pygame.font.Font(None, 36)
        self.horizontal = True

        # Создаем игровые поля
        self.player_field = np.zeros((GRID_SIZE, GRID_SIZE))
        self.computer_field = np.zeros((GRID_SIZE, GRID_SIZE))
        self.computer_visible_field = np.zeros((GRID_SIZE, GRID_SIZE))

        self.ships_to_place = SHIPS.copy()
        # Находим максимальный размер корабля в автоматически созданном словаре
        self.current_ship_size = max(SHIPS.keys())

        self.is_game_started = False
        self.is_player_turn = True
        self.game_over = False

        # Счетчики попаданий
        self.player_hits = 0
        self.computer_hits = 0
        self.total_ship_cells = sum(size * count for size, count in SHIPS.items())

        # Размещаем корабли компьютера
        self.place_computer_ships()

    def display_message(self, message, y_offset=0):
        """
        Выводит сообщение на экран
        message - само сообщение
        y_offset - сдвиг сообщения вверх или вниз (если нужно несколько сообщений)
        """
        text = self.font.render(message, True, BLACK)  # создаем текст
        # размещаем текст по центру внизу экрана (можно сдвинуть по y при помощи y_offset)
        text_rect = text.get_rect(
            center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT - 100 + y_offset)
        )
        self.screen.blit(text, text_rect)  # отображаем текст на экране

    def draw_game_state(self):
        """
        Рисует текущее состояние игры:
        - подсказки при расстановке кораблей
        - информацию о ходе игры
        - количество попаданий
        """
        if self.game_over:  # если игра закончена
            # показываем результат игры
            result = (
                "Вы победили!"
                if self.player_hits == self.total_ship_cells
                else "Компьютер победил!"
            )
            self.display_message(result, -60)
            # показываем сообщение о том, как закрыть игру
            self.display_message("Нажмите крестик, чтобы закрыть игру", 60)

        if not self.is_game_started:  # если игра еще не началась (расставляем корабли)
            # показываем информацию о текущем корабле
            ships_left = f"Разместите корабль размером {self.current_ship_size} ({self.ships_to_place[self.current_ship_size]} осталось)"
            orientation = "Горизонтально" if self.horizontal else "Вертикально"

            # выводим подсказки
            self.display_message(ships_left, -60)
            self.display_message(f"Ориентация: {orientation} (ПКМ для изменения)", -20)
            self.display_message("ЛКМ для размещения корабля", 20)

            # показываем сколько каких кораблей осталось разместить
            remaining = "Осталось разместить: "
            for size, count in self.ships_to_place.items():
                if count > 0:
                    remaining += f"{count}x{size} "  # например: 1x4 2x3 3x2
            self.display_message(remaining, 60)
        else:  # если игра уже идет
            if not self.game_over:  # и игра не закончилась
                # показываем статистику попаданий
                player_status = f"Вы попали: {self.player_hits}/{self.total_ship_cells}"
                computer_status = (
                    f"Компьютер попал: {self.computer_hits}/{self.total_ship_cells}"
                )
                self.display_message(player_status, -20)
                self.display_message(computer_status, 20)

                # показываем чей сейчас ход
                turn_message = "Ваш ход" if self.is_player_turn else "Ход компьютера"
                self.display_message(turn_message, -60)

                # если ход игрока, показываем подсказку
                if self.is_player_turn:
                    self.display_message(
                        "Кликните по правому полю, чтобы атаковать", 60
                    )

        # подписываем поля игрока и компьютера
        player_field_text = self.font.render("Ваше поле", True, BLACK)
        computer_field_text = self.font.render("Поле компьютера", True, BLACK)

        # размещаем подписи над полями
        self.screen.blit(player_field_text, (MARGIN, MARGIN - 30))
        self.screen.blit(computer_field_text, (WINDOW_WIDTH // 2 + MARGIN, MARGIN - 30))

    def place_computer_ships(self):
        """
        Компьютер расставляет свои корабли случайным образом
        """
        # перебираем все корабли
        for ship_size, count in SHIPS.items():
            # для каждого размера корабля расставляем нужное количество
            for _ in range(count):
                while True:  # пытаемся поставить корабль, пока не получится
                    # выбираем случайные координаты
                    x = random.randint(
                        0, GRID_SIZE - 1
                    )  # случайная позиция по горизонтали
                    y = random.randint(
                        0, GRID_SIZE - 1
                    )  # случайная позиция по вертикали
                    horizontal = random.choice([True, False])  # случайная ориентация

                    # проверяем, можно ли поставить корабль
                    if self.can_place_ship(
                        self.computer_field, x, y, ship_size, horizontal
                    ):
                        # если можно - ставим и переходим к следующему кораблю
                        self.place_ship(
                            self.computer_field, x, y, ship_size, horizontal
                        )
                        break  # выходим из while True

    def can_place_ship(self, field, x, y, size, horizontal):
        """
        Проверяет, можно ли поставить корабль в указанное место
        field - поле, на котором ставим
        x, y - координаты начала корабля
        size - размер корабля
        horizontal - как ставим (горизонтально или вертикально)
        """
        if horizontal:  # если ставим горизонтально
            if x + size > GRID_SIZE:  # проверяем, не вылезет ли корабль за поле вправо
                return False
            # проверяем клетки вокруг корабля (корабли не должны касаться друг друга)
            for i in range(max(0, x - 1), min(GRID_SIZE, x + size + 1)):
                for j in range(max(0, y - 1), min(GRID_SIZE, y + 2)):
                    if field[j][i] != 0:  # если клетка не пустая
                        return False
        else:  # если ставим вертикально
            if y + size > GRID_SIZE:  # проверяем, не вылезет ли корабль за поле вниз
                return False
            # проверяем клетки вокруг корабля
            for i in range(max(0, x - 1), min(GRID_SIZE, x + 2)):
                for j in range(max(0, y - 1), min(GRID_SIZE, y + size + 1)):
                    if field[j][i] != 0:  # если клетка не пустая
                        return False
        return True  # если все проверки прошли - корабль можно ставить

    def place_ship(self, field, x, y, size, horizontal):
        """
        Ставит корабль на поле
        field - поле, на котором ставим
        x, y - координаты начала корабля
        size - размер корабля
        horizontal - как ставим (горизонтально или вертикально)
        """
        if horizontal:  # если горизонтально
            field[y, x : x + size] = SHIP  # заполняем клетки по горизонтали
        else:  # если вертикально
            field[y : y + size, x] = SHIP  # заполняем клетки по вертикали

    def draw_grid(self, left_top_x):
        """
        Рисует сетку игрового поля
        left_top_x - отступ слева (чтобы нарисовать два поля рядом)
        """
        # рисуем вертикальные и горизонтальные линии
        for i in range(GRID_SIZE):
            for j in range(GRID_SIZE):
                # рисуем квадратик для каждой клетки
                pygame.draw.rect(
                    self.screen,  # где рисуем
                    BLACK,  # каким цветом
                    (
                        left_top_x + j * CELL_SIZE,  # координата х
                        MARGIN + i * CELL_SIZE,  # координата у
                        CELL_SIZE,  # ширина клетки
                        CELL_SIZE,  # высота клетки
                    ),
                    1,  # толщина линии (1 пиксель)
                )

    def draw_ships(self):
        """
        Рисует корабли и попадания/промахи на обоих полях
        """
        # сначала рисуем поле игрока
        for i in range(GRID_SIZE):
            for j in range(GRID_SIZE):
                if self.player_field[i][j] == SHIP:  # если в клетке корабль
                    # рисуем синий квадратик
                    pygame.draw.rect(
                        self.screen,
                        BLUE,
                        (
                            MARGIN + j * CELL_SIZE,
                            MARGIN + i * CELL_SIZE,
                            CELL_SIZE - 1,
                            CELL_SIZE - 1,
                        ),
                    )
                elif self.player_field[i][j] == MISS:  # если в клетке промах
                    # рисуем серый кружок
                    pygame.draw.circle(
                        self.screen,
                        GRAY,
                        (
                            MARGIN + j * CELL_SIZE + CELL_SIZE // 2,
                            MARGIN + i * CELL_SIZE + CELL_SIZE // 2,
                        ),
                        5,  # радиус кружка
                    )
                elif self.player_field[i][j] == HIT:  # если в клетке попадание
                    # рисуем красный квадратик
                    pygame.draw.rect(
                        self.screen,
                        RED,
                        (
                            MARGIN + j * CELL_SIZE,
                            MARGIN + i * CELL_SIZE,
                            CELL_SIZE - 1,
                            CELL_SIZE - 1,
                        ),
                    )
        # теперь рисуем поле компьютера (только то, что видит игрок)
        for i in range(GRID_SIZE):
            for j in range(GRID_SIZE):
                if self.computer_visible_field[i][j] == MISS:  # если промах
                    # рисуем серый кружок
                    pygame.draw.circle(
                        self.screen,
                        GRAY,
                        (
                            WINDOW_WIDTH // 2 + MARGIN + j * CELL_SIZE + CELL_SIZE // 2,
                            MARGIN + i * CELL_SIZE + CELL_SIZE // 2,
                        ),
                        5,
                    )
                elif self.computer_visible_field[i][j] == HIT:  # если попадание
                    # рисуем красный квадратик
                    pygame.draw.rect(
                        self.screen,
                        RED,
                        (
                            WINDOW_WIDTH // 2 + MARGIN + j * CELL_SIZE,
                            MARGIN + i * CELL_SIZE,
                            CELL_SIZE - 1,
                            CELL_SIZE - 1,
                        ),
                    )

    def check_game_over(self):
        """
        Проверяет, не закончилась ли игра
        Возвращает сообщение о победителе или None, если игра продолжается
        """
        # если игрок попал во все клетки с кораблями компьютера
        if self.player_hits == self.total_ship_cells:
            self.game_over = True
            return "Вы победили!"
        # если компьютер попал во все клетки с кораблями игрока
        elif self.computer_hits == self.total_ship_cells:
            self.game_over = True
            return "Компьютер победил!"
        return None  # игра продолжается

    def computer_move(self):
        """
        Ход компьютера (пока что просто случайные выстрелы)
        """
        while True:  # пытаемся сделать ход, пока не получится
            # выбираем случайные координаты для выстрела
            x = random.randint(0, GRID_SIZE - 1)
            y = random.randint(0, GRID_SIZE - 1)
            # проверяем, не стреляли ли мы уже в эту клетку
            if self.player_field[y][x] in [EMPTY, SHIP]:
                if self.player_field[y][x] == EMPTY:
                    self.player_field[y][x] = MISS  # если пусто - промах
                    self.is_player_turn = True  # передаем ход игроку
                else:
                    self.player_field[y][x] = HIT  # если корабль - попадание
                    self.computer_hits += 1  # увеличиваем счетчик попаданий
                break  # ход сделан, выходим из цикла

    def handle_click(self, pos, button):
        """
        Обрабатывает клики мышкой
        pos - координаты клика
        button - какая кнопка нажата (1 - левая, 3 - правая)
        """
        # пересчитываем координаты клика в координаты поля
        x = (pos[0] - (WINDOW_WIDTH // 2 + MARGIN)) // CELL_SIZE
        y = (pos[1] - MARGIN) // CELL_SIZE

        if not self.is_game_started:  # если расставляем корабли
            x = (pos[0] - MARGIN) // CELL_SIZE  # координаты для левого поля
            if 0 <= x < GRID_SIZE and 0 <= y < GRID_SIZE:  # если кликнули по полю
                if button == 3:  # правая кнопка - меняем ориентацию
                    self.horizontal = not self.horizontal
                elif button == 1:  # левая кнопка - пытаемся поставить корабль
                    if (
                        self.ships_to_place[self.current_ship_size] > 0
                    ):  # если остались корабли
                        # проверяем, можно ли поставить корабль
                        if self.can_place_ship(
                            self.player_field,
                            x,
                            y,
                            self.current_ship_size,
                            self.horizontal,
                        ):
                            # ставим корабль
                            self.place_ship(
                                self.player_field,
                                x,
                                y,
                                self.current_ship_size,
                                self.horizontal,
                            )
                            # уменьшаем количество кораблей этого размера
                            self.ships_to_place[self.current_ship_size] -= 1

                            # если корабли этого размера закончились
                            if self.ships_to_place[self.current_ship_size] == 0:
                                # ищем следующий размер корабля
                                sizes = list(self.ships_to_place.keys())
                                sizes.sort(reverse=True)  # от большего к меньшему
                                for size in sizes:
                                    if self.ships_to_place[size] > 0:
                                        self.current_ship_size = size
                                        break
                                else:  # если все корабли расставлены
                                    self.is_game_started = True  # начинаем игру

        # если игра началась и ход игрока
        elif self.is_player_turn and 0 <= x < GRID_SIZE and 0 <= y < GRID_SIZE:
            # если в эту клетку еще не стреляли
            if self.computer_visible_field[y][x] == EMPTY:
                if self.computer_field[y][x] == EMPTY:
                    self.computer_visible_field[y][x] = MISS  # промах
                    self.is_player_turn = False  # передаем ход компьютеру
                else:
                    self.computer_visible_field[y][x] = HIT  # попадание
                    self.player_hits += 1  # увеличиваем счетчик попаданий

    def run(self):
        """
        Основной игровой цикл
        """
        running = True
        while running:
            self.screen.fill(WHITE)  # заполняем экран белым

            # рисуем сетку для обоих полей
            self.draw_grid(MARGIN)  # левое поле
            self.draw_grid(WINDOW_WIDTH // 2 + MARGIN)  # правое поле

            self.draw_ships()  # рисуем корабли и попадания/промахи
            self.draw_game_state()  # рисуем информацию о состоянии игры

            # проверяем, не закончилась ли игра
            game_result = self.check_game_over()
            if game_result and not self.game_over:  # добавляем проверку флага game_over
                self.game_over = True  # отмечаем что игра закончена
                self.display_message(game_result, -100)  # показываем результат

            # обрабатываем события pygame
            for event in pygame.event.get():
                if event.type == pygame.QUIT:  # если нажали крестик
                    running = False
                elif event.type == pygame.MOUSEBUTTONDOWN and not self.game_over:
                    # если кликнули мышкой и игра не закончена
                    self.handle_click(event.pos, event.button)

            # если ход компьютера
            if not self.is_player_turn and self.is_game_started and not self.game_over:
                pygame.time.wait(500)  # ждем пол секунды (чтобы успеть увидеть ход)
                self.computer_move()  # компьютер делает ход

            pygame.display.flip()  # обновляем экран

        pygame.quit()  # закрываем pygame


# запускаем игру, если файл запущен напрямую
if __name__ == "__main__":
    game = BattleshipGame()  # создаем игру
    game.run()  # запускаем игру
