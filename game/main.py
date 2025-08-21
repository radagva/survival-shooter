import pygame
import math
import random
from enum import Enum


DISPLAY = WINX, WINY = 0, 0
BLACK = 0, 0, 0
FPS = 60

pygame.init()
clock = pygame.time.Clock()
surface = pygame.display.set_mode(DISPLAY, pygame.FULLSCREEN)
pygame.font.init()
font = pygame.font.SysFont("Arial", 24)


class EnemyType(Enum):
    BASIC = 1
    FAST = 2
    TANK = 3
    SHOOTER = 4
    ORBITER = 5
    BOSS = 6


class Player:
    def __init__(self, rect: pygame.Rect) -> None:
        self.speed = 5
        self.rect = rect
        self.health = 100
        self.score = 0

    def draw(self):
        pygame.draw.rect(surface, (255, 255, 255), self.rect)
        # Draw health bar
        pygame.draw.rect(
            surface, (255, 0, 0), (self.rect.x, self.rect.y - 10, self.rect.width, 5)
        )

        # draw health points
        fontTitle = pygame.font.SysFont("Arial", 10)
        textTitle = fontTitle.render(f"{self.health}", True, (0, 0, 0))
        rectTitle = textTitle.get_rect(center=self.rect.center)

        surface.blit(textTitle, rectTitle)

        pygame.draw.rect(
            surface,
            (0, 255, 0),
            (self.rect.x, self.rect.y - 10, self.rect.width * (self.health / 100), 5),
        )

    def _setup_movement(self):
        surfrect = surface.get_rect()
        keys = pygame.key.get_pressed()
        x = self.rect.x
        y = self.rect.y

        if keys[pygame.K_a]:
            x -= self.speed
        if keys[pygame.K_d]:
            x += self.speed
        if keys[pygame.K_w]:
            y -= self.speed
        if keys[pygame.K_s]:
            y += self.speed

        x = max(0, min(x, float(surfrect.w) - self.rect.w))
        y = max(0, min(y, float(surfrect.h) - self.rect.h))

        self.rect.x = int(x)
        self.rect.y = int(y)


class Aim:
    def __init__(self) -> None:
        self.rect = pygame.Rect((0, 0), (10, 10))

    def _setup_position(self, player: Player):
        x, y = pygame.mouse.get_pos()
        angleToMouse = math.atan2(
            y - (player.rect.y + player.rect.h / 2),
            x - (player.rect.x + player.rect.w / 2),
        )

        self.rect.x = int(
            player.rect.x
            + player.rect.w / 2
            + math.cos(angleToMouse) * 35
            - self.rect.w / 2
        )

        self.rect.y = int(
            player.rect.y
            + player.rect.h / 2
            + math.sin(angleToMouse) * 35
            - self.rect.h / 2
        )

    def draw(self):
        pygame.draw.rect(surface, (255, 0, 0), self.rect)


class Bullet:
    def __init__(self, start_pos: tuple[int, int], target_pos: tuple[int, int]) -> None:
        self.pos = pygame.Vector2(start_pos)
        self.target_pos = pygame.Vector2(target_pos)
        self.speed = 10
        self.rect = pygame.Rect((start_pos[0], start_pos[1]), (5, 5))
        self.damage = 25

        direction = self.target_pos - self.pos
        if direction.length() > 0:
            direction = direction.normalize()
        self.velocity = direction * self.speed

    def update(self):
        self.pos += self.velocity
        self.rect.x = int(self.pos.x)
        self.rect.y = int(self.pos.y)

    def draw(self):
        pygame.draw.rect(surface, (255, 0, 0), self.rect)


