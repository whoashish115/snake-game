import sys
import random
import math
import os
from PyQt6.QtCore import Qt, QTimer, QPointF, QEasingCurve, QPropertyAnimation, pyqtProperty
from PyQt6.QtGui import QPainter, QColor, QFont,QIcon, QLinearGradient, QPolygonF
from PyQt6.QtWidgets import QApplication, QWidget, QLabel, QPushButton, QVBoxLayout, QHBoxLayout, QStackedLayout, QComboBox, QDialog, QFormLayout, QSpinBox, QDialogButtonBox
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput
from PyQt6.QtCore import QUrl

def distance_points(p1, p2):
    return math.hypot(p1.x() - p2.x(), p1.y() - p2.y())

def angle_between_points(p1, p2):
    dx = p2.x() - p1.x()
    dy = p2.y() - p1.y()
    angle = math.degrees(math.atan2(dy, dx)) % 360
    return angle


class AnimatedShape:
    def __init__(self, shape_type, pos, size, color, speed):
        self.shape_type = shape_type 
        self.pos = pos
        self.size = size
        self.color = color
        self.speed = speed
        self.direction = QPointF(random.uniform(-1, 1), random.uniform(-1, 1))
        length = math.hypot(self.direction.x(), self.direction.y()) or 1
        self.direction /= length

    def update(self, width, height):
        self.pos += self.direction * self.speed

        if self.pos.x() < self.size or self.pos.x() > width - self.size:
            self.direction.setX(-self.direction.x())
        if self.pos.y() < self.size or self.pos.y() > height - self.size:
            self.direction.setY(-self.direction.y())

    def draw(self, painter):
        glow_alpha = 90
        main_alpha = 190
        glow_color = QColor(self.color.red(), self.color.green(), self.color.blue(), glow_alpha)
        main_color = QColor(self.color.red(), self.color.green(), self.color.blue(), main_alpha)

        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(Qt.PenStyle.NoPen)

        for size in range(self.size + 8, self.size + 22, 7):
            alpha = max(12, glow_alpha - (size - self.size) * 7)
            glow_color.setAlpha(alpha)
            painter.setBrush(glow_color)
            painter.drawEllipse(self.pos, size, size)

        painter.setBrush(main_color)
        if self.shape_type == 'circle':
            painter.drawEllipse(self.pos, self.size, self.size)
        elif self.shape_type == 'triangle':
            points = QPolygonF([
                QPointF(self.pos.x(), self.pos.y() - self.size),
                QPointF(self.pos.x() - self.size * 0.866, self.pos.y() + self.size * 0.5),
                QPointF(self.pos.x() + self.size * 0.866, self.pos.y() + self.size * 0.5),
            ])
            painter.drawPolygon(points)



class Food:
    def __init__(self, x, y, size=None):
        if size is None:
            self.size = random.choice([4, 6, 8, 10, 12]) 
        else:
            self.size = size

        self.pos = QPointF(x, y)
        self.point_value = self.calculate_points()

    def calculate_points(self):
        if self.size <= 4:
            return 5
        elif self.size <= 6:
            return 10
        elif self.size <= 8:
            return 15
        elif self.size <= 10:
            return 25
        else:
            return 40

    def draw(self, painter: QPainter):
        glow_color = QColor(0, 190, 255, 80)
        main_color = QColor(0, 190, 255, 210)
        painter.setPen(Qt.PenStyle.NoPen)

        for glow_size in range(self.size + 4, self.size + 14, 5):
            alpha = max(5, 50 - glow_size * 2)
            painter.setBrush(QColor(glow_color.red(), glow_color.green(), glow_color.blue(), alpha))
            painter.drawEllipse(self.pos, glow_size, glow_size)

        painter.setBrush(main_color)
        painter.drawEllipse(self.pos, self.size, self.size)

