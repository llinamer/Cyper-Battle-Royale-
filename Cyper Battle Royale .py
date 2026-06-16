import pygame
import sys
import math
import random
import webbrowser  # Módulo para abrir el enlace sin cerrar el juego

# Inicializar Pygame
pygame.init()

# Configuración de PANTALLA COMPLETA
screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
WIDTH, HEIGHT = screen.get_size()
pygame.display.set_caption("CRT Cyber Battle Royale - DEV PRO UPDATE")

# Ocultar el cursor del mouse para usar nuestra propia retícula de radar
pygame.mouse.set_visible(False)

# Paleta de colores fósforo CRT
BG_COLOR = (5, 15, 5)
CRT_GREEN = (0, 255, 64)
CRT_GLOW = (0, 80, 20)
TEXT_COLOR = (150, 255, 150)
PLAYER_COLOR = (100, 255, 255)
BOSS_COLOR = (255, 0, 90)

# Tipografías
font_title = pygame.font.SysFont("Courier", 60, bold=True)
font_menu = pygame.font.SysFont("Courier", 35, bold=True)
font_interface = pygame.font.SysFont("Courier", 20)
font_win = pygame.font.SysFont("Courier", 90, bold=True)

# Variables globales del juego
missiles = []
state = "MENU"  # Estados: "MENU", "CONFIG", "GAME"
bot_difficulty = "MEDIO"  # "FACIL", "MEDIO", "DIFICIL", "BOSS FINAL"

# Variables para alertas temporales de fase y desarrollador
phase_msg_text = ""
phase_msg_timer = 0
dev_msg_text = ""
dev_msg_timer = 0

# --- NUEVAS VARIABLES PARA EL SISTEMA DE HABILIDADES ---
current_ability = None        # Almacena la habilidad tirada en el mapa: {"type":..., "pos":..., "spawn_time":...}
ability_next_spawn_time = 0   # Timestamp del próximo spawn
player_active_ability = None  # Habilidad que tiene el jugador activa
player_ability_expiry = 0     # Cuándo termina el efecto del jugador

# --- MAPA REESTRUCTURADO Y AMPLIADO ---
walls = [
    # Pilar central divisor
    pygame.Rect(int(WIDTH * 0.46), int(HEIGHT * 0.45), int(WIDTH * 0.08), int(HEIGHT * 0.25)),
    # Coberturas bajas (Izquierda y Derecha)
    pygame.Rect(int(WIDTH * 0.25), int(HEIGHT * 0.7), int(WIDTH * 0.08), int(HEIGHT * 0.04)),
    # Coberturas altas flotantes
    pygame.Rect(int(WIDTH * 0.15), int(HEIGHT * 0.35), int(WIDTH * 0.12), int(HEIGHT * 0.03)),
    pygame.Rect(int(WIDTH * 0.73), int(HEIGHT * 0.35), int(WIDTH * 0.12), int(HEIGHT * 0.03)),
    # Columnas de contención perimetral
    pygame.Rect(int(WIDTH * 0.06), int(HEIGHT * 0.45), int(WIDTH * 0.02), int(HEIGHT * 0.2)),
    pygame.Rect(int(WIDTH * 0.92), int(HEIGHT * 0.45), int(WIDTH * 0.02), int(HEIGHT * 0.2)),
    # Escudos de techo centrales
    pygame.Rect(int(WIDTH * 0.38), int(HEIGHT * 0.18), int(WIDTH * 0.06), int(HEIGHT * 0.03)),
    pygame.Rect(int(WIDTH * 0.56), int(HEIGHT * 0.18), int(WIDTH * 0.06), int(HEIGHT * 0.03)),

    # NUEVAS PAREDES CORREGIDAS
    pygame.Rect(int(WIDTH * 0.08), int(HEIGHT * 0.15), int(WIDTH * 0.08), int(HEIGHT * 0.03)),
    pygame.Rect(int(WIDTH * 0.84), int(HEIGHT * 0.15), int(WIDTH * 0.08), int(HEIGHT * 0.03)),
    # Columnas verticales desplazadas
    pygame.Rect(int(WIDTH * 0.22), int(HEIGHT * 0.48), int(WIDTH * 0.015), int(HEIGHT * 0.15)),
    pygame.Rect(int(WIDTH * 0.74), int(HEIGHT * 0.48), int(WIDTH * 0.015), int(HEIGHT * 0.15)),
    # Bloque de trinchera inferior central
    pygame.Rect(int(WIDTH * 0.44), int(HEIGHT * 0.82), int(WIDTH * 0.12), int(HEIGHT * 0.02)),
    # Micro-barreras laterales extra
    pygame.Rect(int(WIDTH * 0.05), int(HEIGHT * 0.68), int(WIDTH * 0.05), int(HEIGHT * 0.02)),
    pygame.Rect(int(WIDTH * 0.90), int(HEIGHT * 0.68), int(WIDTH * 0.05), int(HEIGHT * 0.02))
]

