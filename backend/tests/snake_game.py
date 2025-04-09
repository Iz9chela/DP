import pygame
import random
import sys

# Initialize Pygame
pygame.init()

# ---------------- Constants & Global Settings ----------------

# Screen dimensions
SCREEN_WIDTH = 600
SCREEN_HEIGHT = 600

# Colors (R, G, B)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GREEN = (0, 255, 0)
RED = (255, 0, 0)

# Game settings
SNAKE_BLOCK = 20  # The size of each snake segment and food block.
FPS = 10  # Frames per second (affects snake speed)


# ---------------- Helper Functions ----------------

def random_food_position(snake_body):
    """
    Generate a random food position that does not collide with the snake body.
    """
    cols = SCREEN_WIDTH // SNAKE_BLOCK
    rows = SCREEN_HEIGHT // SNAKE_BLOCK
    while True:
        food_x = random.randint(0, cols - 1) * SNAKE_BLOCK
        food_y = random.randint(0, rows - 1) * SNAKE_BLOCK
        if [food_x, food_y] not in snake_body:
            return [food_x, food_y]


def draw_text(surface, text, size, color, center):
    """
    Render text on the screen.
    """
    font = pygame.font.SysFont(None, size)
    text_surface = font.render(text, True, color)
    text_rect = text_surface.get_rect(center=center)
    surface.blit(text_surface, text_rect)


# ---------------- Game Classes ----------------

class SnakeGame:
    def __init__(self):
        # Set up display
        self.display = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Snake Game")
        self.clock = pygame.time.Clock()

        # Initialize game state
        self.snake_body = [[SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2]]
        self.direction = [0, 0]  # starting direction: stationary until key pressed.
        self.food_position = random_food_position(self.snake_body)
        self.score = 0

    def process_events(self):
        """
        Process user inputs and events.
        """
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.KEYDOWN:
                # Change direction but prevent the snake from reversing directly.
                if event.key == pygame.K_LEFT and self.direction != [SNAKE_BLOCK, 0]:
                    self.direction = [-SNAKE_BLOCK, 0]
                elif event.key == pygame.K_RIGHT and self.direction != [-SNAKE_BLOCK, 0]:
                    self.direction = [SNAKE_BLOCK, 0]
                elif event.key == pygame.K_UP and self.direction != [0, SNAKE_BLOCK]:
                    self.direction = [0, -SNAKE_BLOCK]
                elif event.key == pygame.K_DOWN and self.direction != [0, -SNAKE_BLOCK]:
                    self.direction = [0, SNAKE_BLOCK]

    def update_snake(self):
        """
        Update snake's position based on current direction, handle growth.
        """
        if self.direction == [0, 0]:
            # Skip updating if no direction has been chosen.
            return

        # Get current head position and calculate new head based on the direction.
        new_head = [self.snake_body[0][0] + self.direction[0],
                    self.snake_body[0][1] + self.direction[1]]
        # Insert new head to the snake body
        self.snake_body.insert(0, new_head)

        # Check if snake has eaten the food
        if new_head == self.food_position:
            self.score += 1
            # Generate new food location not on the snake.
            self.food_position = random_food_position(self.snake_body)
        else:
            # Remove the tail segment if no food has been eaten.
            self.snake_body.pop()

    def check_collisions(self):
        """
        Check for collisions with walls or snake's own body.
        """
        head_x, head_y = self.snake_body[0]
        # Collision with walls
        if head_x < 0 or head_x >= SCREEN_WIDTH or head_y < 0 or head_y >= SCREEN_HEIGHT:
            return True
        # Self-collision: if head collides with any body segment
        if self.snake_body[0] in self.snake_body[1:]:
            return True
        return False

    def render(self):
        """
        Render all game objects and update display.
        """
        self.display.fill(BLACK)

        # Draw Food
        pygame.draw.rect(self.display, RED, (self.food_position[0], self.food_position[1], SNAKE_BLOCK, SNAKE_BLOCK))

        # Draw Snake
        for segment in self.snake_body:
            pygame.draw.rect(self.display, GREEN, (segment[0], segment[1], SNAKE_BLOCK, SNAKE_BLOCK))

        # Draw Score
        draw_text(self.display, f"Score: {self.score}", 30, WHITE, (80, 20))

        pygame.display.update()

    def run(self):
        """
        Main game loop.
        """
        while True:
            self.process_events()
            self.update_snake()

            if self.check_collisions():
                # If collision detected, show Game Over and final score.
                self.display.fill(BLACK)
                draw_text(self.display, "Game Over", 50, RED, (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 30))
                draw_text(self.display, f"Score: {self.score}", 40, WHITE, (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 30))
                pygame.display.update()
                pygame.time.wait(2000)
                pygame.quit()
                sys.exit()

            self.render()
            self.clock.tick(FPS)


# ---------------- Main Entry Point ----------------

if __name__ == "__main__":
    game = SnakeGame()
    game.run()