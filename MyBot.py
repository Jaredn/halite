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
game = hlt.Game("Jbot_new")
# Then we print our start message to the logs
LOG = logging.getLogger('jbot')
LOG.setLevel(logging.INFO)
LOG.info("Starting my jbot !")


def get_my_planets():
    """Returns only my planets"""
    x = []
    for planet in all_planets:
        if planet.is_owned() and game_map.my_id == planet.owner.id:
            x.append(planet)
    return x


def get_average_size_of_my_planets():
    all_sizes_added = 0
    average_size = 0

    for planet in my_planets:
        all_sizes_added += planet.radius

    if len(my_planets):
        average_size = all_sizes_added / len(my_planets)
    return average_size


def get_nearest_unowned_planet_for_ship(myship):
    """Get the nearest unowned planet for the passed in ship

    Args:
        game_map: halite game_map instance
        myship: any ship

    Returns:
        Planet: instance of a planet

    """
    entities_by_distance = game_map.nearby_entities_by_distance(myship)
    for distance in sorted(entities_by_distance):
        entities = entities_by_distance[distance]
        for entity in entities:
            if isinstance(entity, hlt.entity.Planet):
                if not entity.is_owned():
                    return entity


def get_nearest_unowned_outer_planet_for_ship(myship):
    """Get the nearest unowned outer planet for the passed in ship

    Args:
        game_map: halite game_map instance
        myship: any ship

    Returns:
        Planet: instance of a planet

    """
    entities_by_distance = game_map.nearby_entities_by_distance(myship)
    for distance in sorted(entities_by_distance):
        entities = entities_by_distance[distance]
        for entity in entities:
            if entity in all_outer_planets:
                if not entity.is_owned():
                    return entity


def get_nearest_enemy_planet(myship):
    """Get nearest enemy planet

    Args:
        myship: any ship

    Returns:
        Planet: instance of a planet

    """
    entities_by_distance = game_map.nearby_entities_by_distance(myship)
    for distance in sorted(entities_by_distance):
        entities = entities_by_distance[distance]
        for entity in entities:
            if isinstance(entity, hlt.entity.Planet):
                if entity.is_owned() and entity.owner.id != game_map.my_id:
                    return entity
    return []


def get_nearest_notfull_planet_i_own_for_ship(myship):
    """Get the nearest planet owned by me for the passed in ship

    Args:
        game_map: halite game_map instance
        myship: any ship

    Returns:
        Planet: instance of a planet that isn't full

    """
    # Get Tuple of Tuples representing Not Full Planets I own in (distance, radius)
    average_size_of_my_planets = get_average_size_of_my_planets()
    for planet in my_planets:
        if not planet.is_full() and planet.radius >= average_size_of_my_planets:
            return planet

    # Otherwise, lets just get the closest planet...
    entities_by_distance = game_map.nearby_entities_by_distance(myship)
    for distance in sorted(entities_by_distance):
        entities = entities_by_distance[distance]
        for entity in entities:
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
    three_planets = []
    for distance in sorted(entities_by_distance):
        entities = entities_by_distance[distance]
        for entity in entities:
            if isinstance(entity, hlt.entity.Planet):
                if not entity.is_owned():
                    three_planets.append(entity)
                    if len(three_planets) == 3:
                        three_planets.sort(key=lambda x: x.radius, reverse=True)
                        LOG.critical(three_planets)
                        return three_planets[0]
    if len(three_planets):
        return three_planets[0]
    return False


def get_nearest_enemy_ship(myship, leader_only=False):
    """Get the nearest enemy ship

    Args:
        myship: One of my ships
        leader_only (bool): If True, only return the nearest LEADER ship

    Returns:
        htl.entity.Ship: Nearest enemy ship
    """
    entities_by_distance = game_map.nearby_entities_by_distance(myship)
    for distance, entity_list in sorted(entities_by_distance.items()):
        for entity in entity_list:
            if isinstance(entity, hlt.entity.Ship):
                if entity.owner != myship.owner:
                    if leader_only and entity.owner.id == leader:
                        return entity
                    if not leader_only:
                        return entity


def get_nearby_enemy_docker(myship):
    """Check for nearby enemy docking ships

    Args:
        myship (Ship):

    Returns:

    """
    for player in all_players:
        playerid = player.id
        player_ships = player.all_ships()
        player_ships.sort(key=lambda x: myship.calculate_distance_between(x))
        if playerid != game_map.my_id:
            for enemy_ship in player_ships:
                if enemy_ship.docking_status != enemy_ship.DockingStatus.UNDOCKED and myship.calculate_distance_between(enemy_ship) <= 12:
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