# Escudo extra frente al Boss si estamos en su modo
boss_shield = pygame.Rect(int(WIDTH * 0.65), int(HEIGHT * 0.68), int(WIDTH * 0.08), int(HEIGHT * 0.04))

def check_wall_collision(rect):
    return rect.collidelist(walls) != -1

def create_entities():
    if bot_difficulty == "BOSS FINAL" and boss_shield not in walls:
        walls.append(boss_shield)
    elif bot_difficulty != "BOSS FINAL" and boss_shield in walls:
        walls.remove(boss_shield)

    player = {
        "name": "JUGADOR (TU)",
        "pos": [int(WIDTH * 0.12), int(HEIGHT * 0.8)],
        "alive": True, "color": PLAYER_COLOR, "cooldown": 0, "radius": 14
    }

    bots = []
    cooldown_range = (70, 150)
    error_margin = 15

    if bot_difficulty == "BOSS FINAL":
        bots.append({
            "id": 99, "name": "MÁSTER BOSS FINAL", "pos": [int(WIDTH * 0.82), int(HEIGHT * 0.55)],
            "target_pos": [int(WIDTH * 0.82), int(HEIGHT * 0.55)], "alive": True,
            "cooldown": 60, "color": BOSS_COLOR, "speed": 2.5, "radius": 32,
            "is_boss": True, "hp": 50, "max_hp": 50, "hits_taken": 0, "burst_count": 0,
            "phase": 1
        })
        bots.append({
            "id": 1, "name": "ESCOLTA MINION A", "pos": [int(WIDTH * 0.68), int(HEIGHT * 0.82)],
            "target_pos": [int(WIDTH * 0.68), int(HEIGHT * 0.82)], "alive": True,
            "cooldown": 90, "color": (180, 180, 180), "speed": 3.0, "radius": 10
        })
        bots.append({
            "id": 2, "name": "ESCOLTA MINION B", "pos": [int(WIDTH * 0.88), int(HEIGHT * 0.82)],
            "target_pos": [int(WIDTH * 0.88), int(HEIGHT * 0.82)], "alive": True,
            "cooldown": 110, "color": (180, 180, 180), "speed": 3.0, "radius": 10
        })
    else:
        if bot_difficulty == "FACIL":
            speed_mult, cooldown_range, error_margin = 1.5, (120, 240), 25
        elif bot_difficulty == "MEDIO":
            speed_mult, cooldown_range, error_margin = 3.0, (70, 150), 15
        else:
            speed_mult, cooldown_range, error_margin = 5.0, (40, 90), 4

        bots = [
            {"id": 1, "name": "BOT ALFA", "pos": [int(WIDTH * 0.35), int(HEIGHT * 0.82)], "target_pos": [int(WIDTH * 0.35), int(HEIGHT * 0.82)], "alive": True, "cooldown": random.randint(cooldown_range[0], cooldown_range[1]), "color": (0, 255, 100), "speed": speed_mult, "radius": 12},
            {"id": 2, "name": "BOT BRAVO", "pos": [int(WIDTH * 0.32), int(HEIGHT * 0.52)], "target_pos": [int(WIDTH * 0.32), int(HEIGHT * 0.52)], "alive": True, "cooldown": random.randint(cooldown_range[0], cooldown_range[1]), "color": (255, 200, 0), "speed": speed_mult * 1.1, "radius": 12},
            {"id": 3, "name": "BOT CHARLIE", "pos": [int(WIDTH * 0.65), int(HEIGHT * 0.52)], "target_pos": [int(WIDTH * 0.65), int(HEIGHT * 0.52)], "alive": True, "cooldown": random.randint(cooldown_range[0], cooldown_range[1]), "color": (255, 100, 100), "speed": speed_mult * 0.8, "radius": 12},
            {"id": 4, "name": "BOT DELTA", "pos": [int(WIDTH * 0.88), int(HEIGHT * 0.82)], "target_pos": [int(WIDTH * 0.88), int(HEIGHT * 0.82)], "alive": True, "cooldown": random.randint(cooldown_range[0], cooldown_range[1]), "color": (200, 100, 255), "speed": speed_mult * 1.3, "radius": 12}
        ]

    return player, bots, cooldown_range, error_margin