class Snake:
    def __init__(self, x, y, color, is_player=False, speed=2.5, turn_speed=4.5):
        self.positions = [QPointF(x, y)]
        self.length = 20
        self.speed = speed
        self.direction = 0  
        self.color = color
        self.is_player = is_player
        self.alive = True
        self.turn_speed = turn_speed
        self.grow_segments = 0
        self.max_length = 200
        self.score = 0
        self.kill_count = 0
        self.target_food = None

    def head_pos(self):
        return self.positions[0]

    def update(self, foods, keys=None):
        if not self.alive:
            return

        if self.is_player and keys:
            if keys.get(Qt.Key.Key_Left, False) or keys.get(Qt.Key.Key_A, False):
                self.direction -= self.turn_speed
            if keys.get(Qt.Key.Key_Right, False) or keys.get(Qt.Key.Key_D, False):
                self.direction += self.turn_speed

        if not self.is_player:
            if not foods:
                return
            if not self.target_food or self.target_food not in foods:
                self.target_food = min(foods, key=lambda f: distance_points(self.head_pos(), f.pos))
            target_angle = angle_between_points(self.head_pos(), self.target_food.pos)
            angle_diff = (target_angle - self.direction + 360) % 360

            if angle_diff > 5 and angle_diff < 180:
                self.direction += min(self.turn_speed, angle_diff)
            elif angle_diff >= 180 and angle_diff < 355:
                self.direction -= min(self.turn_speed, 360 - angle_diff)

            self.direction %= 360

        rad = math.radians(self.direction)
        dx = math.cos(rad) * self.speed
        dy = math.sin(rad) * self.speed
        new_head = QPointF(self.head_pos().x() + dx, self.head_pos().y() + dy)

        if new_head.x() < 0:
            new_head.setX(800 + new_head.x())
        elif new_head.x() > 800:
            new_head.setX(new_head.x() - 800)
        if new_head.y() < 0:
            new_head.setY(600 + new_head.y())
        elif new_head.y() > 600:
            new_head.setY(new_head.y() - 600)

        self.positions.insert(0, new_head)

        if self.grow_segments > 0:
            self.grow_segments -= 1
        else:
            if len(self.positions) > self.length:
                self.positions.pop()

        if len(self.positions) > self.max_length:
            self.positions.pop()

    def grow(self, amount=5):
        self.length += amount
        self.grow_segments += amount
        self.score += amount

    def draw(self, painter):
        if not self.alive:
            return

        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        glow_color = QColor(self.color.red(), self.color.green(), self.color.blue(), 80)
        main_color = QColor(self.color.red(), self.color.green(), self.color.blue(), 200)

        for pos in self.positions:
            painter.setBrush(glow_color)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(pos, 12, 12)

        for pos in self.positions:
            painter.setBrush(main_color)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(pos, 8, 8)

        head = self.positions[0]
        painter.setBrush(QColor(255, 255, 255, 220))
        painter.drawEllipse(head, 10, 10)

        eye_offset = QPointF(math.cos(math.radians(self.direction)) * 6,
                             math.sin(math.radians(self.direction)) * 6)
        eye_pos = head + eye_offset
        painter.setBrush(QColor(20, 20, 20))
        painter.drawEllipse(eye_pos, 3, 3)

    def collides_with_point(self, point, size=10):
        for pos in self.positions:
            if distance_points(pos, point) < size:
                return True
        return False

    def collides_with_self(self):
        head = self.positions[0]
        for pos in self.positions[5:]:
            if distance_points(head, pos) < 8:
                return True
        return False

    def collides_with_snake(self, other):
        head = self.positions[0]
        for pos in other.positions[1:]:
            if distance_points(head, pos) < 8:
                return True
        return False


class AnimatedGradient(QWidget):
    def __init__(self, colors=None, speed=0.5):
        super().__init__()
        self.colors = colors or [
            QColor(0, 60, 160),
            QColor(0, 100, 220),
            QColor(0, 140, 255),
            QColor(0, 100, 220),
            QColor(0, 60, 160)
        ]
        self.offset = 0.0
        self.speed = speed

        self.timer = QTimer()
        self.timer.timeout.connect(self.advance)
        self.timer.start(30) 

    def advance(self):
        self.offset += self.speed
        if self.offset >= self.height():
            self.offset = 0
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        h = self.height()
        w = self.width()

        gradient = QLinearGradient(0, -self.offset, 0, h - self.offset)
        step = 1 / (len(self.colors) - 1)

        for i, color in enumerate(self.colors):
            gradient.setColorAt(i * step, color)

        painter.fillRect(0, 0, w, h, gradient)


class GlassPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAutoFillBackground(False)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = self.rect()

        color = QColor(140, 140, 140, 40)
        painter.setBrush(color)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(rect, 15, 15)


class AnimatedButton(QPushButton):
    def __init__(self, text):
        super().__init__(text)
        self.default_color = QColor(10, 90, 230)
        self.hover_color = QColor(0, 140, 255)
        self.glow_color = QColor(0, 160, 255, 150)

        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFont(QFont("Segoe UI", 14, QFont.Weight.DemiBold))
        self.setMinimumHeight(40)
        self.setStyleSheet(self.generate_stylesheet(self.default_color))

        self._glow_opacity = 0.0
        self.anim = QPropertyAnimation(self, b"glow_opacity")
        self.anim.setDuration(300)
        self.anim.setEasingCurve(QEasingCurve.Type.InOutQuad)

    def generate_stylesheet(self, color):
        return f"""
        QPushButton {{
            background-color: rgba({color.red()}, {color.green()}, {color.blue()}, 220);
            border: none;
            border-radius: 12px;
            color: white;
            padding: 8px 24px;
        }}
        QPushButton:pressed {{
            background-color: rgba({color.red()}, {color.green()}, {color.blue()}, 180);
        }}
        """

    def enterEvent(self, event):
        self.anim.stop()
        self.anim.setEndValue(1.0)
        self.anim.start()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.anim.stop()
        self.anim.setEndValue(0.0)
        self.anim.start()
        super().leaveEvent(event)

    def paintEvent(self, event):
        if self._glow_opacity > 0:
            painter = QPainter(self)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            glow_color = QColor(self.glow_color)
            glow_color.setAlphaF(self._glow_opacity)
            painter.setBrush(glow_color)
            painter.setPen(Qt.PenStyle.NoPen)
            rect = self.rect().adjusted(1, 1, -1, -1)
            painter.drawRoundedRect(rect, 12, 12)
        
        super().paintEvent(event)

    def get_glow_opacity(self):
        return self._glow_opacity

    def set_glow_opacity(self, value):
        self._glow_opacity = value
        self.update()

    glow_opacity = pyqtProperty(float, fget=get_glow_opacity, fset=set_glow_opacity)