class EnemyBullet:
    def __init__(self, x: int, y: int, target_x: int, target_y: int, speed: int = 7):
        self.rect = pygame.Rect(x, y, 8, 8)
        self.speed = speed
        self.color = (255, 100, 100)  # Reddish color for enemy bullets
        self.damage = 10

        # Calculate direction
        dx = target_x - x
        dy = target_y - y
        distance = math.sqrt(dx * dx + dy * dy)

        if distance > 0:
            self.vx = (dx / distance) * self.speed
            self.vy = (dy / distance) * self.speed
        else:
            self.vx, self.vy = 0, 0

    def update(self):
        self.rect.x += int(self.vx)
        self.rect.y += int(self.vy)

    def draw(self, surface):
        pygame.draw.rect(surface, self.color, self.rect)


class Enemy:
    def __init__(self, x, y, enemy_type: EnemyType = EnemyType.BASIC):
        self.type = enemy_type
        size = 30

        # Set properties based on type
        if self.type == EnemyType.BASIC:
            self.color = (0, 255, 0)  # Green
            self.speed = 2
            self.health = 50
            size = 30
        elif self.type == EnemyType.FAST:
            self.color = (0, 200, 255)  # Light blue
            self.speed = 4
            self.health = 30
            size = 25
        elif self.type == EnemyType.TANK:
            self.color = (255, 100, 0)  # Orange
            self.speed = 1
            self.health = 150
            size = 40
        elif self.type == EnemyType.BOSS:
            self.color = (255, 0, 0)
            self.speed = 4
            self.health = 2000
            self.shoot_cooldown = 0
            self.shoot_interval = 800  # 0.8 seconds in ms

            size = 90
        elif self.type == EnemyType.SHOOTER:
            self.color = (150, 0, 150)  # Purple
            self.speed = 1.5
            self.health = 80
            size = 35
            self.shoot_cooldown = 0
            self.shoot_interval = 2000  # 2 seconds in ms
            self.min_distance = 250  # Stay at least this far from player

        self.rect = pygame.Rect(x, y, size, size)
        self.max_health = self.health
        self.hit_timer = 0

    def update(self, player_pos, dt, enemy_bullets: list[EnemyBullet]):
        px, py = player_pos

        if self.type == EnemyType.SHOOTER or self.type == EnemyType.BOSS:
            # Shooting logic
            self.shoot_cooldown -= dt
            if self.shoot_cooldown <= 0:  # and distance > 0
                enemy_bullets.append(
                    EnemyBullet(
                        self.rect.centerx,
                        self.rect.centery,
                        px,
                        py,
                        10 if self.type == EnemyType.BOSS else 5,
                    )
                )
                self.shoot_cooldown = self.shoot_interval

        if self.type == EnemyType.SHOOTER:
            if self.type == EnemyType.SHOOTER:
                # Ranged behavior
                dx = px - self.rect.x
                dy = py - self.rect.y
                distance = math.sqrt(dx * dx + dy * dy)

                # Maintain minimum distance
                if distance > 0:
                    if distance < self.min_distance:
                        # Move away from player
                        self.rect.x -= (dx / distance) * self.speed
                        self.rect.y -= (dy / distance) * self.speed
                    else:
                        # Move toward player but stop at min distance
                        self.rect.x += (dx / distance) * min(
                            self.speed, distance - self.min_distance
                        )
                        self.rect.y += (dy / distance) * min(
                            self.speed, distance - self.min_distance
                        )

        else:
            # Original movement logic for other enemies
            dx = px - self.rect.x
            dy = py - self.rect.y
            distance = math.sqrt(dx * dx + dy * dy)

            if distance > 0:
                dx = dx / distance
                dy = dy / distance

            self.rect.x += dx * self.speed
            self.rect.y += dy * self.speed

        # Update hit timer
        if self.hit_timer > 0:
            self.hit_timer -= 1

    def take_damage(self, amount):
        self.health -= amount
        self.hit_timer = 10  # Visual feedback duration
        return self.health <= 0

    def draw(self):
        # Flash white when hit
        color = (255, 255, 255) if self.hit_timer > 0 else self.color
        pygame.draw.rect(surface, color, self.rect)

        # Draw health bar
        bar_width = self.rect.width
        health_ratio = self.health / self.max_health
        pygame.draw.rect(
            surface, (255, 0, 0), (self.rect.x, self.rect.y - 8, bar_width, 3)
        )

        fontTitle = pygame.font.SysFont("Arial", 10)
        textTitle = fontTitle.render(f"{self.health}", True, (0, 0, 0))
        rectTitle = textTitle.get_rect(center=self.rect.center)

        surface.blit(textTitle, rectTitle)

        pygame.draw.rect(
            surface,
            (0, 255, 0),
            (self.rect.x, self.rect.y - 8, bar_width * health_ratio, 3),
        )