def go_to_nearest_enemy_ship(myship, leader_only=False):
    """Go to the nearest enemy ship (attack)

    Args:
        myship:
        leader_only (bool): If True, only go to the nearest enemy ship of the leader

    Returns:
        bool: if action was successful

    """
    nearest_enemy_ship = get_nearest_enemy_ship(myship, leader_only)
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


def get_all_outer_planets():
    """ Returns a list of all outer planets

    Returns:
        list[hlt.entity.Planet]: Only Outer Planets
    """
    high_end_percent = .34
    low_end_percent = .66
    x_must_be_gt = game_map.width * high_end_percent
    x_must_be_lt = game_map.width * low_end_percent
    y_must_be_gt = game_map.height * high_end_percent
    y_must_be_lt = game_map.height * low_end_percent
    the_outer_planets = []
    for planet in all_planets:
        if not planet.is_owned():
            if planet.x >= x_must_be_gt or planet.x <= x_must_be_lt or planet.y >= y_must_be_gt or planet.y <= y_must_be_lt:
                the_outer_planets.append(planet)
    return the_outer_planets


def general_attack(myship, attack_planet=False, closest_point=True):
    """This is my default attack mode.  Tweak as necessary.

    Args:
        myship:
        attack_planet (bool): Should I attack a planet instead?
        closest_point (bool): Closest point, or straight in?

    Returns:
        bool: True if action was successful
    """
    if attack_planet:
        nearest_enemy_planet = get_nearest_enemy_planet(myship)
        if nearest_enemy_planet:
            if closest_point:
                target = myship.closest_point_to(nearest_enemy_planet)
            else:
                target = nearest_enemy_planet
            navigate_command = myship.navigate(
                target,
                game_map,
                speed=int(hlt.constants.MAX_SPEED),
                max_corrections=18,
                angular_step=5,
                ignore_ships=False,
                ignore_planets=False)
            if navigate_command:
                command_queue.append(navigate_command)
                LOG.info('SHIP %s is ATTACKING PLANET %s', myship.id, nearest_enemy_planet.id)
                return True
    else:
        dist_ratio = 1  # How much further will you go to attack the leader?  Example:  3x
        nearest_leader_ship = get_nearest_enemy_ship(myship, leader_only=True)
        nearest_enemy_ship = get_nearest_enemy_ship(myship, leader_only=False)
        dist_to_leader_ship = nearest_leader_ship.calculate_distance_between(myship)
        dist_to_enemy_ship = nearest_enemy_ship.calculate_distance_between(myship)

        if nearest_enemy_ship == nearest_leader_ship:
            ship_to_attack = nearest_enemy_ship
        elif dist_to_leader_ship / dist_to_enemy_ship <= dist_ratio:
            # basically, if leader ship is less than dist_ratio times further away, hit the leader.
            ship_to_attack = nearest_leader_ship
            LOG.info('General Attack: Hitting Leader Due to Distance Override!')
        else:
            ship_to_attack = nearest_enemy_ship
        navigate_command = myship.navigate(
            myship.closest_point_to(ship_to_attack),
            game_map,
            speed=int(hlt.constants.MAX_SPEED),
            max_corrections=18,
            angular_step=5,
            ignore_ships=False,
            ignore_planets=False)
        if navigate_command:
            command_queue.append(navigate_command)
            LOG.info('SHIP %s is ATTACKING enemy ship %s', myship.id, ship_to_attack.id)
            return True
    return False


def general_expansion(myship):
    """This is what a ship should do if it should be expanding.

    Args:
        myship: a Ship instance.

    Returns:
        bool: True if action is successful
    """
    # GO TO MY NEAREST NOT FULL BIG PLANET AND DOCK
    planet_i_own = get_nearest_notfull_planet_i_own_for_ship(myship)
    unowned_planet = get_nearest_unowned_planet_for_ship(myship)
    outer_planet = get_nearest_unowned_outer_planet_for_ship(myship)

    if planet_i_own:
        best_planet = planet_i_own
    elif outer_planet:
        best_planet = outer_planet
        LOG.info('Overriding best planet to OUTER planet %s', outer_planet.id)
    elif unowned_planet:
        best_planet = unowned_planet
    else:
        # NOWHERE TO EXPAND TO, SOMETHING ELSE NEEDS TO HAPPEN
        return False

    if go_to_and_dock_at_planet(myship, best_planet, check_for_enemies=True):
        ships_expanding.append(myship)
        if best_planet.id in expansion_tracker.keys():
            expansion_tracker[best_planet.id].append(myship.id)
        else:
            expansion_tracker[best_planet.id] = [myship.id]
        LOG.info('EXPANSION TRACKER: %s', expansion_tracker)
        return True
    return False


