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
import traceback
from datetime import datetime, timedelta

# GAME START
# Here we define the bot's name as Settler and initialize the game, including communication with the Halite engine.
game = hlt.Game("Jbot")
# Then we print our start message to the logs
LOG = logging.getLogger('jbot')
LOG.setLevel(logging.INFO)
LOG.info("Starting my jbot !")


def get_nearest_planet_for_ship(myship):
    """Get the nearest planet of any type for the passed in ship

    Args:
        game_map: halite game_map instance
        myship: any ship

    Returns:
        Planet: instance of a planet

    """
    entities_by_distance = game_map.nearby_entities_by_distance(myship)
    LOG.debug('entities by distance: %s', entities_by_distance)
    for distance in sorted(entities_by_distance):
        entities = entities_by_distance[distance]
        LOG.debug('distance: %s, entities: %s', distance, entities)
        for entity in entities:
            LOG.debug('entity: %s', entity)
            if isinstance(entity, hlt.entity.Planet):
                return entity


def get_nearest_unowned_planet_for_ship(myship):
    """Get the nearest unowned planet for the passed in ship

    Args:
        game_map: halite game_map instance
        myship: any ship

    Returns:
        Planet: instance of a planet

    """
    entities_by_distance = game_map.nearby_entities_by_distance(myship)
    LOG.debug('entities by distance: %s', entities_by_distance)
    for distance in sorted(entities_by_distance):
        entities = entities_by_distance[distance]
        LOG.debug('distance: %s, entities: %s', distance, entities)
        for entity in entities:
            LOG.debug('entity: %s', entity)
            if isinstance(entity, hlt.entity.Planet):
                if not entity.is_owned():
                    return entity


def get_nearest_3_unowned_planets_for_ship(myship):
    """Get the nearest 3 unowned planet for the passed in ship.  Only used for turn 1 logic.

    Args:
        game_map: halite game_map instance
        myship: any ship

    Returns:
        list: of planets

    """
    entities_by_distance = game_map.nearby_entities_by_distance(myship)
    LOG.debug('entities by distance: %s', entities_by_distance)
    three_planets = []
    for distance in sorted(entities_by_distance):
        entities = entities_by_distance[distance]
        LOG.debug('distance: %s, entities: %s', distance, entities)
        for entity in entities:
            LOG.debug('entity: %s', entity)
            if isinstance(entity, hlt.entity.Planet):
                if not entity.is_owned():
                    three_planets.append(entity)
                    if len(three_planets) == 3:
                        return three_planets


def get_nearest_enemy_ship(myship):
    """Get the nearest enemy ship

    Args:
        myship: One of my ships

    Returns:
        htl.entity.Ship: Nearest enemy ship
    """
    LOG.info('Finding nearest enemy ship')
    entities = game_map.nearby_entities_by_distance(myship)
    LOG.info('entities: %s', entities)
    for distance, entity_list in entities.items():
        LOG.info('checking entity_list: %s', entity_list)
        for entity in entity_list:
            LOG.info('checking entity: %s', entity)
            if isinstance(entity, hlt.entity.Ship):
                LOG.info('It is a ship!')
                entity_owner = entity.owner
                my_id = game_map.my_id
                LOG.info('COMPARING entity_owner %s and my id %s', entity_owner, my_id)
                if entity.owner != game_map.my_id:
                    LOG.info('Not owned by me!!!!, returning %s', entity)
                    return entity


def nearby_enemy_docker(myship, all_players):
    """
    Locate a nearby enemy ship docking
    """
    for player in all_players:
        playerid = player.id
        player_ships = player.all_ships()
        player_ships.sort(key=lambda x: myship.calculate_distance_between(x))
        if playerid != game_map.my_id:
            for enemy_ship in player_ships:
                if enemy_ship.docking_status == enemy_ship.DockingStatus.DOCKING and myship.calculate_distance_between(enemy_ship) <= 35:
                    return enemy_ship
    return False

