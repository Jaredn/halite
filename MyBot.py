"""
Welcome to your first Halite-II bot!

This bot's name is Settler. It's purpose is simple (don't expect it to win complex games :) ):
1. Initialize game
2. If a ship is not docked and there are unowned planets
2.a. Try to Dock in the planet if close enough
2.b If not, go towards the planet

Note: Please do not place print statements here as they are used to communicate with the Halite engine. If you need
to log anything use the logging module.
"""
# Let's start by importing the Halite Starter Kit so we can interface with the Halite engine
import hlt
# Then let's import the logging module so we can print out information
import logging
from datetime import datetime, timedelta

# GAME START
# Here we define the bot's name as Settler and initialize the game, including communication with the Halite engine.
game = hlt.Game("Jbot")
# Then we print our start message to the logs
LOG = logging.getLogger('jbot')
LOG.setLevel(logging.INFO)
LOG.info("Starting my jbot !")


def get_nearest_planet_for_ship(game_map, ship):
    entities_by_distance = game_map.nearby_entities_by_distance(ship)
    LOG.debug('entities by distance: %s', entities_by_distance)
    for distance in sorted(entities_by_distance):
        entities = entities_by_distance[distance]
        LOG.debug('distance: %s, entities: %s', distance, entities)
        for entity in entities:
            LOG.debug('entity: %s', entity)
            if isinstance(entity, hlt.entity.Planet):
                return entity


def get_nearest_unowned_planet_for_ship(game_map, ship):
    entities_by_distance = game_map.nearby_entities_by_distance(ship)
    LOG.debug('entities by distance: %s', entities_by_distance)
    for distance in sorted(entities_by_distance):
        entities = entities_by_distance[distance]
        LOG.debug('distance: %s, entities: %s', distance, entities)
        for entity in entities:
            LOG.debug('entity: %s', entity)
            if isinstance(entity, hlt.entity.Planet):
                if not entity.is_owned():
                    return entity

timedelta_2s = timedelta(seconds=2)
timedelta_buffer = timedelta(milliseconds=200)
while True:
    # TURN START
    time_turnstart = datetime.utcnow()
    time_timeout = time_turnstart + timedelta_2s

    # Update the map for the new turn and get the latest version
    game_map = game.update_map()

    # Here we define the set of commands to be sent to the Halite engine at the end of the turn
    command_queue = []

    # For every ship that I control
    for ship in game_map.get_me().all_ships():
        time_now = datetime.utcnow()

        # End turn early if needed due to timeout.
        if time_now + timedelta_buffer >= time_timeout:
            LOG.critical('BAILING TURN FOR TIMEOUT')
            break  # break out of the per ship loop, which should send our commands

        nearest_planet = get_nearest_planet_for_ship(game_map, ship)
        nearest_unowned_planet = get_nearest_unowned_planet_for_ship(game_map, ship)
        LOG.debug('ship %s, nearest ANY_planet: %s', ship, nearest_planet)
        LOG.debug('ship %s, nearest UNO_planet: %s', ship, nearest_unowned_planet)
        # If the ship is docked
        if ship.docking_status != ship.DockingStatus.UNDOCKED:
            # Skip this ship
            continue

        if ship.can_dock(nearest_unowned_planet):
            command_queue.append(ship.dock(nearest_unowned_planet))
        else:
            navigate_command = ship.navigate(
                ship.closest_point_to(nearest_unowned_planet),
                game_map,
                speed=int(hlt.constants.MAX_SPEED/2),
                ignore_ships=True)
            if navigate_command:
                command_queue.append(navigate_command)

    # Send our set of commands to the Halite engine for this turn
    game.send_command_queue(command_queue)
    # TURN END
# GAME END