def is_planet_expansion_full(some_planet):
    """For some_planet, check to see if we're already sending enough ships there.

    Args:
        some_planet (hlt.entity.Planet):

    Returns:
        bool: True if expansion slots full, False otherwise
    """
    if some_planet.id not in expansion_tracker.keys():
        return False
    if len(expansion_tracker[some_planet.id]) >= some_planet.num_docking_spots:
        return True
    return False


def go_to_and_dock_at_planet(myship, some_planet, travel_speed=hlt.constants.MAX_SPEED, check_for_enemies=True):
    if myship.can_dock(some_planet) and not some_planet.is_full():
        if check_for_enemies:
            nearest_enemy = get_nearest_enemy_ship(myship, leader_only=False)
            if myship.calculate_distance_between(nearest_enemy) >= 15:
                LOG.info('SHIP %s is docking at planet %s', myship.id, some_planet.id)
                command_queue.append(myship.dock(some_planet))
                return True
            else:
                LOG.info('SHIP %s NOT docking at planet %s due to nearby enemy ship %s', myship.id, some_planet.id, nearest_enemy.id)
        else:
            LOG.info('SHIP %s is docking at planet %s', myship.id, some_planet.id)
            command_queue.append(myship.dock(some_planet))
            return True

    elif not some_planet.is_full() and not is_planet_expansion_full(some_planet):
        navigate_command = myship.navigate(
            myship.closest_point_to(some_planet),
            game_map,
            speed=travel_speed,
            ignore_ships=False,
            max_corrections=18,
            angular_step=5)
        if navigate_command:
            LOG.info('SHIP %s going to planet %s', myship.id, some_planet.id)
            command_queue.append(navigate_command)
            return True
    return False


def go_to_specific_ship(myship, some_ship):
    navigate_command = myship.navigate(
        myship.closest_point_to(some_ship),
        game_map,
        speed=hlt.constants.MAX_SPEED,
        ignore_ships=False,
        max_corrections=18,
        angular_step=5)
    if navigate_command:
        LOG.info('SHIP %s going to attack specific ship %s', myship.id, some_ship.id)
        command_queue.append(navigate_command)
        return True
    return False


def find_leader():
    """Determine leader based on shipcount

    Returns:

    """
    x = {}

    for player in all_players:
        playerid = player.id
        player_ships = player.all_ships()
        player_planets = 0
        for planet in all_planets:
            if planet.is_owned() and player.id == planet.owner:
                player_planets += planet.radius
        healthy_player_ships = [s for s in player_ships if s.health > 0]
        ship_count = len(healthy_player_ships)
        if playerid != game_map.my_id:
            x[playerid] = ship_count + player_planets
    LOG.info('LEADER LIST: %s', x)
    leader = max(x, key=x.get)
    LOG.info('LEADER = %s', leader)
    return leader


def get_enemy_ships_near_entity(myentity, filter_distance):
    """

    Args:
        myentity (Entity): any entity (ship or planet)
        filter_distance: Radius to check within for enemy ships

    Returns:
        list: of enemy Ships
    """
    ship_list = []
    entities_by_distance = game_map.nearby_entities_by_distance(myentity)
    for distance, entity_list in sorted(entities_by_distance.items()):
        for entity in entity_list:
            if isinstance(entity, hlt.entity.Ship):
                if entity.owner != myentity.owner:
                    if distance <= filter_distance:
                        ship_list.append(entity)
    return ship_list


def update_defend_list():
    """Updates defend_against_ships global."""
    # This for loop removes any ship that died from defend_against_ships
    for some_ship in defend_against_ships:
        if some_ship not in all_ships:
            defend_against_ships.remove(some_ship)

    # This for loop updates defend_against_ships for any new ships
    # First loop over my ships, and find DOCKED/DOCKING Ships.
    # Then find nearby enemy ships that may be coming to attack my docked ships.
    # Update the defend_against_ships list
    for myship in my_ships:
        if myship.docking_status != myship.DockingStatus.UNDOCKED:
            for enemy_ship in get_enemy_ships_near_entity(myship, 30):
                if enemy_ship.docking_status == enemy_ship.DockingStatus.UNDOCKED and enemy_ship not in defend_against_ships:
                    defend_against_ships.append(enemy_ship)


