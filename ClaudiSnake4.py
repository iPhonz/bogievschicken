import pygame
import sys
import random
from collections import deque
import cv2
import numpy as np
import os

# Constants
WIDTH, HEIGHT = 1600, 1200
BLOCK_SIZE = 80
BASE_SPEEDS = {'EASY': 8, 'MEDIUM': 12, 'HARD': 16}
DIFFICULTIES = ['EASY', 'MEDIUM', 'HARD']
TIME_LIMITS = {'EASY': 60, 'MEDIUM': 45, 'HARD': 35}
SUCCESS_SCORE = 1000

# Colors
BACKGROUND = (240, 240, 240)
SNAKE_COLOR = (30, 130, 76)
SNAKE_GRADIENT = [(30, 130, 76), (39, 174, 96)]
TEXT_COLOR = (255, 255, 255)
WHITE = (255, 255, 255)
TRANSLUCENT = (255, 255, 255, 180)

# Initialize Pygame and audio
def initialize_pygame():
    pygame.init()
    try:
        pygame.mixer.init()
        return True
    except pygame.error:
        print("Pygame mixer initialization failed. Audio will be disabled.")
        print("To enable audio, make sure you have the necessary audio codecs installed.")
        return False

# Load assets
def load_image(filename, size=None):
    try:
        image = pygame.image.load(filename)
        if size:
            return pygame.transform.scale(image, size)
        return image
    except pygame.error:
        print(f"Unable to load image: {filename}")
        return pygame.Surface((BLOCK_SIZE, BLOCK_SIZE))

def load_sound(filename):
    try:
        return pygame.mixer.Sound(filename)
    except pygame.error:
        print(f"Unable to load sound: {filename}")
        return None

def load_assets(use_audio):
    background_image = load_image('background2.jpg', (WIDTH, HEIGHT))
    intro_background = load_image('intro_background.jpg', (WIDTH, HEIGHT))
    spill_logo = load_image('spill_logo.jpg', (BLOCK_SIZE, BLOCK_SIZE))
    nyt_logo = load_image('nyt_logo.jpg', (BLOCK_SIZE, BLOCK_SIZE))

    sounds = {}
    if use_audio:
        sounds['eat'] = load_sound('eat_sound.wav')
        sounds['game_over'] = load_sound('game_over_sound.wav')
        sounds['success'] = load_sound('success_sound.mp3')
        sounds['intro'] = load_sound('intro_music.mp3')
        sounds['gameplay'] = load_sound('gameplay_music.mp3')

    return background_image, intro_background, spill_logo, nyt_logo, sounds

