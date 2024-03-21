import sys
from time import sleep

import pygame
from settings import Settings
from game_stats import GameStats
from scoreboard import Scoreboard
from button import Button
from ship import Ship
from bullet import Bullet
from alien import Alien


class AlienInvasion:
    """Overall class to manage game assets and behavior."""

    def __init__(self):
        """Initialize the game, and create game resources."""
        pygame.init()
        self.settings = Settings()

        self.screen = pygame.display.set_mode((1200, 800))
        # Use below code snippet to run game in fullscreen mode
        """self.screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        self.settings.screen_width = self.screen.get_rect().width
        self.settings.screen_height = self.screen.get_rect().height"""
        pygame.display.set_caption("Alien Invasion")

        # Create an instance to store game statistics.
        # And create a scoreboard
        self.stats = GameStats(self)
        self.sb = Scoreboard(self)

        # Creates the actual initials of the game
        self.ship = Ship(self)
        self.bullets = pygame.sprite.Group()  # creates a group to manage bullets already fired
        self.aliens = pygame.sprite.Group()  # create a group to manage the aliens

        self._create_fleet()

        # Making the play button
        self.play_button = Button(self, "Play Game")

    def _create_alien(self, alien_number, row_number):
        # create an alien and place it in the row adjacent to the last one
        alien = Alien(self)
        alien_width, alien_height = alien.rect.size  # Uses the 'size' tuple to get x and y dims
        alien.x = alien_width + (2 * alien_width * alien_number)  # defines x-pos
        alien.rect.x = alien.x
        alien.rect.y = alien_height + (2 * alien.rect.height * row_number)  # defines y-pos
        self.aliens.add(alien)  # adds the newly created alien to the group

    def _create_fleet(self):
        """Create the fleet of aliens."""
        # Create an alien and find the number of aliens in a row
        # Spacing between each alien is equal to one alien width
        # Make an alien
        alien = Alien(self)
        alien_width, alien_height = alien.rect.size
        available_space_x = self.settings.screen_width - (2 * alien_width)
        number_aliens_x = available_space_x // (2 * alien_width)  # "//" is the floor divisor

        # Determine the number of rows of aliens that fit on the screen
        ship_height = self.ship.rect.height
        available_space_y = (self.settings.screen_height - (3 * alien_height) - ship_height)
        number_rows = available_space_y // (2 * alien_height)

        # Creates the full fleet of aliens
        for row_number in range(number_rows):
            # Create the first row of aliens
            for alien_number in range(number_aliens_x):
                self._create_alien(alien_number, row_number)

    def _check_fleet_edges(self):
        """Respond appropriately if any aliens hit the edge"""
        for alien in self.aliens.sprites():  # checks all of the aliens
            if alien.check_edges():
                self._change_fleet_direction()  # if any of them return true we flip the dir of the whole fleet
                break

    def _change_fleet_direction(self):
        """Drops the height of the entire fleet when called"""
        for alien in self.aliens.sprites():
            alien.rect.y += self.settings.fleet_drop_speed  # drops them 10 pixels
        self.settings.fleet_direction *= -1  # flips the direction by mupltiplying itself by -1

    def run_game(self):
        """Start the main loop for the game."""
        while True:
            self._check_events()

            if self.stats.game_active:
                self.ship.update()
                self._update_bullets()
                self._update_aliens()

            self._update_screen()

    def _check_events(self):
        # Watch for keyboard and mouse events.
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                self._check_keydown_events(event)
            elif event.type == pygame.KEYUP:  # stop moving if the key is lifted
                self._check_keyup_events(event)
            elif event.type == pygame.MOUSEBUTTONDOWN:
                mouse_pos = pygame.mouse.get_pos()
                self._check_play_button(mouse_pos)

    def _check_play_button(self, mouse_pos):
        """Start the new game when the player clicks on the 'play' button"""
        button_clicked = self.play_button.rect.collidepoint(mouse_pos)
        if button_clicked and not self.stats.game_active:
            self._start_game()

    def _start_game(self):
        # Reset the game stats
        self.stats.reset_stats()  # Resets the number of ships
        self.stats.game_active = True
        self.sb.prep_score()
        self.sb.prep_level()
        self.sb.prep_ships()

        # Clears remaining aliens and bullets and redraws new ones
        self.aliens.empty()
        self.bullets.empty()
        self._create_fleet()
        self.ship.center_ship()

        # Hide the mouse cursor
        pygame.mouse.set_visible(False)

        # Reset the game settings.
        self.settings.initialize_dynamic_settings()

    def _check_keydown_events(self, event):
        """Responds to key presses"""
        if event.key == pygame.K_RIGHT:
            self.ship.moving_right = True  # move the ship to the right.
        elif event.key == pygame.K_LEFT:
            self.ship.moving_left = True  # move the ship to the left.
        elif event.key == pygame.K_q:
            sys.exit()
        elif event.key == pygame.K_SPACE:  # we don't need a keyDOWN event bc there is just one action from space
            self._fire_bullet()
        elif event.key == pygame.K_p:
            self._start_game()

    def _check_keyup_events(self, event):
        """Responds when the key is released"""
        if event.key == pygame.K_RIGHT:
            self.ship.moving_right = False  # sets the ship stationary again
        elif event.key == pygame.K_LEFT:
            self.ship.moving_left = False

    def _fire_bullet(self):
        """Create a new bullet and add it to the bullets group."""
        if len(self.bullets) < self.settings.bullets_allowed:  # implements bullet limiter
            new_bullet = Bullet(self)
            self.bullets.add(new_bullet)  # adds a new bullet sprite to the group

    def _update_bullets(self):
        """Update position of bullets and get rid of old bullets."""
        # Update bullet positions.
        self.bullets.update()

        # Get rid of bullets that disappear
        for bullet in self.bullets.copy():
            if bullet.rect.bottom <= 0:
                self.bullets.remove(bullet)
        # print(len(self.bullets)) proof of concept that bullets were generated then deleted

        self._check_bullet_alien_collisions()

    def _check_bullet_alien_collisions(self):
        # Check for any bullets that have collided with an alien instance
        # Eliminate both the bullet and the alien
        """The new code we added compares the positions of all the bullets in 
        self.bullets and all the aliens in self.aliens, and identifies any that 
        overlap. Whenever the rects of a bullet and alien overlap, groupcollide() 
        adds a key-value pair to the dictionary it returns. The two True arguments 
        tell Pygame to delete the bullets and aliens that have collided. 
        (To make a high-powered bullet that can travel to the top of the screen, 
        destroying every alien in its path, you could set the first Boolean argument
        to False and keep the second Boolean argument set to True. The aliens hit 
        would disappear, but all bullets would stay active until they disappeared 
        off the top of the screen.)"""
        collisions = pygame.sprite.groupcollide(self.bullets, self.aliens, True, True)

        # Changes the score every time we hit an alien
        if collisions:
            for aliens in collisions.values():
                self.stats.score += self.settings.alien_points * len(aliens)
            self.sb.prep_score()
            self.sb.check_high_score()

        if not self.aliens:  # checks whether the aliens group is empty
            # I can delete existing bullets with self.bullets.empty()
            # creates a new fleet
            self._create_fleet()
            self.settings.increase_speed()

            # Increase level
            self.stats.level += 1
            self.sb.prep_level()

    def _update_aliens(self):
        """Check if the fleet is at an edge,
        then update the positions of all aliens in the fleet"""
        self._check_fleet_edges()
        self.aliens.update()

        # Look for alien-ship collisions
        if pygame.sprite.spritecollideany(self.ship, self.aliens):
            print(f"Ship Hit!!! You have {self.stats.ships_left} ships left!")
            self._ship_hit()

        # Looks for any aliens approaching the bottom of the screen
        self._check_aliens_bottom()

    def _ship_hit(self):
        """Respond to the ship being hit by an alien"""

        if self.stats.ships_left > 0:
            # Decrement ships left and update scoreboard
            self.stats.ships_left -= 1
            self.sb.prep_ships()

            # Remove remaining aliens and bullets
            self.aliens.empty()
            self.bullets.empty()

            # Create a new fleet and center the ship
            self._create_fleet()
            self.ship.center_ship()

            # Pause the game for a half second
            sleep(0.5)
        else:
            self.stats.game_active = False
            pygame.mouse.set_visible(True)

    def _check_aliens_bottom(self):
        """Checks if any aliens reach the bottom of the screen"""
        screen_rect = self.screen.get_rect()
        for alien in self.aliens.sprites():
            if alien.rect.bottom >= screen_rect.bottom:  # checks the bottom of each instance and compares
                # We can treat this the same as if we got hit and use that method
                self._ship_hit()
                break

    def _update_screen(self):
        """Update images on the screen, and flip to the new screen."""
        # Redraw the screen during each pass through the loop.
        self.screen.fill(self.settings.bg_color)
        self.ship.blitme()
        for bullet in self.bullets.sprites():
            bullet.draw_bullet()  # updates the bullets on the screen
        self.aliens.draw(self.screen)  # makes alien appear on the screen which is draw's argument

        # Draw the score information
        self.sb.show_score()

        # Draw the play button if the game is inactive
        if not self.stats.game_active:
            self.play_button.draw_button()

        # Make the most recently drawn screen visible.
        pygame.display.flip()


if __name__ == '__main__':
    # Make a game instance, and run the game.
    ai = AlienInvasion()
    ai.run_game()