def get_my_closest_ships_to_ship(some_ship, num_ships, filter_distance):
    """

    Args:
        some_ship: enemy ship
        num_ships: number of my ships to find nearby
        filter_distance: max distance to look within

    Returns:
        list: of my Ships
    """
    my_closest_ships = []
    entities_by_distance = game_map.nearby_entities_by_distance(some_ship)
    for distance, entity_list in sorted(entities_by_distance.items()):
        for entity in entity_list:
            if isinstance(entity, hlt.entity.Ship):
                if entity.owner.id == game_map.my_id:
                    if distance <= filter_distance:
                        if entity not in ships_with_actions:
                            my_closest_ships.append(entity)
                            if len(my_closest_ships) == num_ships:
                                return my_closest_ships
                    else:
                        # This is to save processing time, we're already passed the distance limit.
                        return my_closest_ships
    return my_closest_ships


try:
    TURN = 0
    initial_planet = None
    defend_against_ships = []
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
        all_planets = game_map.all_planets()
        all_players = game_map.all_players()
        all_outer_planets = get_all_outer_planets()
        all_ships = []
        for player in all_players:
            all_ships.extend([x for x in player.all_ships()])
        my_planets = get_my_planets()
        leader = find_leader()
        my_undocked_ships = []  # Obvious
        for ship in my_ships:
            if ship.docking_status == ship.DockingStatus.UNDOCKED:
                my_undocked_ships.append(ship)
        ships_with_actions = []  # Tracks ships that already have priority actions (defending usually)
        update_defend_list()
        ships_expanding = []  # List of ships current expanding (used for ratio logic)
        expansion_tracker = {}  # Tracks My+Neutral planets and how many ships are going to them.
        LOG.info('DEFEND AGAINST: %s', [x.id for x in defend_against_ships])

        # PRIORITY DEFENSE ACTIONS
        for enemy_ship in defend_against_ships:
            # find my closest x ships to this ship
            my_closest_ships = get_my_closest_ships_to_ship(enemy_ship, 2, 60)
            for close_ship in my_closest_ships:
                if close_ship not in ships_with_actions:
                    if close_ship.docking_status == close_ship.DockingStatus.UNDOCKED:
                        if go_to_specific_ship(close_ship, enemy_ship):
                            LOG.info('SHIP %s GOT PRIORITY DEFENSE AGAINST SHIP %s', close_ship, enemy_ship)
                            ships_with_actions.append(close_ship)

        LOG.info('PRIORITY ACTIONS: %s', ships_with_actions)

        # For every ship that I control
        for ship in my_ships:

            # TIMEOUT PROTECTION
            if time.time() > end_time:
                LOG.warning('BAILING TURN FOR TIMEOUT')
                continue  # break out of the per ship loop, which should send our commands

            # SKIP IF SHIP ALREADY HAS PRIORITY ACTION (LIKE DEFENSE)
            if ship in ships_with_actions:
                continue

            # SHIP IS DOCKED, DO NOTHING
            if ship.docking_status != ship.DockingStatus.UNDOCKED:
                LOG.debug('SHIP %s is docked, skipping.', ship.id)
                # Skip this ship
                continue

            if not initial_planet and TURN is 1:
                initial_planet = get_biggest_early_planet_for_ship(ship)
                LOG.critical('GETTING INITIAL PLANET: id %s', initial_planet.id)

            # ATTACK ENEMY DOCKERS
            enemy_docking_ship = get_nearby_enemy_docker(ship)
            if enemy_docking_ship:
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

            if TURN <= 10:
                speed = hlt.constants.MAX_SPEED
                if go_to_and_dock_at_planet(ship, initial_planet, travel_speed=speed):
                    continue

            if len(my_undocked_ships):
                ratio_expanding = len(ships_expanding) / len(my_undocked_ships)
            else:
                ratio_expanding = 0
            # Generally expand with some percentage of ships.
            if general_expansion(ship):
                continue

            if ship.health <= 64:
                if general_expansion(ship):
                    continue
            if TURN <= 180:
                # have some ships group up on an enemy planet
                if ship.id % 5 <= 2:
                    if general_attack(ship, attack_planet=True, closest_point=True):
                        continue

            if general_attack(ship, attack_planet=False):
                continue
            LOG.warning('SHIP %s NO COMMAND GIVEN', ship.id)

        # Send our set of commands to the Halite engine for this turn
        game.send_command_queue(command_queue)
        # TURN END
    # GAME END
except Exception as e:
    LOG.critical(e)
    LOG.critical(traceback.format_exc())