class StartupWidget(QWidget):
    def __init__(self, start_callback):
        super().__init__()
        self.start_callback = start_callback
        self.player_speed = 2.5 
        self.bot_speed = 1.5 
        self.setFixedSize(800, 600)

        self.bg_shapes = []
        self.init_animated_shapes()

        self.gradient_bg = AnimatedGradient(self)
        self.gradient_bg.setGeometry(self.rect())

        self.panel = GlassPanel(self)
        self.panel.setGeometry(150, 150, 500, 300)

        self.player = QMediaPlayer()
        self.audio_output = QAudioOutput()
        self.player.setAudioOutput(self.audio_output)

        current_dir = os.path.dirname(os.path.abspath(__file__))
        music_path = os.path.join(current_dir, "assets/sounds/startup.mp3")
        music_url = QUrl.fromLocalFile(music_path)

        self.player.setSource(music_url)
        self.audio_output.setVolume(0.5)
        self.player.setLoops(QMediaPlayer.Loops.Infinite)
        self.player.play()


        layout = QVBoxLayout(self.panel)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(25)

        title = QLabel("SNAKE GAME")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setFont(QFont("Segoe UI", 36, QFont.Weight.Bold))
        title.setStyleSheet("color: white;background:transparent;")
        layout.addWidget(title)

        layout.addSpacing(15)

        self.level_combo = QComboBox()
        self.level_combo.addItems(["Easy", "Medium", "Hard"])
        self.level_combo.setFixedHeight(36)
        self.level_combo.setStyleSheet(
            """
            QComboBox {
                background-color: rgba(255,255,255,0.1);
                color: white;
                border: 2px solid rgba(0, 140, 255, 0.7);
                border-radius: 10px;
                padding-left: 12px;
                font-size: 16px;
                font-weight: 600;
            }
            QComboBox::drop-down {
                border: none;
            }
            QComboBox QAbstractItemView {
                background-color: rgba(10, 10, 30, 0.8);
                selection-background-color: rgba(0, 140, 255, 0.6);
                color: white;
            }
            """
        )
        layout.addWidget(self.level_combo)

        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(30)

        self.settings_btn = AnimatedButton("Settings")
        self.start_btn = AnimatedButton("Start Game")
        btn_layout.addWidget(self.settings_btn)
        btn_layout.addWidget(self.start_btn)

        layout.addLayout(btn_layout)
        layout.addStretch()

        self.settings_btn.clicked.connect(self.open_settings)
        self.start_btn.clicked.connect(self.start_game)

        self.timer = QTimer()
        self.timer.timeout.connect(self.animate)
        self.timer.start(40) 

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.gradient_bg.setGeometry(self.rect())
        self.panel.setGeometry(150, 150, 500, 300)

    def init_animated_shapes(self):
        for _ in range(12):
            shape = AnimatedShape(
                shape_type=random.choice(['circle', 'triangle']),
                pos=QPointF(random.uniform(100, 700), random.uniform(100, 500)),
                size=random.randint(14, 24),
                color=QColor(0, 180, 255),
                speed=random.uniform(0.2, 0.8),
            )
            self.bg_shapes.append(shape)

    def animate(self):
        for shape in self.bg_shapes:
            shape.update(self.width(), self.height())
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        for shape in self.bg_shapes:
            shape.draw(painter)

    def open_settings(self):
        dlg = SettingsDialog()
        if dlg.exec():
            self.player_speed, self.bot_speed = dlg.get_values()
            print(f"Custom speeds - Player: {self.player_speed}, Bot: {self.bot_speed}")

    def start_game(self):
        self.player.stop() 
        level = self.level_combo.currentText()
        self.start_callback(level, self.player_speed, self.bot_speed)


class SettingsDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Settings")
        self.setWindowIcon(QIcon("assets/images/icon.ico"))
        self.setFixedSize(280, 140)

        layout = QFormLayout()
        self.speed_spin = QSpinBox()
        self.speed_spin.setRange(1, 10)
        self.speed_spin.setValue(3)
        self.bot_speed_spin = QSpinBox()
        self.bot_speed_spin.setRange(1, 40)
        self.bot_speed_spin.setValue(2)

        layout.addRow("Player Speed:", self.speed_spin)
        layout.addRow("Bot Speed:", self.bot_speed_spin)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        layout.addWidget(buttons)
        self.setLayout(layout)

    def get_values(self):
        return self.speed_spin.value(), self.bot_speed_spin.value()


import random
from PyQt6.QtWidgets import QWidget, QPushButton, QVBoxLayout, QHBoxLayout
from PyQt6.QtCore import QTimer, QPointF, Qt
from PyQt6.QtGui import QColor, QPainter, QFont

