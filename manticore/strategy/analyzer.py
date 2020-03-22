from enum import Enum

from gosling_utils.utils import argmax, side, argmin


class Objective(Enum):
    GO_FOR_IT = 0
    FOLLOW_UP = 1
    ROTATE_BACK_OR_DEF = 2
    UNKNOWN = 3


class GameAnalyzer:
    def __init__(self):
        self.closest_foe_to_ball = None
        self.closest_foe_to_ball_dist = 99999
        self.car_with_possession = None
        self.ally_with_possession = None
        self.foe_with_possession = None

    def update(self, agent):
        # Find closest foe to ball
        self.closest_foe_to_ball = None
        self.closest_foe_to_ball_dist = 99999
        for foe in agent.foes:
            dist = foe.location.dist(agent.ball.location)
            if dist < self.closest_foe_to_ball_dist:
                self.closest_foe_to_ball = foe
                self.closest_foe_to_ball_dist = dist

        # Possession
        self.car_with_possession = None
        self.ally_with_possession = None
        self.foe_with_possession = None
        for car in agent.all_cars:
            point_in_front = car.location + car.orientation.forward * (car.velocity.magnitude())
            ball_point_dist = agent.ball.location.dist(point_in_front)
            dist01 = 1500 / (1500 + ball_point_dist)  # Halves every 1500 uu of dist
            car_to_ball = agent.ball.location - car.location
            car_to_ball_unit, car_ball_dist = car_to_ball.normalize(True)
            in_front01 = car.orientation.forward.dot(car_to_ball_unit)
            car.possession = dist01 * in_front01
            if self.car_with_possession is None or car.possession > self.car_with_possession.possession:
                self.car_with_possession = car
            if car.team == agent.team and (self.ally_with_possession is None or car.possession > self.ally_with_possession.possession):
                self.ally_with_possession = car
            if car.team != agent.team and (self.foe_with_possession is None or car.possession > self.foe_with_possession.possession):
                self.foe_with_possession = car

        # Objectives
        for car in agent.all_cars:
            car.last_objective = car.objective
            car.objective = Objective.UNKNOWN
        attacker, attacker_score = argmax(agent.friends + [agent.me],
                                          lambda ally: (0.1 if ally.last_objective == Objective.GO_FOR_IT else 0)
                                                       + ally.possession * (10_000 - side(ally.team) * ally.location.y) / 20_000)
        attacker.objective = Objective.GO_FOR_IT
        follower_expected_location = (agent.ball.location + agent.friend_goal.location) * 0.5
        follower, follower_score = argmin([ally for ally in agent.friends + [agent.me] if ally.objective == Objective.UNKNOWN],
                                          lambda ally: (-400 if ally.last_objective == Objective.FOLLOW_UP else 0)
                                                        + ally.location.dist(follower_expected_location))
        follower.objective = Objective.FOLLOW_UP
        for car in agent.friends + [agent.me]:
            if car.objective == Objective.UNKNOWN:
                car.objective = Objective.ROTATE_BACK_OR_DEF
        if agent.me.objective != agent.me.last_objective:
            agent.clear()
