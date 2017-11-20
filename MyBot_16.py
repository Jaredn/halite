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
import time

# GAME START
# Here we define the bot's name as Settler and initialize the game, including communication with the Halite engine.
game = hlt.Game("Jbot_16")
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


def get_nearest_notfull_planet_i_own_for_ship(myship):
    """Get the nearest planet owned by me for the passed in ship

    Args:
        game_map: halite game_map instance
        myship: any ship

    Returns:
        Planet: instance of a planet that isn't full

    """
    entities_by_distance = game_map.nearby_entities_by_distance(myship)
    LOG.debug('entities by distance: %s', entities_by_distance)
    for distance in sorted(entities_by_distance):
        entities = entities_by_distance[distance]
        LOG.debug('distance: %s, entities: %s', distance, entities)
        for entity in entities:
            LOG.debug('entity: %s', entity)
            if isinstance(entity, hlt.entity.Planet):
                if entity.owner == myship.owner and not entity.is_full():
                    return entity
    return None


def get_biggest_early_planet_for_ship(myship):
    """Get the nearest 3 unowned planet for the passed in ship.  Only used for turn 1 logic.

    Args:
        game_map: halite game_map instance
        myship: any ship

    Returns:
        hlt.entity.Planet: Initial planet to inhabit.

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
                        three_planets.sort(key=lambda x: x.radius, reverse=True)
                        LOG.critical(three_planets)
                        return three_planets[0]


def get_nearest_enemy_ship(myship):
    """Get the nearest enemy ship

    Args:
        myship: One of my ships

    Returns:
        htl.entity.Ship: Nearest enemy ship
    """
    entities_by_distance = game_map.nearby_entities_by_distance(myship)
    for distance, entity_list in sorted(entities_by_distance.items()):
        for entity in entity_list:
            if isinstance(entity, hlt.entity.Ship):
                if entity.owner != myship.owner:
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
                if enemy_ship.docking_status != enemy_ship.DockingStatus.UNDOCKED and myship.calculate_distance_between(enemy_ship) <= 10:
                    return enemy_ship
    return False


def go_to_nearest_unowned_planet(myship):
    """Move the ship to the nearest unowned planet and dock it.

    Args:
        myship:

    Returns:
        bool: if action was successful

    """
    # GO TO NEAREST UNOWNED PLANET
    nearest_unowned_planet = get_nearest_unowned_planet_for_ship(myship)
    if nearest_unowned_planet:
        LOG.info('SHIP %s going to nearest unowned planet %s', ship.id, nearest_unowned_planet.id)
        if ship.can_dock(nearest_unowned_planet):
            command_queue.append(ship.dock(nearest_unowned_planet))
            return True
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
                return True
    return False


def go_to_nearest_enemy_ship(myship):
    """Go to the nearest enemy ship (attack)

    Args:
        myship:

    Returns:
        bool: if action was successful

    """
    nearest_enemy_ship = get_nearest_enemy_ship(myship)
    if nearest_enemy_ship:
        LOG.info('SHIP %s ATTACKING NEAREST ENEMY SHIP %s', myship.id, nearest_enemy_ship.id)
        navigate_command = ship.navigate(
            myship.closest_point_to(nearest_enemy_ship),
            game_map,
            speed=int(hlt.constants.MAX_SPEED),
            max_corrections=18,
            angular_step=5,
            ignore_ships=False,
            ignore_planets=False)
        if navigate_command:
            command_queue.append(navigate_command)
            return True
    return False


try:
    TURN = 0
    initial_planet = None
    while True:
        # TURN START

        # Update the map for the new turn and get the latest version
        game_map = game.update_map()
        start_time = time.time()
        end_time = start_time + 1.6
        TURN += 1
        LOG.info('TURN %s START', TURN)

        # Here we define the set of commands to be sent to the Halite engine at the end of the turn
        command_queue = []

        my_ships = game_map.get_me().all_ships()
        all_players = game_map.all_players()
        LOG.info('MY SHIPS: %s', len(my_ships))

        # For every ship that I control
        for ship in my_ships:

            # TIMEOUT PROTECTION
            if time.time() > end_time:
                LOG.warning('BAILING TURN FOR TIMEOUT')
                continue  # break out of the per ship loop, which should send our commands

            # SHIP IS DOCKED, DO NOTHING
            if ship.docking_status != ship.DockingStatus.UNDOCKED:
                LOG.info('SHIP %s is docked, skipping.', ship.id)
                # Skip this ship
                continue
            if not initial_planet and TURN is 1:
                initial_planet = get_biggest_early_planet_for_ship(ship)
                LOG.critical('GETTING INITIAL PLANET: id %s', initial_planet.id)

            # ATTACK ENEMY DOCKERS
            enemy_docking_ship = nearby_enemy_docker(ship, all_players)
            if enemy_docking_ship and TURN >= 20:
                logging.info("SHIP %s FOUND NEARBY ENEMY DOCKING SHIP, ATTACKING SHIP %s", ship.id, enemy_docking_ship.id)
                navigate_command = ship.navigate(
                    ship.closest_point_to(enemy_docking_ship),
                    game_map,
                    speed=int(hlt.constants.MAX_SPEED),
                    max_corrections=18,
                    angular_step=5,
                    ignore_ships=False,
                    ignore_planets=False)
                if navigate_command:
                    command_queue.append(navigate_command)
                    continue

            # EARLY TURNS?  HUMP BIGGEST INITIAL PLANET
            if len(my_ships) <= 10 and TURN <= 15:
                LOG.info('In early turns.  HUMP PLANET')
                if ship.can_dock(initial_planet) and not initial_planet.is_full():
                    command_queue.append(ship.dock(initial_planet))
                    LOG.info('SHIP %s docking at initial planet %s', ship.id, initial_planet.id)
                    continue
                elif not initial_planet.is_full():
                    navigate_command = ship.navigate(
                        ship.closest_point_to(initial_planet),
                        game_map,
                        speed=hlt.constants.MAX_SPEED,
                        ignore_ships=False,
                        ignore_planets=False,
                        max_corrections=18,
                        angular_step=5)
                    if navigate_command:
                        command_queue.append(navigate_command)
                        LOG.info('SHIP %s going to initial planet %s', ship.id, initial_planet.id)
                        continue

            # GO TO NEAREST UNOWNED PLANET
            if ship.id % 4 == 0:
                if go_to_nearest_unowned_planet(ship):
                    continue

            # GO TO MY NEAREST NOT FULL BIG PLANET AND DOCK
            my_nearest_planet = get_nearest_notfull_planet_i_own_for_ship(ship)
            if my_nearest_planet and (ship.id % 3 == 1):
                if ship.can_dock(my_nearest_planet) and not my_nearest_planet.is_full():
                    LOG.info('SHIP %s is docking at my planet %s', ship.id, my_nearest_planet.id)
                    command_queue.append(ship.dock(my_nearest_planet))
                    continue
                elif not my_nearest_planet.is_full():
                    navigate_command = ship.navigate(
                        ship.closest_point_to(my_nearest_planet),
                        game_map,
                        speed=int(hlt.constants.MAX_SPEED),
                        ignore_ships=False,
                        max_corrections=18,
                        angular_step=5)
                    if navigate_command:
                        LOG.info('SHIP %s going to my planet %s', ship.id, my_nearest_planet.id)
                        command_queue.append(navigate_command)
                        continue

            # ATTACK NEAREST ENEMY SHIP
            if go_to_nearest_enemy_ship(ship):
                continue
            LOG.warning('SHIP %s NO COMMAND GIVEN', ship.id)

        # Send our set of commands to the Halite engine for this turn
        game.send_command_queue(command_queue)
        # TURN END
    # GAME END
except Exception as e:
    LOG.critical(e)
    LOG.critical(traceback.format_exc())