surfrect = surface.get_rect()
# Initialize game objects
player = Player(pygame.Rect((surfrect.w // 2, surfrect.h // 2), (20, 20)))
aim = Aim()
bullets: list[Bullet] = []
enemies: list[Enemy] = []
enemy_bullets: list[EnemyBullet] = []

player.draw()
aim._setup_position(player)

# Game state variables
enemy_spawn_timer = 0
enemy_spawn_interval = 1200  # 1.2 seconds
game_over = False
wave = 0
enemies_per_wave = 5
enemies_spawned = 0
boss_fight = False


def spawn_enemy():
    global enemies_spawned, boss_fight
    surfrect = surface.get_rect()

    # Randomly select enemy type with different probabilities
    rand = random.random()
    if rand < 0.5:  # 50% chance
        enemy_type = EnemyType.BASIC
    elif rand < 0.75:  # 25% chance
        enemy_type = EnemyType.FAST
    elif rand < 0.90:  # 15% chance
        enemy_type = EnemyType.TANK
    else:  # 10% chance
        enemy_type = EnemyType.SHOOTER

    # Spawn at random edge
    side = random.randint(0, 3)
    padding = 50

    if side == 0:  # Top
        x = random.randint(0, surfrect.w)
        y = -padding
    elif side == 1:  # Right
        x = surfrect.w + padding
        y = random.randint(0, surfrect.h)
    elif side == 2:  # Bottom
        x = random.randint(0, surfrect.w)
        y = surfrect.h + padding
    else:  # Left
        x = -padding
        y = random.randint(0, surfrect.h)

    enemies.append(Enemy(x, y, enemy_type))
    enemies_spawned += 1
    boss_fight = False


def spawn_boss():
    global enemies_spawned, boss_fight
    # Spawn at random edge
    side = random.randint(0, 3)
    surfrect = surface.get_rect()
    padding = 50

    if side == 0:  # Top
        x = random.randint(0, surfrect.w)
        y = -padding
    elif side == 1:  # Right
        x = surfrect.w + padding
        y = random.randint(0, surfrect.h)
    elif side == 2:  # Bottom
        x = random.randint(0, surfrect.w)
        y = surfrect.h + padding
    else:  # Left
        x = -padding
        y = random.randint(0, surfrect.h)

    enemies.append(Enemy(x, y, EnemyType.BOSS))
    enemies_spawned += 1
    boss_fight = True


def check_collisions():
    # Bullet-enemy collisions
    for bullet in bullets[:]:
        for enemy in enemies[:]:
            if bullet.rect.colliderect(enemy.rect):
                if enemy.take_damage(bullet.damage):
                    player.score += (
                        enemy.type.value * 10
                    )  # More points for stronger enemies
                    enemies.remove(enemy)
                bullets.remove(bullet)
                break

    # Player-enemy collisions
    for enemy in enemies[:]:
        if player.rect.colliderect(enemy.rect):
            player.health -= 1
            if player.health <= 0:
                return True
    return False


def show_paused():
    pause_text = font.render("Paused, press p to resume", True, (255, 255, 255))
    surface.blit(pause_text, (surfrect.w // 2 - 150, surfrect.h // 2))


def draw_score():
    score_text = font.render(f"Score: {player.score}", True, (255, 255, 255))
    wave_text = font.render(f"Wave: {wave}", True, (255, 255, 255))
    surface.blit(score_text, (10, 10))
    surface.blit(wave_text, (10, 40))


# Main game loop
running = True
paused = True

show_paused()
draw_score()

while running:
    surfrect = surface.get_rect()

    dt = clock.tick(FPS)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif (
            event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and not game_over
        ):
            if not paused:
                mouse_pos = pygame.mouse.get_pos()
                start_pos = (aim.rect.x + aim.rect.w // 2, aim.rect.y + aim.rect.h // 2)
                bullets.append(Bullet(start_pos, mouse_pos))
        elif event.type == pygame.KEYDOWN and event.key == pygame.K_p and not game_over:
            show_paused()
            paused = not paused
        elif event.type == pygame.KEYDOWN and game_over:
            if event.key == pygame.K_r:
                # Reset game
                player = Player(
                    pygame.Rect((surfrect.w // 2, surfrect.h // 2), (20, 20))
                )
                bullets = []
                enemies = []
                enemy_spawn_timer = 0
                game_over = False
                wave = 1
                boss_fight = False
                enemies_spawned = 0

    if not paused:
        surface.fill(BLACK)

    if not game_over:
        # Enemy spawning
        if wave > 0 and wave % 5 == 0:
            if not boss_fight:
                spawn_boss()
        elif enemies_spawned < wave * enemies_per_wave:
            enemy_spawn_timer += dt
            if enemy_spawn_timer >= enemy_spawn_interval:
                spawn_enemy()
                enemy_spawn_timer = 0

        # Start next wave if all enemies are defeated
        if (
            enemies_spawned >= wave * enemies_per_wave
            and len(enemies) == 0
            or boss_fight
            and len(enemies) == 0
        ):
            boss_fight = False
            wave += 1
            enemy_spawn_timer = 0
            enemies_spawned = 0
            enemy_spawn_interval = max(
                500, enemy_spawn_interval - 100
            )  # Faster spawns each wave
            player.health += 10 if player.health <= 90 else 100 - player.health

        # Drawing
        if not paused:
            # Update player and aim
            player._setup_movement()
            aim._setup_position(player)

            # Check collisions
            game_over = check_collisions()

    # Draw bullets
    for bullet in bullets[:]:
        if not paused:
            bullet.update()

        bullet.draw()
        if (
            bullet.rect.x < -50
            or bullet.rect.x > surfrect.w + 50
            or bullet.rect.y < -50
            or bullet.rect.y > surfrect.h + 50
        ):
            bullets.remove(bullet)

    # Draw enemies
    for enemy in enemies:
        if not paused:
            enemy.update((player.rect.x, player.rect.y), dt, enemy_bullets)
        enemy.draw()

    # Update enemy bullets
    for bullet in enemy_bullets[:]:
        if not paused:
            bullet.update()
        # Remove off-screen bullets
        if (
            bullet.rect.x < -50
            or bullet.rect.x > surfrect.w + 50
            or bullet.rect.y < -50
            or bullet.rect.y > surfrect.h + 50
        ):
            enemy_bullets.remove(bullet)
        # Check player collision
        elif bullet.rect.colliderect(player.rect):
            player.health -= bullet.damage
            enemy_bullets.remove(bullet)

    # In your drawing code:
    for bullet in enemy_bullets:
        bullet.draw(surface)

    # Draw player and aim
    if not game_over:
        player.draw()
        aim.draw()

    # Draw UI
    if not paused:
        draw_score()

    if game_over:
        game_over_text = font.render(
            "GAME OVER - Press R to Restart", True, (255, 0, 0)
        )
        surface.blit(game_over_text, (surfrect.w // 2 - 150, surfrect.h // 2))

    pygame.display.flip()

pygame.quit()