player, bots, cooldown_range, error_margin = create_entities()
clock = pygame.time.Clock()
game_over = False
win_pulse = 0

# Distribución de botones del menú de inicio
play_btn_rect = pygame.Rect((WIDTH // 2) - 200, (HEIGHT // 2) - 80, 400, 50)
config_btn_rect = pygame.Rect((WIDTH // 2) - 200, (HEIGHT // 2) - 10, 400, 50)
dev_btn_rect = pygame.Rect((WIDTH // 2) - 200, (HEIGHT // 2) + 60, 400, 50)

# Botones del selector de dificultad
easy_btn_rect = pygame.Rect((WIDTH // 2) - 150, (HEIGHT // 2) - 100, 300, 45)
medium_btn_rect = pygame.Rect((WIDTH // 2) - 150, (HEIGHT // 2) - 40, 300, 45)
hard_btn_rect = pygame.Rect((WIDTH // 2) - 150, (HEIGHT // 2) + 20, 300, 45)
boss_btn_rect = pygame.Rect((WIDTH // 2) - 150, (HEIGHT // 2) + 80, 300, 45)

# Bucle principal
running = True
while running:
    screen.fill(BG_COLOR)
    mouse_pos = pygame.mouse.get_pos()
    now_time = pygame.time.get_ticks()

    # Malla CRT de fondo
    for x in range(0, WIDTH, 50):
        pygame.draw.line(screen, (10, 25, 10), (x, 0), (x, HEIGHT), 1)
    for y in range(0, HEIGHT, 50):
        pygame.draw.line(screen, (10, 25, 10), (0, y), (WIDTH, y), 1)

    # ==================== ESTADO: MENÚ DE INICIO ====================
    if state == "MENU":
        for event in pygame.event.get():
            if event.type == pygame.QUIT: running = False
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE: running = False
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if play_btn_rect.collidepoint(mouse_pos):
                    player, bots, cooldown_range, error_margin = create_entities()
                    missiles.clear()
                    game_over = False
                    phase_msg_text = ""
                    phase_msg_timer = 0
                    # Reset de habilidades al empezar partida
                    current_ability = None
                    player_active_ability = None
                    ability_next_spawn_time = pygame.time.get_ticks() + 15000 # Primera habilidad a los 15s para probar rápido
                    state = "GAME"
                elif config_btn_rect.collidepoint(mouse_pos):
                    state = "CONFIG"
                elif dev_btn_rect.collidepoint(mouse_pos):
                    webbrowser.open("https://github.com/llinamer")
                    dev_msg_text = "Enlace abierto en su navegador web"
                    dev_msg_timer = pygame.time.get_ticks() + 3000

        title_text = font_title.render("CRT CYBER BATTLE ROYALE", True, CRT_GREEN)
        screen.blit(title_text, title_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 180)))

        # Render: JUGAR
        h_play = play_btn_rect.collidepoint(mouse_pos)
        pygame.draw.rect(screen, (0, 40, 15) if h_play else BG_COLOR, play_btn_rect)
        pygame.draw.rect(screen, PLAYER_COLOR if h_play else CRT_GREEN, play_btn_rect, 2)
        t_play = font_menu.render("JUGAR", True, PLAYER_COLOR if h_play else CRT_GREEN)
        screen.blit(t_play, t_play.get_rect(center=play_btn_rect.center))

        # Render: NIVEL BOTS
        h_config = config_btn_rect.collidepoint(mouse_pos)
        pygame.draw.rect(screen, (0, 40, 15) if h_config else BG_COLOR, config_btn_rect)
        pygame.draw.rect(screen, PLAYER_COLOR if h_config else CRT_GREEN, config_btn_rect, 2)
        t_config = font_menu.render("NIVEL BOTS", True, PLAYER_COLOR if h_config else CRT_GREEN)
        screen.blit(t_config, t_config.get_rect(center=config_btn_rect.center))

        # Render: DESARROLLADOR
        h_dev = dev_btn_rect.collidepoint(mouse_pos)
        pygame.draw.rect(screen, (0, 40, 15) if h_dev else BG_COLOR, dev_btn_rect)
        pygame.draw.rect(screen, PLAYER_COLOR if h_dev else CRT_GREEN, dev_btn_rect, 2)
        t_dev = font_menu.render("DESARROLLADOR", True, PLAYER_COLOR if h_dev else CRT_GREEN)
        screen.blit(t_dev, t_dev.get_rect(center=dev_btn_rect.center))

        # Texto de aviso de enlace abierto
        if dev_msg_text and pygame.time.get_ticks() < dev_msg_timer:
            d_surf = font_interface.render(dev_msg_text, True, PLAYER_COLOR)
            screen.blit(d_surf, d_surf.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 140)))

        info = font_interface.render(f"[ESC] Apagar terminal  |  Modo cargado: {bot_difficulty}", True, TEXT_COLOR)
        screen.blit(info, info.get_rect(center=(WIDTH // 2, HEIGHT - 50)))

    # ==================== ESTADO: CONFIGURACIÓN DE NIVEL BOTS ====================
    elif state == "CONFIG":
        for event in pygame.event.get():
            if event.type == pygame.QUIT: running = False
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE: state = "MENU"
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if easy_btn_rect.collidepoint(mouse_pos): bot_difficulty = "FACIL"
                elif medium_btn_rect.collidepoint(mouse_pos): bot_difficulty = "MEDIO"
                elif hard_btn_rect.collidepoint(mouse_pos): bot_difficulty = "DIFICIL"
                elif boss_btn_rect.collidepoint(mouse_pos): bot_difficulty = "BOSS FINAL"

        c_title = font_title.render("SELECCIONAR NIVEL BOTS", True, CRT_GREEN)
        screen.blit(c_title, c_title.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 180)))

        for rect, diff_name in [(easy_btn_rect, "FACIL"), (medium_btn_rect, "MEDIO"), (hard_btn_rect, "DIFICIL"), (boss_btn_rect, "BOSS FINAL")]:
            hover = rect.collidepoint(mouse_pos)
            selected = bot_difficulty == diff_name
            color = BOSS_COLOR if diff_name == "BOSS FINAL" else CRT_GREEN
            pygame.draw.rect(screen, (0, 50, 30) if selected else ((0, 30, 10) if hover else BG_COLOR), rect)
            pygame.draw.rect(screen, PLAYER_COLOR if (hover or selected) else color, rect, 2 if not selected else 3)
            txt = font_menu.render(diff_name + (" <" if selected else ""), True, PLAYER_COLOR if selected else (TEXT_COLOR if hover else color))
            screen.blit(txt, txt.get_rect(center=rect.center))

        back_info = font_interface.render("[ESC] Volver al Menú Principal", True, TEXT_COLOR)
        screen.blit(back_info, back_info.get_rect(center=(WIDTH // 2, HEIGHT - 50)))

    # ==================== ESTADO: EN PARTIDA ====================
    elif state == "GAME":
        for event in pygame.event.get():
            if event.type == pygame.QUIT: running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE: state = "MENU"
                if event.key == pygame.K_r:
                    player, bots, cooldown_range, error_margin = create_entities()
                    missiles.clear()
                    game_over = False
                    phase_msg_text = ""
                    phase_msg_timer = 0
                    # Reset de habilidades al reiniciar
                    current_ability = None
                    player_active_ability = None
                    ability_next_spawn_time = pygame.time.get_ticks() + 15000

        if not game_over:
            # --- CONDICIONES DE FIN DE PARTIDA ---
            boss_alive = any(b.get("is_boss") and b["alive"] for b in bots)

            if not player["alive"]:
                game_over = True
            elif bot_difficulty == "BOSS FINAL" and not boss_alive:
                game_over = True
            elif bot_difficulty != "BOSS FINAL":
                total_alive = (1 if player["alive"] else 0) + sum(1 for b in bots if b["alive"])
                if total_alive <= 1:
                    game_over = True

            # ==================== GESTIÓN DE HABILIDADES (SOLO BOSS FINAL) ====================
            if bot_difficulty == "BOSS FINAL":
                # 1. Spawnear cada 30 segundos si no hay una activa en el suelo
                if now_time >= ability_next_spawn_time and current_ability is None:
                    safe_ab_spawn = False
                    ab_x, ab_y = 0, 0
                    # Bucle anti-paredes estricto
                    while not safe_ab_spawn:
                        ab_x = random.randint(int(WIDTH * 0.15), int(WIDTH * 0.85))
                        ab_y = random.randint(int(HEIGHT * 0.35), int(HEIGHT * 0.8))
                        # Caja de testeo del ítem
                        if not check_wall_collision(pygame.Rect(ab_x - 15, ab_y - 15, 30, 30)):
                            safe_ab_spawn = True

                    chosen_type = random.choice(["RAFAGA", "INMORTALIDAD", "DISPARAR AUTO"])
                    current_ability = {"type": chosen_type, "pos": [ab_x, ab_y], "spawn_time": now_time}
                    ability_next_spawn_time = now_time + 30000 # Planificar siguiente en 30s

                # 2. Despawnear a los 10 segundos si no se recoge
                if current_ability and now_time >= current_ability["spawn_time"] + 10000:
                    current_ability = None

                # 3. Comprobar si el jugador la recoge
                if current_ability and player["alive"]:
                    p_dist = math.hypot(player["pos"][0] - current_ability["pos"][0], player["pos"][1] - current_ability["pos"][1])
                    if p_dist < (player["radius"] + 15):
                        player_active_ability = current_ability["type"]
                        player_ability_expiry = now_time + 5000 # Dura 5 segundos
                        current_ability = None

                # 4. Apagar habilidad del jugador si expira su tiempo
                if player_active_ability and now_time >= player_ability_expiry:
                    player_active_ability = None

            # --- MOVIMIENTO JUGADOR ---
            if player["alive"]:
                keys = pygame.key.get_pressed()
                mx, my = 0, 0
                if keys[pygame.K_a]: mx = -5
                if keys[pygame.K_d]: mx = 5
                if keys[pygame.K_w]: my = -5
                if keys[pygame.K_s]: my = 5

                player["pos"][0] += mx
                player["pos"][0] = max(20, min(WIDTH - 20, player["pos"][0]))
                if check_wall_collision(pygame.Rect(player["pos"][0]-player["radius"], player["pos"][1]-player["radius"], player["radius"]*2, player["radius"]*2)):
                    player["pos"][0] -= mx

                player["pos"][1] += my
                player["pos"][1] = max(20, min(HEIGHT - 50, player["pos"][1]))
                if check_wall_collision(pygame.Rect(player["pos"][0]-player["radius"], player["pos"][1]-player["radius"], player["radius"]*2, player["radius"]*2)):
                    player["pos"][1] -= my

                if player["cooldown"] > 0: player["cooldown"] -= 1

                # --- SISTEMA DE DISPARO (MANUAL / RÁFAGA / AUTO-SHOOT) ---
                # Habilidad DISPARAR AUTO: Dispara solo si el cooldown está listo
                auto_shoot_trigger = (player_active_ability == "DISPARAR AUTO" and player["cooldown"] == 0)
                manual_shoot_trigger = (pygame.mouse.get_pressed()[0] and player["cooldown"] == 0)

                if manual_shoot_trigger or auto_shoot_trigger:
                    dx, dy = mouse_pos[0] - player["pos"][0], mouse_pos[1] - player["pos"][1]
                    dist = math.hypot(dx, dy)
                    if dist > 0:
                        # Si tiene RÁFAGA, dispara 3 proyectiles dispersos
                        if player_active_ability == "RAFAGA":
                            base_angle = math.atan2(dy, dx)
                            for offset in [-0.12, 0, 0.12]:
                                vx = 18.0 * math.cos(base_angle + offset)
                                vy = 18.0 * math.sin(base_angle + offset)
                                missiles.append({"pos": [float(player["pos"][0]), float(player["pos"][1])], "vel": [vx, vy], "owner_id": 0, "trail": []})
                            player["cooldown"] = 12 # Cooldown ligeramente más rápido para la ráfaga
                        else:
                            # Disparo estándar (O auto-shoot estándar)
                            missiles.append({"pos": [float(player["pos"][0]), float(player["pos"][1])], "vel": [(dx/dist)*18.0, (dy/dist)*18.0], "owner_id": 0, "trail": []})
                            player["cooldown"] = 18

            # --- IA: ENRUTAMIENTO Y MOVIMIENTO ---
            for bot in bots:
                if not bot["alive"]: continue

                current_speed = bot["speed"]
                current_error = error_margin
                is_boss = bot.get("is_boss", False)
                phase = bot.get("phase", 1)

                if is_boss:
                    if phase == 1:   current_speed = 2.5
                    elif phase == 2: current_speed = 3.0
                    elif phase == 3: current_error = 7.5; current_speed = 3.7
                    elif phase == 4: current_error = 4.0; current_speed = 4.5
                    bot["speed"] = current_speed

                if random.random() < 0.015:
                    bot["target_pos"] = [random.randint(int(WIDTH*0.1), int(WIDTH*0.9)), random.randint(int(HEIGHT*0.35), int(HEIGHT*0.85))]

                bdx, bdy = bot["target_pos"][0] - bot["pos"][0], bot["target_pos"][1] - bot["pos"][1]
                b_dist = math.hypot(bdx, bdy)

                if b_dist > 5:
                    sx, sy = (bdx/b_dist)*current_speed, (bdy/b_dist)*current_speed

                    bot["pos"][0] += sx
                    if check_wall_collision(pygame.Rect(bot["pos"][0]-bot["radius"], bot["pos"][1]-bot["radius"], bot["radius"]*2, bot["radius"]*2)):
                        bot["pos"][0] -= sx
                        bot["target_pos"] = [random.randint(int(WIDTH*0.1), int(WIDTH*0.9)), random.randint(int(HEIGHT*0.35), int(HEIGHT*0.85))]

                    bot["pos"][1] += sy
                    if check_wall_collision(pygame.Rect(bot["pos"][0]-bot["radius"], bot["pos"][1]-bot["radius"], bot["radius"]*2, bot["radius"]*2)):
                        bot["pos"][1] -= sy
                        bot["target_pos"] = [random.randint(int(WIDTH*0.1), int(WIDTH*0.9)), random.randint(int(HEIGHT*0.35), int(HEIGHT*0.85))]

                # Disparos de los bots
                if bot["cooldown"] > 0:
                    bot["cooldown"] -= 1
                else:
                    if bot_difficulty == "BOSS FINAL":
                        targets = [player] if player["alive"] else []
                    else:
                        targets = [player] if player["alive"] else []
                        targets += [b for b in bots if b["alive"] and b["id"] != bot["id"]]

                    if targets:
                        victim = random.choice(targets)
                        v_dx, v_dy = victim["pos"][0] - bot["pos"][0], victim["pos"][1] - bot["pos"][1]
                        ang = math.atan2(-v_dy, v_dx) + math.radians(random.uniform(-current_error, current_error))
                        pwr = (math.hypot(v_dx, v_dy) * 0.012) + random.uniform(8, 13)

                        def fire(offset=0.0):
                            vx = pwr * math.cos(ang + offset)
                            vy = -pwr * math.sin(ang + offset)
                            missiles.append({"pos": [float(bot["pos"][0]), float(bot["pos"][1])], "vel": [vx, vy], "owner_id": bot["id"], "trail": []})

                        if not is_boss:
                            fire()
                            bot["cooldown"] = random.randint(cooldown_range[0], cooldown_range[1])
                        else:
                            if phase == 1:
                                fire()
                                bot["cooldown"] = random.randint(50, 90)
                            elif phase == 2 or phase == 3:
                                fire(-0.15)
                                fire(0)
                                fire(0.15)
                                bot["cooldown"] = random.randint(60, 100)
                            elif phase == 4:
                                fire()
                                bot["burst_count"] += 1
                                if bot["burst_count"] < 4:
                                    bot["cooldown"] = 7
                                else:
                                    bot["burst_count"] = 0
                                    bot["cooldown"] = random.randint(45, 75)

            # --- PROYECTILES Y COLISIONES ---
            for m in missiles[:]:
                m["pos"][0] += m["vel"][0]
                m["pos"][1] += m["vel"][1]
                m["vel"][1] += 0.15
                m["trail"].append(list(m["pos"]))
                if len(m["trail"]) > 8: m["trail"].pop(0)

                hit = False
                if check_wall_collision(pygame.Rect(int(m["pos"][0])-3, int(m["pos"][1])-3, 6, 6)):
                    hit = True

                if not hit and player["alive"] and m["owner_id"] != 0:
                    if math.hypot(m["pos"][0]-player["pos"][0], m["pos"][1]-player["pos"][1]) < 20:
                        # Habilidad INMORTALIDAD evita que mueras
                        if player_active_ability == "INMORTALIDAD":
                            hit = True # La bala estalla en tu escudo
                        else:
                            player["alive"] = False
                            hit = True

                if not hit:
                    for bot in bots:
                        if bot["alive"] and bot["id"] != m["owner_id"]:
                            if bot_difficulty == "BOSS FINAL" and m["owner_id"] != 0:
                                continue

                            if math.hypot(m["pos"][0] - bot["pos"][0], m["pos"][1] - bot["pos"][1]) < (bot["radius"] + 5):
                                hit = True
                                if bot.get("is_boss", False):
                                    bot["hits_taken"] += 1
                                    bot["hp"] -= 1

                                    hits = bot["hits_taken"]
                                    new_phase = 1
                                    if hits <= 15:    new_phase = 1
                                    elif hits <= 30:  new_phase = 2
                                    elif hits <= 45:  new_phase = 3
                                    else:             new_phase = 4

                                    if new_phase > bot["phase"]:
                                        bot["phase"] = new_phase
                                        phase_msg_text = f"EL JEFE HA CAMBIADO DE FASE A LA FASE {new_phase}"
                                        phase_msg_timer = pygame.time.get_ticks() + 3000

                                        # REFUERZOS CON SPAWN SEGURO EVITA-PAREDES
                                        for i in range(2):
                                            r_id = random.randint(100 + new_phase*10, 999)
                                            r_radius = 10

                                            safe_spawn = False
                                            spawn_x, spawn_y = 0, 0
                                            while not safe_spawn:
                                                spawn_x = random.randint(int(WIDTH * 0.65), int(WIDTH * 0.9))
                                                spawn_y = random.randint(int(HEIGHT * 0.35), int(HEIGHT * 0.85))
                                                test_rect = pygame.Rect(spawn_x - r_radius, spawn_y - r_radius, r_radius * 2, r_radius * 2)
                                                if not check_wall_collision(test_rect):
                                                    safe_spawn = True

                                            bots.append({
                                                "id": r_id, "name": f"REFUERZO F{new_phase}-{i+1}",
                                                "pos": [spawn_x, spawn_y],
                                                "target_pos": [random.randint(50, WIDTH-50), random.randint(int(HEIGHT*0.4), HEIGHT-60)],
                                                "alive": True, "cooldown": random.randint(60, 120), "color": (180, 180, 180), "speed": 3.2, "radius": r_radius
                                            })

                                    if bot["hp"] <= 0: bot["alive"] = False
                                else:
                                    bot["alive"] = False
                                break

                if hit or m["pos"][0] < 0 or m["pos"][0] > WIDTH or m["pos"][1] > HEIGHT:
                    missiles.remove(m)

        # --- DIBUJADO DE ENTIDADES Y ESCENARIO ---
        for wall in walls:
            pygame.draw.rect(screen, (0, 35, 12), wall)
            pygame.draw.rect(screen, CRT_GREEN, wall, 2)

        # Renderizar Habilidad tirada en el mapa (Si existe)
        if bot_difficulty == "BOSS FINAL" and current_ability:
            ax, ay = current_ability["pos"]
            # Efecto matriz parpadeante/esfera
            pulse_r = 14 + int(math.sin(now_time * 0.01) * 3)
            pygame.draw.circle(screen, (255, 200, 0), (ax, ay), pulse_r, 1)
            pygame.draw.circle(screen, PLAYER_COLOR, (ax, ay), 9)
            # Inicial de la habilidad dentro del ítem
            letter = current_ability["type"][0]
            letter_s = font_interface.render(letter, True, BG_COLOR)
            screen.blit(letter_s, letter_s.get_rect(center=(ax, ay)))

        if player["alive"]:
            # Si el jugador es inmortal, dibujamos un escudo extra cian a su alrededor
            if player_active_ability == "INMORTALIDAD":
                pygame.draw.circle(screen, PLAYER_COLOR, (int(player["pos"][0]), int(player["pos"][1])), 26, 2)

            pygame.draw.circle(screen, CRT_GLOW, (int(player["pos"][0]), int(player["pos"][1])), 22)
            pygame.draw.circle(screen, player["color"], (int(player["pos"][0]), int(player["pos"][1])), 14, 4)
            screen.blit(font_interface.render(player["name"], True, player["color"]), (player["pos"][0]-55, player["pos"][1]-40))

        for bot in bots:
            if bot["alive"]:
                pygame.draw.circle(screen, CRT_GLOW, (int(bot["pos"][0]), int(bot["pos"][1])), bot["radius"]+6)
                pygame.draw.circle(screen, bot["color"], (int(bot["pos"][0]), int(bot["pos"][1])), bot["radius"], 3 if bot.get("is_boss") else 2)
                screen.blit(font_interface.render(bot["name"], True, bot["color"]), (bot["pos"][0]-40, bot["pos"][1] + bot["radius"] + 10))

                if bot.get("is_boss"):
                    hp_ratio = bot["hp"] / bot["max_hp"]
                    fase_id = bot["phase"]

                    bar_w, bar_h = 400, 25
                    bx, by = (WIDTH // 2) - (bar_w // 2), 30
                    pygame.draw.rect(screen, (30, 0, 10), (bx, by, bar_w, bar_h))
                    pygame.draw.rect(screen, BOSS_COLOR, (bx, by, int(bar_w * hp_ratio), bar_h))
                    pygame.draw.rect(screen, CRT_GREEN, (bx, by, bar_w, bar_h), 2)

                    hp_txt = font_interface.render(f"BOSS CORE HP: {bot['hp']}/50  |  FASE: {fase_id}", True, TEXT_COLOR)
                    screen.blit(hp_txt, (bx, by + 30))

        for m in missiles:
            for i, pos in enumerate(m["trail"]): pygame.draw.circle(screen, CRT_GLOW, (int(pos[0]), int(pos[1])), 2 + i // 2)
            pygame.draw.circle(screen, CRT_GREEN, (int(m["pos"][0]), int(m["pos"][1])), 5)

        screen.blit(font_interface.render(f"[WASD] Moverse | [Click Izq] Fuego | Modo: {bot_difficulty} | [ESC] Volver", True, TEXT_COLOR), (30, HEIGHT - 40))

        # --- INTERFAZ: MOSTRAR HABILIDAD ADQUIRIDA ABAJO A LA DERECHA ---
        if bot_difficulty == "BOSS FINAL" and player_active_ability:
            time_left = max(0.0, (player_ability_expiry - now_time) / 1000.0)
            # Texto estilizado terminal retro
            ability_text = f"SISTEMA CARGADO: {player_active_ability} ({time_left:.1f}s)"
            ability_surf = font_menu.render(ability_text, True, PLAYER_COLOR)
            ability_rect = ability_surf.get_rect(bottomright=(WIDTH - 40, HEIGHT - 40))

            # Sombra de fósforo quemado (Glow)
            screen.blit(font_menu.render(ability_text, True, CRT_GLOW), (ability_rect.x + 2, ability_rect.y + 2))
            screen.blit(ability_surf, ability_rect)

        # Alerta de cambio de fase
        if phase_msg_text and pygame.time.get_ticks() < phase_msg_timer:
            msg_surf = font_menu.render(phase_msg_text, True, BOSS_COLOR)
            msg_rect = msg_surf.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 130))
            screen.blit(font_menu.render(phase_msg_text, True, CRT_GLOW), (msg_rect.x + 3, msg_rect.y + 3))
            screen.blit(msg_surf, msg_rect)

        # --- PANTALLA DE FIN DE PARTIDA ---
        if game_over:
            win_pulse += 0.05
            if int(win_pulse * 2.5) % 2 == 0:
                main_text = "YOU WIN" if player["alive"] else "DEFEAT"
                text_color = CRT_GREEN if player["alive"] else (255, 30, 30)

                text_surface = font_win.render(main_text, True, text_color)
                text_rect = text_surface.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 50))
                screen.blit(font_win.render(main_text, True, CRT_GLOW), (text_rect.x + 5, text_rect.y + 5))
                screen.blit(text_surface, text_rect)

            survivor = [b for b in bots if b["alive"]]
            if player["alive"]:
                w_text = "¡SISTEMA JEFE DESTRUIDO CON ÉXITO!" if bot_difficulty == "BOSS FINAL" else "¡HAS GANADO, SIMULACIÓN COMPLETADA!"
                w_color = PLAYER_COLOR
            else:
                if bot_difficulty == "BOSS FINAL":
                    boss_is_alive = any(b.get("is_boss") for b in survivor)
                    if boss_is_alive:
                        w_text = "EL MÁSTER BOSS O SUS ESCOLTAS HAN ANIQUILADO TU SISTEMA"
                    else:
                        w_text = "LOS ESCOLTAS TE ELIMINARON TRAS LA CAÍDA DEL JEFE"
                elif survivor:
                    w_text = f"SIMULACIÓN CONCLUIDA - GANADOR: {survivor[0]['name']}"
                else:
                    w_text = "ANIQUILACIÓN MUTUA DETECTADA"
                w_color = BOSS_COLOR

            screen.blit(w_surf := font_interface.render(w_text, True, w_color), w_surf.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 40)))

    # Retícula de mira del Mouse
    pygame.draw.circle(screen, PLAYER_COLOR, mouse_pos, 15, 1)
    pygame.draw.line(screen, PLAYER_COLOR, (mouse_pos[0]-22, mouse_pos[1]), (mouse_pos[0]+22, mouse_pos[1]), 1)
    pygame.draw.line(screen, PLAYER_COLOR, (mouse_pos[0], mouse_pos[1]-22), (mouse_pos[0], mouse_pos[1]+22), 1)

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
sys.exit()