class GameWidget(QWidget):
    def __init__(self, level="Easy", player_speed=2.5, bot_speed=1.5):
        super().__init__()
        self.setFixedSize(800, 600)
        self.level = level
        self.player_speed = player_speed
        self.bot_speed = bot_speed

        self.player_snake = Snake(400, 300, QColor(0, 170, 255), is_player=True, speed=self.player_speed)
        bot_count = {
            "Easy": 1,
            "Medium": 2,
            "Hard": 4
        }.get(self.level, 2) 

        self.bots = [
            Snake(random.randint(100, 700), random.randint(100, 500), QColor(0, 120, 180), speed=self.bot_speed)
            for _ in range(bot_count)
        ]
        for bot in self.bots:
            bot.respawn_timer = 0

        self.foods = []
        self.spawn_food()

        self.timer = QTimer()
        self.timer.timeout.connect(self.game_loop)
        self.timer.start(30)  

        self.keys = {}

        self.game_over = False
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setFocus()

        self.restart_btn = QPushButton("Restart")
        self.restart_btn.clicked.connect(self.restart_game)
        self.restart_btn.setVisible(False)
        self.restart_btn.setFixedWidth(120)
        self.restart_btn.setStyleSheet(
            """
            QPushButton {
                background-color: #0055ff;
                color: white;
                font-weight: bold;
                font-size: 18px;
                border-radius: 12px;
                padding: 12px 24px;
            }
            QPushButton:hover {
                background-color: #003bb5;
            }
            """
        )

        self.home_btn = QPushButton("Home")
        self.home_btn.clicked.connect(self.go_home) 
        self.home_btn.setVisible(False)
        self.home_btn.setFixedWidth(120)
        self.home_btn.setStyleSheet(
            """
            QPushButton {
                background-color: #999999;
                color: white;
                font-weight: bold;
                font-size: 18px;
                border-radius: 12px;
                padding: 12px 24px;
            }
            QPushButton:hover {
                background-color: #003bb5;
            }
            """
        )


        self.layout = QVBoxLayout(self)
        self.layout.addStretch()
        hbox = QHBoxLayout()
        hbox.addStretch()
        hbox.addWidget(self.restart_btn)
        hbox.addStretch()
        self.layout.addLayout(hbox)
        self.layout.setContentsMargins(0, 0, 20, 20)

        hbox2 = QHBoxLayout()
        hbox2.addStretch()
        hbox2.addWidget(self.home_btn)
        hbox2.addStretch()

        self.layout.addLayout(hbox2)

        self.base_speed = self.player_speed      
        self.max_speed = self.player_speed + 2.0 
        self.speed_increase_rate = 0.05          
        self.speed_decrease_rate = 0.1            
        self.speed_current = self.base_speed    

        
        self.bg_music_player = QMediaPlayer()
        self.bg_music_output = QAudioOutput()
        self.bg_music_player.setAudioOutput(self.bg_music_output)
        bg_music_path = os.path.abspath("assets/sounds/game_music.mp3")
        self.bg_music_player.setSource(QUrl.fromLocalFile(bg_music_path))
        self.bg_music_output.setVolume(0.3)
        self.bg_music_player.setLoops(QMediaPlayer.Loops.Infinite)
        self.bg_music_player.play()

        self.game_over_player = QMediaPlayer()
        self.game_over_output = QAudioOutput()
        self.game_over_player.setAudioOutput(self.game_over_output)
        game_over_path = os.path.abspath("assets/sounds/game_over.mp3")
        self.game_over_player.setSource(QUrl.fromLocalFile(game_over_path))
        self.game_over_output.setVolume(0.7)

        self.game_over_sound_played = False
        self.food_drop_timer = 0
        self.speed_was_boosted_last_frame = False


    def spawn_food(self):
        while len(self.foods) < 10:
            x = random.randint(20, 780)
            y = random.randint(20, 580)
            pos = QPointF(x, y)

            collision = False
            for snake in [self.player_snake] + self.bots:
                if snake.collides_with_point(pos, size=20):
                    collision = True
                    break
            if not collision:
                self.foods.append(Food(x, y))

    def respawn_snake(self, snake):
        new_x = random.uniform(50, 750)
        new_y = random.uniform(50, 550)
        snake.positions = [QPointF(new_x, new_y)]
        snake.length = 20
        snake.direction = random.uniform(0, 360)
        snake.alive = True
        snake.grow_segments = 0

    def game_loop(self):
        arrow_keys = [Qt.Key.Key_Up, Qt.Key.Key_Down, Qt.Key.Key_Left, Qt.Key.Key_Right]
        any_arrow_pressed = any(self.keys.get(k, False) for k in arrow_keys)

        previous_speed = self.speed_current

        if any_arrow_pressed and self.player_snake.score > 0:
            if self.speed_current < self.max_speed:
                self.speed_current = min(self.max_speed, self.speed_current + self.speed_increase_rate)
        else:
            if self.speed_current > self.base_speed:
                self.speed_current = max(self.base_speed, self.speed_current - self.speed_decrease_rate)

        if (
            self.speed_current > self.base_speed and
            self.speed_was_boosted_last_frame and
            self.speed_current <= previous_speed and
            self.player_snake.score > 0
        ):
            self.player_snake.score = max(0, self.player_snake.score - 0.5)

        self.speed_was_boosted_last_frame = (self.speed_current > self.base_speed)

        if self.speed_current > previous_speed:
            self.food_drop_timer += 1

            if self.food_drop_timer >= 10:
                if hasattr(self.player_snake, "positions") and len(self.player_snake.positions) > 5:
                    tail_pos = self.player_snake.positions[-1]
                    before_tail_pos = self.player_snake.positions[-2]

                    dx = tail_pos.x() - before_tail_pos.x()
                    dy = tail_pos.y() - before_tail_pos.y()

                    length = (dx**2 + dy**2) ** 0.5
                    if length == 0:
                        length = 1 

                    offset_x = dx / length * 10
                    offset_y = dy / length * 10

                    food_x = tail_pos.x() + offset_x
                    food_y = tail_pos.y() + offset_y

                    small_food = Food(food_x, food_y, size=4)
                    self.foods.append(small_food)

                self.food_drop_timer = 0
        else:
            self.food_drop_timer = 0

        self.player_snake.speed = self.speed_current

        if self.player_snake.alive and not self.game_over:
            self.player_snake.update(self.foods, self.keys)

        respawn_delay = 120

        for bot in self.bots:
            if not hasattr(bot, 'respawn_timer'):
                bot.respawn_timer = 0
            if not bot.alive:
                bot.respawn_timer += 1
                if bot.respawn_timer >= respawn_delay:
                    self.respawn_snake(bot)
                    bot.respawn_timer = 0
                continue
            bot.update(self.foods)

        for food in self.foods[:]:
            collision_radius = max(food.size + 4, 12)

            if self.player_snake.collides_with_point(food.pos, size=collision_radius):
                self.foods.remove(food)
                self.player_snake.grow(3)
                self.player_snake.score += 10

            for bot in self.bots:
                if bot.collides_with_point(food.pos, size=collision_radius):
                    if food in self.foods:
                        self.foods.remove(food)
                    bot.grow(3)

        for bot in self.bots:
            if bot.alive and distance_points(self.player_snake.head_pos(), bot.head_pos()) < 12:
                self.player_snake.alive = False
                bot.alive = False
                bot.kill_count += 1
                self.game_over = True
                self.update()
                return

        for bot in self.bots:
            if bot.alive and self.player_snake.collides_with_snake(bot):
                self.player_snake.alive = False
                bot.kill_count += 1
                self.game_over = True
                self.update()
                return

        for bot in self.bots[:]:
            if bot.alive and self.player_snake.alive and bot.collides_with_snake(self.player_snake):
                bot.alive = False
                self.player_snake.kill_count += 1
                self.player_snake.score += 100

        for i in range(len(self.bots)):
            for j in range(i + 1, len(self.bots)):
                bot1 = self.bots[i]
                bot2 = self.bots[j]
                if bot1.alive and bot2.alive:
                    if distance_points(bot1.head_pos(), bot2.head_pos()) < 12:
                        bot1.alive = False
                        bot2.alive = False
                        bot1.kill_count += 1
                        bot2.kill_count += 1

        self.spawn_food()
        self.update()

        if self.game_over:
            self.restart_btn.setVisible(True)
            self.home_btn.setVisible(True)

            if not self.game_over_sound_played:
                print("Game over detected: stopping music and playing game over sound")

                if self.bg_music_player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
                    self.bg_music_player.stop()

                self.game_over_player.play()
                self.game_over_sound_played = True

            return

    def go_home(self):
        parent = self.parent()
        while parent and not isinstance(parent, MainWindow):
            parent = parent.parent()
        if isinstance(parent, MainWindow):
            if self.game_over_player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
                self.game_over_player.stop()

            parent.go_home_from_game()

    def restart_game(self):
        if self.game_over_player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self.game_over_player.stop()
        self.player_snake = Snake(400, 300, QColor(0, 170, 255), is_player=True, speed=self.player_speed)
        self.bots = [
            Snake(random.randint(100, 700), random.randint(100, 500), QColor(0, 120, 180), speed=self.bot_speed),
            Snake(random.randint(100, 700), random.randint(100, 500), QColor(0, 120, 180), speed=self.bot_speed)
        ]
        for bot in self.bots:
            bot.respawn_timer = 0
        self.foods.clear()
        self.spawn_food()
        self.game_over = False
        self.restart_btn.setVisible(False)
        self.home_btn.setVisible(False)

        self.speed_current = self.base_speed
        self.player_snake.speed = self.base_speed

        if self.bg_music_player.playbackState() != QMediaPlayer.PlaybackState.PlayingState:
            print("Restarting background music")
            self.bg_music_player.play()

        self.game_over_sound_played = False

        self.update()

    def keyPressEvent(self, event):
        self.keys[event.key()] = True
        super().keyPressEvent(event)

    def keyReleaseEvent(self, event):
        self.keys[event.key()] = False
        super().keyReleaseEvent(event)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor(10, 10, 20)) 

        for food in self.foods:
            food.draw(painter)

        self.player_snake.draw(painter)
        for bot in self.bots:
            bot.draw(painter)

        painter.setFont(QFont("Segoe UI", 14))
        painter.setPen(QColor(255, 255, 255))
        painter.drawText(10, 25, f"Kill Count: {self.player_snake.kill_count}")
        painter.drawText(10, 50, f"Score: {self.player_snake.score}")

        if self.game_over:
            overlay_color = QColor(0, 0, 0, 180)  
            painter.fillRect(self.rect(), overlay_color)

            painter.setPen(QColor(0, 120, 255))  
            painter.setFont(QFont("Segoe UI", 48, QFont.Weight.Bold))
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "Game Over!")

            painter.setFont(QFont("Segoe UI", 20))
            painter.drawText(
                self.rect().adjusted(0, 100, 0, 0),
                Qt.AlignmentFlag.AlignCenter,
                "Press 'Restart' to play again",
            )

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Snake Game")
        self.setFixedSize(800, 600)
        self.setStyleSheet("background-color: rgba(10,10,20,1);")
        self.setWindowIcon(QIcon("assets/images/icon.ico"))

        self.stack = QStackedLayout(self)

        self.startup_music_player = QMediaPlayer(self)
        self.audio_output = QAudioOutput(self)
        self.startup_music_player.setAudioOutput(self.audio_output)

        startup_music_path = os.path.abspath("assets/sounds/startup.mp3")
        self.startup_music_player.setSource(QUrl.fromLocalFile(startup_music_path))
        self.startup_music_player.setLoops(QMediaPlayer.Loops.Infinite)
        self.startup_music_player.play()

        self.startup = StartupWidget(self.start_game)
        self.game = None

        self.stack.addWidget(self.startup)

    def start_game(self, level, player_speed, bot_speed):
        if self.startup_music_player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self.startup_music_player.stop()

        if self.game:
            self.stack.removeWidget(self.game)
            self.game.deleteLater()
            self.game = None

        self.game = GameWidget(level, player_speed, bot_speed)
        self.stack.addWidget(self.game)
        self.stack.setCurrentWidget(self.game)

    def go_home_from_game(self):
        if self.startup_music_player.playbackState() != QMediaPlayer.PlaybackState.PlayingState:
            self.startup_music_player.play()

        self.stack.setCurrentWidget(self.startup)

    def keyPressEvent(self, event):
        if self.game:
            self.game.keyPressEvent(event)

    def keyReleaseEvent(self, event):
        if self.game:
            self.game.keyReleaseEvent(event)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = MainWindow()
    win.show()
    sys.exit(app.exec())