timedelta_2s = timedelta(seconds=2)
timedelta_buffer = timedelta(milliseconds=200)
try:
    TURN = 0
    early_shipmap = {}
    while True:
        # TURN START
        time_turnstart = datetime.utcnow()
        time_timeout = time_turnstart + timedelta_2s

        # Update the map for the new turn and get the latest version
        game_map = game.update_map()
        TURN += 1
        LOG.info('TURN %s START', TURN)

        # Here we define the set of commands to be sent to the Halite engine at the end of the turn
        command_queue = []

        my_ships = game_map.get_me().all_ships()
        all_players = game_map.all_players()
        initial_3_planets = []

        # For every ship that I control
        shipcount = 0
        for ship in my_ships:
            shipcount += 1
            time_now = datetime.utcnow()

            # TIMEOUT PROTECTION
            if time_now + timedelta_buffer >= time_timeout:
                LOG.warning('BAILING TURN FOR TIMEOUT')
                break  # break out of the per ship loop, which should send our commands

            # SHIP IS DOCKED, DO NOTHING
            if ship.docking_status != ship.DockingStatus.UNDOCKED:
                # Skip this ship
                continue

            # EARLY TURNS?  DIVIDE AND CONQUER
            if len(my_ships) == 3 and TURN <= 20:
                if not initial_3_planets:
                    initial_3_planets = get_nearest_3_unowned_planets_for_ship(ship)
                    LOG.info('INITIAL 3 PLANETS: %s', initial_3_planets)
                if TURN == 1:
                    early_shipmap[ship.id] = initial_3_planets[shipcount - 1]
                    LOG.info('EARLY SHIPMAP: %s', early_shipmap)
                go_to_planet = early_shipmap[ship.id]
                LOG.info('EARLY TURNS ship %s going to unowned planet %s', ship.id, go_to_planet)
                if ship.can_dock(go_to_planet):
                    command_queue.append(ship.dock(go_to_planet))
                else:
                    navigate_command = ship.navigate(
                        ship.closest_point_to(go_to_planet),
                        game_map,
                        speed=int(hlt.constants.MAX_SPEED),
                        ignore_ships=False,
                        max_corrections=18,
                        angular_step=5)
                    if navigate_command:
                        command_queue.append(navigate_command)
                continue


            # ATTACK ENEMY DOCKERS
            if nearby_enemy_docker(ship, all_players):
                logging.info("SHIP %s FOUND NEARBY ENEMY DOCKING SHIP, ATTACKING", ship)
                navigate_command = ship.navigate(
                    ship.closest_point_to(ship),
                    game_map,
                    speed=int(hlt.constants.MAX_SPEED),
                    max_corrections=18,
                    angular_step=5,
                    ignore_ships=False,
                    ignore_planets=False)
                if navigate_command:
                    command_queue.append(navigate_command)
                continue

            nearest_planet = get_nearest_planet_for_ship(ship)
            nearest_unowned_planet = get_nearest_unowned_planet_for_ship(ship)
            LOG.debug('ship %s, nearest ANY_planet: %s', ship, nearest_planet)
            LOG.debug('ship %s, nearest UNO_planet: %s', ship, nearest_unowned_planet)

            # GO TO NEAREST UNOWNED PLANET
            if nearest_unowned_planet:
                LOG.info('ship %s going to nearest unowned planet %s', ship, nearest_planet)
                if ship.can_dock(nearest_unowned_planet):
                    command_queue.append(ship.dock(nearest_unowned_planet))
                else:
                    navigate_command = ship.navigate(
                        ship.closest_point_to(nearest_unowned_planet),
                        game_map,
                        speed=int(hlt.constants.MAX_SPEED),
                        ignore_ships=False,
                        max_corrections=18,
                        angular_step=5)
                    if navigate_command:
                        command_queue.append(navigate_command)
                continue

            # ATTACK NEAREST ENEMY SHIP
            nearest_enemy_ship = get_nearest_enemy_ship(ship)
            if nearest_enemy_ship:
                navigate_command = ship.navigate(
                    ship.closest_point_to(nearest_enemy_ship),
                    game_map,
                    speed=int(hlt.constants.MAX_SPEED),
                    max_corrections=18,
                    angular_step=5,
                    ignore_ships=False,
                    ignore_planets=False)
                if navigate_command:
                    command_queue.append(navigate_command)
                continue

        # Send our set of commands to the Halite engine for this turn
        game.send_command_queue(command_queue)
        # TURN END
    # GAME END
except Exception as e:
    LOG.critical(e)
    LOG.critical(traceback.format_exc())