# Game logic
def generate_food(snake):
    while True:
        new_food = (random.randint(0, (WIDTH - BLOCK_SIZE) // BLOCK_SIZE) * BLOCK_SIZE,
                    random.randint(0, (HEIGHT - BLOCK_SIZE) // BLOCK_SIZE) * BLOCK_SIZE)
        if new_food not in snake:
            return new_food

def reset_game(difficulty):
    snake = deque([(400, 400), (480, 400), (560, 400), (640, 400), (720, 400)])
    food = generate_food(snake)
    direction = 'RIGHT'
    score = 0
    start_time = pygame.time.get_ticks()
    time_limit = TIME_LIMITS[difficulty] * 1000  # Convert to milliseconds
    return snake, food, direction, score, start_time, time_limit

# Drawing functions
def draw_text(screen, text, pos, color, font_size=72, shadow_color=(0, 0, 0)):
    font = pygame.font.Font(None, font_size)
    text_shadow = font.render(text, True, shadow_color)
    shadow_rect = text_shadow.get_rect(center=(pos[0]+4, pos[1]+4))
    screen.blit(text_shadow, shadow_rect)
    text_surface = font.render(text, True, color)
    text_rect = text_surface.get_rect(center=pos)
    screen.blit(text_surface, text_rect)

def draw_button(screen, rect, text):
    pygame.draw.rect(screen, WHITE, rect)
    draw_text(screen, text, rect.center, TEXT_COLOR, 48)

def draw_info_box(screen, score, current_time, difficulty, completed_cycles, time_limit):
    info_box = pygame.Surface((400, 240), pygame.SRCALPHA)
    pygame.draw.rect(info_box, TRANSLUCENT, info_box.get_rect(), border_radius=20)
    screen.blit(info_box, (20, 20))
    
    current_difficulty = f"{difficulty} +{completed_cycles}"
    time_left = max(0, (time_limit - current_time) // 1000)
    draw_text(screen, f'Score: {score}', (220, 60), TEXT_COLOR, 48)
    draw_text(screen, f'Time left: {time_left}s', (220, 120), TEXT_COLOR, 48)
    draw_text(screen, f'Difficulty: {current_difficulty}', (220, 180), TEXT_COLOR, 48)

def draw_snake_segment(screen, pos, spill_logo, is_head=False, letter=None):
    if is_head:
        screen.blit(spill_logo, pos)
    elif letter:
        font = pygame.font.Font(None, BLOCK_SIZE)
        letter_surface = font.render(letter, True, SNAKE_GRADIENT[1])
        letter_rect = letter_surface.get_rect(center=(pos[0] + BLOCK_SIZE // 2, pos[1] + BLOCK_SIZE // 2))
        pygame.draw.rect(screen, SNAKE_COLOR, pygame.Rect(pos[0], pos[1], BLOCK_SIZE, BLOCK_SIZE))
        screen.blit(letter_surface, letter_rect)
    else:
        rect = pygame.Rect(pos[0], pos[1], BLOCK_SIZE, BLOCK_SIZE)
        pygame.draw.rect(screen, SNAKE_COLOR, rect)
        pygame.draw.rect(screen, SNAKE_GRADIENT[1], rect, 4)
        pygame.draw.circle(screen, SNAKE_GRADIENT[1], (pos[0] + BLOCK_SIZE // 2, pos[1] + BLOCK_SIZE // 2), BLOCK_SIZE // 4)

def draw_food(screen, pos, nyt_logo):
    rect = pygame.Rect(pos[0], pos[1], BLOCK_SIZE, BLOCK_SIZE)
    pygame.draw.rect(screen, (200, 0, 0), rect)
    screen.blit(nyt_logo, pos)

def draw_blinking_text(screen, text, pos, color, font_size=144, blink_speed=5):
    if pygame.time.get_ticks() % (1000 // blink_speed) < 500 // blink_speed:
        draw_text(screen, text, pos, color, font_size)

def draw_strobe_effect(screen):
    strobe_surface = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    alpha = abs(int(255 * np.sin(pygame.time.get_ticks() * 0.01)))
    strobe_surface.fill((255, 255, 255, alpha))
    screen.blit(strobe_surface, (0, 0))

def draw_intro_screen(screen, intro_background):
    screen.blit(intro_background, (0, 0))
    text = "Bogie vs Chicken"
    font_size = 200
    font = pygame.font.Font(None, font_size)
    text_surface = font.render(text, True, WHITE)
    text_rect = text_surface.get_rect(center=(WIDTH // 2, HEIGHT // 6))
    
    color = (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
    pygame.draw.rect(screen, color, text_rect.inflate(40, 40))
    screen.blit(text_surface, text_rect)
    
    draw_text(screen, "Press SPACE to start", (WIDTH // 2, HEIGHT * 3 // 4), WHITE, 72)

def draw_difficulty_selection(screen, background_image, gradient_overlay):
    screen.blit(background_image, (0, 0))
    screen.blit(gradient_overlay, (0, 0))
    
    draw_text(screen, 'Select Difficulty', (WIDTH // 2, HEIGHT // 4), TEXT_COLOR, 144)
    
    difficulty_buttons = []
    for i, difficulty in enumerate(DIFFICULTIES):
        button_rect = pygame.Rect(WIDTH // 2 - 200, HEIGHT // 2 - 150 + i * 200, 400, 100)
        difficulty_buttons.append(button_rect)
        
        pygame.draw.rect(screen, WHITE, button_rect, 4)
        
        draw_text(screen, difficulty, button_rect.center, TEXT_COLOR, 72)
    
    return difficulty_buttons

def main():
    use_audio = initialize_pygame()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Bogie vs Chicken")

    background_image, intro_background, spill_logo, nyt_logo, sounds = load_assets(use_audio)

    gradient_overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    gradient_rect = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    pygame.draw.rect(gradient_rect, (0, 0, 0, 180), gradient_rect.get_rect(), border_radius=0)
    gradient_overlay.blit(gradient_rect, (0, 0))

    exit_button = pygame.Rect(WIDTH - 200, 20, 180, 60)
    play_again_button = pygame.Rect(WIDTH // 2 - 200, HEIGHT // 2 + 100, 400, 60)
    exit_game_button = pygame.Rect(WIDTH // 2 - 200, HEIGHT // 2 + 200, 400, 60)

    difficulty_index = 0
    speed = BASE_SPEEDS[DIFFICULTIES[difficulty_index]]
    completed_cycles = 0

    snake, food, direction, score, start_time, time_limit = reset_game(DIFFICULTIES[difficulty_index])

    game_over = False
    game_won = False
    choosing_difficulty = False
    playing_video = False
    video_play_count = 0
    paused = False
    show_intro = True
    all_levels_completed = False

    try:
        success_video = cv2.VideoCapture('success_video.mov')
        video_fps = success_video.get(cv2.CAP_PROP_FPS)
    except cv2.error:
        print("Unable to load success video. Video playback will be disabled.")
        success_video = None

    clock = pygame.time.Clock()
    video_clock = pygame.time.Clock()

    if use_audio:
        sounds['intro'].play(-1)

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                if success_video:
                    success_video.release()
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                if show_intro and event.key == pygame.K_SPACE:
                    show_intro = False
                    choosing_difficulty = True
                    if use_audio:
                        sounds['intro'].stop()
                elif not game_over and not game_won and not choosing_difficulty and not playing_video:
                    if event.key == pygame.K_UP and direction != 'DOWN':
                        direction = 'UP'
                    elif event.key == pygame.K_DOWN and direction != 'UP':
                        direction = 'DOWN'
                    elif event.key == pygame.K_LEFT and direction != 'RIGHT':
                        direction = 'LEFT'
                    elif event.key == pygame.K_RIGHT and direction != 'LEFT':
                        direction = 'RIGHT'
                    elif event.key == pygame.K_p:
                        paused = not paused
                        if paused:
                            if use_audio:
                                sounds['gameplay'].stop()
                        else:
                            if use_audio:
                                sounds['gameplay'].play(-1)
                elif playing_video and event.key == pygame.K_SPACE:
                    playing_video = False
                    if success_video:
                        success_video.set(cv2.CAP_PROP_POS_FRAMES, 0)
                    video_play_count = 0
                    if use_audio:
                        pygame.mixer.music.stop()
                    choosing_difficulty = True
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if exit_button.collidepoint(event.pos):
                    if success_video:
                        success_video.release()
                    pygame.quit()
                    sys.exit()
                elif choosing_difficulty:
                    difficulty_buttons = draw_difficulty_selection(screen, background_image, gradient_overlay)
                    for i, button in enumerate(difficulty_buttons):
                        if button.collidepoint(event.pos):
                            difficulty_index = i
                            speed = BASE_SPEEDS[DIFFICULTIES[difficulty_index]]
                            choosing_difficulty = False
                            snake, food, direction, score, start_time, time_limit = reset_game(DIFFICULTIES[difficulty_index])
                            if use_audio:
                                sounds['gameplay'].play(-1)
                elif (game_over or game_won) and play_again_button.collidepoint(event.pos):
                    if game_won:
                        if difficulty_index < len(DIFFICULTIES) - 1:
                            difficulty_index += 1
                        else:
                            difficulty_index = 0
                            completed_cycles += 1
                        speed = BASE_SPEEDS[DIFFICULTIES[difficulty_index]] + completed_cycles
                    elif game_over:
                        difficulty_index = 0
                        completed_cycles = 0
                        speed = BASE_SPEEDS[DIFFICULTIES[difficulty_index]]
                    snake, food, direction, score, start_time, time_limit = reset_game(DIFFICULTIES[difficulty_index])
                    game_over = False
                    game_won = False
                    if use_audio:
                        sounds['gameplay'].play(-1)
                elif (game_over or game_won) and exit_game_button.collidepoint(event.pos):
                    if success_video:
                        success_video.release()
                    pygame.quit()
                    sys.exit()

        if show_intro:
            draw_intro_screen(screen, intro_background)
        elif choosing_difficulty:
            difficulty_buttons = draw_difficulty_selection(screen, background_image, gradient_overlay)
        elif playing_video and success_video:
            if video_play_count == 0 and use_audio:
                if all_levels_completed:
                    pygame.mixer.music.load('victory_music.mp3')
                    pygame.mixer.music.play(-1)
                else:
                    sounds['success'].play()
            ret, frame = success_video.read()
            if ret:
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                frame = cv2.resize(frame, (WIDTH, HEIGHT))
                frame = np.rot90(frame)
                frame = pygame.surfarray.make_surface(frame)
                screen.blit(frame, (0, 0))
                
                draw_blinking_text(screen, "YOU ARE THE BEST!", (WIDTH // 2, HEIGHT // 4), (255, 255, 0), 144)
                draw_blinking_text(screen, "YOU ARE A DRAGON!", (WIDTH // 2, HEIGHT * 3 // 4), (255, 0, 0), 144)
                draw_strobe_effect(screen)
                
                video_clock.tick(video_fps)
            else:
                video_play_count += 1
                if video_play_count < 32:
                    success_video.set(cv2.CAP_PROP_POS_FRAMES, 0)
                else:
                    playing_video = False
                    video_play_count = 0
                    if use_audio:
                        pygame.mixer.music.stop()
                    choosing_difficulty = True
        else:
            if not game_over and not game_won and not choosing_difficulty and not paused:
                head = snake[-1]
                if direction == 'UP':
                    new_head = (head[0], (head[1] - BLOCK_SIZE) % HEIGHT)
                elif direction == 'DOWN':
                    new_head = (head[0], (head[1] + BLOCK_SIZE) % HEIGHT)
                elif direction == 'LEFT':
                    new_head = ((head[0] - BLOCK_SIZE) % WIDTH, head[1])
                elif direction == 'RIGHT':
                    new_head = ((head[0] + BLOCK_SIZE) % WIDTH, head[1])

                snake.append(new_head)

                if new_head == food:
                    food = generate_food(snake)
                    score += 325
                    if use_audio and sounds['eat']:
                        sounds['eat'].play()
                else:
                    snake.popleft()

                if new_head in list(snake)[:-1]:
                    game_over = True
                    if use_audio:
                        sounds['gameplay'].stop()
                        sounds['game_over'].play()

                current_time = pygame.time.get_ticks() - start_time
                if current_time >= time_limit:
                    game_over = True
                    if use_audio:
                        sounds['gameplay'].stop()
                        sounds['game_over'].play()

                if score >= SUCCESS_SCORE:
                    game_won = True
                    if use_audio:
                        sounds['gameplay'].stop()
                        sounds['success'].play()
                    if difficulty_index == len(DIFFICULTIES) - 1 and completed_cycles == 0:
                        playing_video = True
                        all_levels_completed = True

            screen.blit(background_image, (0, 0))
            screen.blit(gradient_overlay, (0, 0))

            # Draw the snake with "SPILL" in its body
            spill_letters = "SPILL"
            letter_index = 0
            for i, pos in enumerate(reversed(snake)):
                if i == 0:  # Head
                    draw_snake_segment(screen, pos, spill_logo, is_head=True)
                elif i < len(spill_letters) + 1:  # Body segments spelling "SPILL"
                    draw_snake_segment(screen, pos, spill_logo, letter=spill_letters[letter_index])
                    letter_index = (letter_index + 1) % len(spill_letters)
                else:  # Remaining body segments
                    draw_snake_segment(screen, pos, spill_logo)

            draw_food(screen, food, nyt_logo)
            draw_info_box(screen, score, current_time, DIFFICULTIES[difficulty_index], completed_cycles, time_limit)
            draw_button(screen, exit_button, 'Exit')

            if game_over:
                draw_text(screen, 'GAME OVER', (WIDTH // 2, HEIGHT // 2 - 100), TEXT_COLOR, 144)
                draw_button(screen, play_again_button, 'Play Again')
                draw_button(screen, exit_game_button, 'Exit')
            elif game_won:
                draw_text(screen, 'YOU WIN!', (WIDTH // 2, HEIGHT // 2 - 100), TEXT_COLOR, 144)
                draw_button(screen, play_again_button, 'Next Level')
                draw_button(screen, exit_game_button, 'Exit')

        pygame.display.flip()

        if not playing_video:
            clock.tick(speed)

if __name__ == "__main__":
    main()