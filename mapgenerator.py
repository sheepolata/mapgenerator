#!/usr/bin/env python
#-*- coding: utf-8 -*-

import pygame
from pygame.locals import *
import random
import sys
import time
import numpy as np
from screeninfo import get_monitors
import os
import operator
import colour

import tile_info
import utils
import parameters
import pathfinding as pf

class MapTile(pygame.sprite.Sprite):
    def __init__(self, x, y, w, h, index):
        super(MapTile, self).__init__()
        self.x = x
        self.y = y
        self.h = h
        self.w = w

        self.index = index

        self.caravan = []
        self.village = None
        self.river = False

        # self.color = (int(random.random() * 255), int(random.random() * 255), int(random.random() * 255))
        self.reset()

        self.image = pygame.Surface([self.w, self.h])
        self.image.fill(self.color)
        self.rect = pygame.Rect(self.x, self.y, self.w, self.h)

        self.distance_to_neighbours = {}

        self.selected = False
        self.effect = True
        self.randomEffectSettings()

        self.score_computed = False
        self.score = 0.0
        self.detail_score = ""

    def reset(self):
        # t = time.time()
        self.heat_color_score = tile_info.EMPTY
        self.heat_color_cost = tile_info.EMPTY
        if parameters.getInstance().DEFAULT_DRAWING:
            self.color = random.choice(parameters.getInstance().COLOR_PALETTE)
        else:
            # print(parameters.getInstance().COLOR_PALETTE)
            # print(parameters.getInstance().COLOR_PROBA)
            # self.color = tuple(np.random.choice(np.array(parameters.getInstance().COLOR_PALETTE,dtype='i,i,i'), p=parameters.getInstance().COLOR_PROBA))
            self.color = utils.weighted_choice(parameters.getInstance().BIOME)
        self.color_fixed = False
        self.caravan = []
        self.river = False
        self.village = None
        # print (time.time() - t)

    def getPose(self):
        return (self.x, self.y)

    def update(self):
        if not self.color_fixed:
            neighs = utils.getNeighboursFrom1D(self.index, parameters.getInstance().MAP_TILES, parameters.getInstance().CANVAS_WIDTH, parameters.getInstance().CANVAS_HEIGHT)
            
            self.color = random.choice([c.color for c in neighs])

            self.randomEffectSettings()
        else:
            pass

        self.image.fill(self.color)

    def get2DCoord(self):
        #k =     i * width + j. Thus i = k / width, j = k % width
        return (self.index / parameters.getInstance().CANVAS_WIDTH, self.index%parameters.getInstance().CANVAS_WIDTH)

    def randomEffectSettings(self):
        self.effect_random_placement = (random.randrange(-4, 4), random.randrange(-4, 4))
        
        self.nb_grass = random.randint(2,4)
        self.grass_coord = []
        self.grass_size  = []
        for i in xrange(1,self.nb_grass):
            self.grass_coord.append((random.randrange(-6, 6), random.randrange(-6, 6)))
            self.grass_size.append(random.randint(2, 5))

        self.effect_size = 0
        if self.getType() == "mountain":
            self.effect_size = random.randrange(5, 8)
        if self.getType() == "forest":
            self.effect_size = random.randrange(2, 5)
        if self.getType() == "hill":
            self.effect_size = random.randrange(2, 6)
            

    def draw(self, screen, _FAST_DISPLAY):
        # pygame.draw.rect(screen, self.color, self.rect)
        screen.blit(self.image, self.rect)
        if self.selected:
            pygame.draw.rect(screen, tile_info.RED, self.rect, 2)
            # print(self.toString())
        if self.effect and not _FAST_DISPLAY:
            if self.getType() == "mountain":
                pygame.draw.polygon(screen, 
                                    tile_info.BROWN_EFFECT, 
                                    utils.trianglePointsFromCenter((self.rect.center[0] + self.effect_random_placement[0], self.rect.center[1] + self.effect_random_placement[1]), self.effect_size))
            if self.getType() == "forest":
                pygame.draw.polygon(screen, 
                                    tile_info.GREEN_3, 
                                    utils.trianglePointsFromCenter((self.rect.center[0] + self.effect_random_placement[0], self.rect.center[1] + self.effect_random_placement[1]), self.effect_size))
            if self.getType() == "hill":
                pygame.draw.polygon(screen, 
                                    tile_info.OLIVE_EFFECT, 
                                    utils.roughSemicirclePointsFromCenter((self.rect.center[0] + self.effect_random_placement[0], self.rect.center[1] + self.effect_random_placement[1]), self.effect_size))
            if self.getType() == "plain":
                for i in xrange(0,self.nb_grass-1):
                    pygame.draw.line(screen,
                                    tile_info.GREEN_EFFECT,
                                    (self.rect.center[0] + self.grass_coord[i][0], self.rect.center[1] + self.grass_coord[i][1]),
                                    (self.rect.center[0] + self.grass_coord[i][0], self.rect.center[1] + self.grass_coord[i][1] + self.grass_size[i])
                                    )

    def draw_heatmap(self, alpha_surface, _type=0):
        if _type == 0:
            pygame.draw.rect(alpha_surface, self.heat_color_score, self.rect)
        if _type == 1:
            pygame.draw.rect(alpha_surface, self.heat_color_cost, self.rect)

    def getType(self):
        return tile_info.COLOR_TO_TYPE[self.color]

    def getCost(self):
        return tile_info.TYPE_TO_COST[self.getType()] * ((1.0+(0.5*self.river)) if self.getType() not in tile_info.WATER_TYPES else 1.0)

    def collidepoint(self, pos):
        return self.rect.collidepoint(pos)

    def toString(self):
        return ("({}, {}) {} ({})"
                    .format(self.x, self.y, self.getType(), self.getCost()))

    def evaluate(self, forced=False):
        if not self.score_computed or forced:
            # if forced: print("FORCED EVALUATION")
            vinicity = utils.getTilesInRadius(self, radius=2, include_self=False)
            vinicity_type = [x.getType() for x in vinicity]
            freq = utils.countFreq(vinicity_type)
            #1.0 MAX => MAX Diversity
            diversity = float(len(freq.keys())) / float(len(tile_info.USED_TYPES))

            neighbouring_river = sum([x.river*tile_info.SCORE_NEIGH_RIVER for x in vinicity])
            # if neighbouring_river != 0.0: print(neighbouring_river)

            if self.getType() in ["shallow_water", "deep_water", "city"] or set(["city"]).intersection(set(freq.keys())) != set([]):
                self.score = 0.0
                self.score_computed = True
                return self.score
            
            score = 0.0

            for t in tile_info.USED_TYPES:
                if t not in freq.keys():
                    freq[t] = 0.0


            score = (   tile_info.TYPE_TO_SCORE[self.getType()]
                        +
                        (tile_info.TYPE_TO_WEIGTH_SCORE["plain"]*freq["plain"] 
                            + tile_info.TYPE_TO_WEIGTH_SCORE["shallow_water"]*freq["shallow_water"] 
                            + tile_info.TYPE_TO_WEIGTH_SCORE["forest"]*freq["forest"] 
                            + tile_info.TYPE_TO_WEIGTH_SCORE["hill"]*freq["hill"] 
                            + tile_info.TYPE_TO_WEIGTH_SCORE["deep_water"]*freq["deep_water"]
                            + tile_info.TYPE_TO_WEIGTH_SCORE["desert"]*freq["desert"] 
                            + tile_info.TYPE_TO_WEIGTH_SCORE["mountain"]*freq["mountain"] 
                            + tile_info.TYPE_TO_WEIGTH_SCORE["city"]*(1.0 if freq["city"] > 0 else 0.0)
                        )
                        +
                        (diversity if diversity <= 0.5 else (1.0 - diversity)) * 2.0
                        +
                        self.river * tile_info.SCORE_RIVER + neighbouring_river
                    )

            self.score = max(0.0, round(score, 4))
            self.score_computed = True

            self.detail_score = "{}({}, {}) + ({}*{}(plain)+{}*{}(shallow_water)+{}*{}(forest)+{}*{}(hill)+{}*{}(deep_water)+{}*{}(desert)+{}*{}(mountain)+{}*{}(city)) + {}(diversity) + {}*{}+{}(rivers) = {}".format(
                                    tile_info.TYPE_TO_SCORE[self.getType()]
                                    , self.getType()
                                    , self.getPose()
                                    , tile_info.TYPE_TO_WEIGTH_SCORE["plain"], freq["plain"] 
                                    , tile_info.TYPE_TO_WEIGTH_SCORE["shallow_water"], freq["shallow_water"] 
                                    , tile_info.TYPE_TO_WEIGTH_SCORE["forest"], freq["forest"] 
                                    , tile_info.TYPE_TO_WEIGTH_SCORE["hill"], freq["hill"] 
                                    , tile_info.TYPE_TO_WEIGTH_SCORE["deep_water"], freq["deep_water"]
                                    , tile_info.TYPE_TO_WEIGTH_SCORE["desert"], freq["desert"] 
                                    , tile_info.TYPE_TO_WEIGTH_SCORE["mountain"], freq["mountain"] 
                                    , tile_info.TYPE_TO_WEIGTH_SCORE["city"], (1.0 if freq["city"] > 0 else 0.0)
                                    , (diversity if diversity <= 0.5 else (1.0 - diversity)) 
                                    , self.river, tile_info.SCORE_RIVER, neighbouring_river
                                    , self.score
                                    )
            # if freq["city"] > 0.0 :print(self.detail_score)
            return self.score
        else:
            return self.score

class Caravan(pygame.sprite.Sprite):
    def __init__(self, _tile, population_count=-1, name="caravan"):
        # Call the parent class (Sprite) constructor
        super(Caravan, self).__init__()

        self.tile = _tile
        self.tile.caravan.append(self)
        self.x = self.tile.rect.center[0]
        self.y = self.tile.rect.center[1]

        if population_count == -1:
            self.population_count = int(random.random()*(parameters.getInstance().MAX_POP_PER_CARAVAN - parameters.getInstance().MIN_POP_PER_CARAVAN) + parameters.getInstance().MIN_POP_PER_CARAVAN)
        else:
            self.population_count = population_count

        # self.speed_modifier =  1.0 + round(utils.normalise(self.population_count, parameters.getInstance().MIN_POP_PER_CARAVAN*0.8, parameters.getInstance().MAX_POP_PER_CARAVAN*1.2), 3)
        # self.speed_modifier = round(0.25 + random.random()*0.50, 2)
        self.speed_modifier = 0.05

        # self.speed_modifier = 1 + round(self.population_count / parameters.getInstance().MAX_POP_PER_CARAVAN, 2)

        self.name = name

        self.selected = False

        # Create an image of the block, and fill it with a color.
        # This could also be an image loaded from the disk.
        # self.image = pygame.Surface([width, height])
        # self.image.fill(color)
        self.image = pygame.image.load(os.path.join('Sprites', 'caravan.png'))
        # self.image = pygame.transform.scale(self.image, (parameters.getInstance().MAP_TILES[0].w, parameters.getInstance().MAP_TILES[0].h))

        # Fetch the rectangle object that has the dimensions of the image
        # Update the position of this object by setting the values of rect.x and rect.y
        self.rect = pygame.Rect(self.x-(self.image.get_rect().size[0]/2), 
                                self.y-(self.image.get_rect().size[1]/2),
                                self.image.get_rect().size[0],
                                self.image.get_rect().size[1])
        # self.rect = self.image.get_rect()

        self.destination = None
        self.route = []

        self.tile_goto = None
        self.walking_left = 0

        self.vision_range = 4
        self.visible_vinicity = []
        self.explored_tiles = []
        self.possible_settlement_tile = []
        self.previous_possible_settlement_tile = []
        self.location_memory = 10
        self.map_percent = 0.15

        self.settling = False
        self.settlement_tile = None
        self.last_check = False

        self.score_thresh = (
                            utils.clamp(utils.normalise(self.population_count, 
                                            parameters.getInstance().MIN_POP_PER_CARAVAN*0.4, 
                                            parameters.getInstance().MAX_POP_PER_CARAVAN*1.2)
                            , 0.2, 0.9)
                            * parameters.getInstance().MAX_TILE_SCORE
                            )
        # print("{} ==>  {} < {} < {}".format(self.score_thresh, parameters.getInstance().MIN_POP_PER_CARAVAN, self.population_count, parameters.getInstance().MAX_POP_PER_CARAVAN))

    #Choose the destination of the caravan if None
    def choose_destination(self, goal=None, forbidden=[]):
        if goal == None:
            self.destination = utils.getRandomTile(tilemap=list(set(parameters.getInstance().MAP_TILES).symmetric_difference(set(self.explored_tiles))))
        else:
            self.destination = goal
        self.route = pf.astar(self.tile, self.destination, forbidden=[])

    #Move to the next tile in the route or choose to change course or action
    def next_step(self, _step):
        self.visible_vinicity = utils.getTilesInRadius(self.tile, self.vision_range)

        if self.destination == None or len(self.route) == 0:
            if not self.settling:
                self.choose_destination()
            elif self.old_settlement_tile != self.settlement_tile and self.previous_possible_settlement_tile != self.possible_settlement_tile:
                self.lastCheckBeforeSettling()
            else:
                self.makeVillage()
                return

        if self.tile_goto == None and self.route != []:
            self.tile_goto = self.route[0]
            self.walking_left = max(1, int(round(self.tile_goto.getCost() * (self.speed_modifier) * 2, 2)))

        if self.tile_goto != None and self.walking_left > 0:
            self.walking_left -= 1
            if self.walking_left <= 0:
                self.set_next_tile()
                self.tile_goto = None

        if _step%10:
            self.scanVinicity()
        
        self.settle()

    def makeVillage(self):
        print("Make Village")
        village = Village("Village"+self.name[7:], self.tile, self.population_count)
        self.self_destroy()
        print("Make Village ==> END")

    def self_destroy(self):
        self.tile.caravan.remove(self)
        parameters.getInstance().CARAVAN_LIST.remove(self)

    def lastCheckBeforeSettling(self):
        print("Last check before settling")
        self.settling = False
        self.scanVinicity()
        self.settle()
        print("Last check before settling ==> END")

    def settle(self):
        if not self.settling:
            if (float(len(self.explored_tiles))/float(len(parameters.getInstance().MAP_TILES))) > self.map_percent and len(self.possible_settlement_tile) >= self.location_memory:
                print("{} is settling!".format(self.name))

                self.old_settlement_tile = self.settlement_tile

                # self.settlement_tile = max(self.possible_settlement_tile, key=operator.methodcaller('evaluate'))
                _sum = 0
                for st in self.possible_settlement_tile:
                    _sum += st.evaluate()
                _dict = {}
                for st in self.possible_settlement_tile:
                    _dict[st] = st.evaluate() / _sum
                self.settlement_tile = utils.weighted_choice(_dict)

                self.settling = True
            elif len(self.possible_settlement_tile) >= self.location_memory and (float(len(self.explored_tiles))/float(len(parameters.getInstance().MAP_TILES))) > 0.75:
                self.self_destroy()
        elif self.destination != self.settlement_tile:
            self.choose_destination(goal=self.settlement_tile)

    def scanVinicity(self):
        # print("TEST ", operator.methodcaller('evaluate')(parameters.getInstance().MAP_TILES[0]))
        min_thresh_tile = None
        self.previous_possible_settlement_tile = self.possible_settlement_tile

        if self.possible_settlement_tile != []:
            min_thresh_tile = min(self.possible_settlement_tile, key=operator.methodcaller('evaluate'))

        for v in self.visible_vinicity:
            if v not in self.explored_tiles:
                self.explored_tiles.append(v)
            if v in self.possible_settlement_tile:
                continue
            if v.evaluate() >= self.score_thresh:
                if (len(self.possible_settlement_tile) >= self.location_memory):
                        if v.evaluate() > min(self.possible_settlement_tile, key=operator.methodcaller('evaluate')).evaluate():
                            self.possible_settlement_tile[self.possible_settlement_tile.index(min(self.possible_settlement_tile, key=operator.methodcaller('evaluate')))] = v
                else:
                    self.possible_settlement_tile.append(v)
                # if len(self.possible_settlement_tile) > self.location_memory:
                #     self.possible_settlement_tile = self.possible_settlement_tile[1:]



    def set_next_tile(self):
        self.route = self.route[1:]
        self.tile.caravan.remove(self)
        self.tile = self.tile_goto
        self.tile.caravan.append(self)

        self.x = self.tile.rect.center[0]
        self.y = self.tile.rect.center[1]
        self.rect = pygame.Rect(self.x-(self.image.get_rect().size[0]/2), 
                                self.y-(self.image.get_rect().size[1]/2),
                                self.image.get_rect().size[0],
                                self.image.get_rect().size[1])

    def collidepoint(self, c):
        self.rect.collidepoint(c)

    def draw(self, screen, local_info, alpha):
        # pygame.draw.circle(screen, tile_info.WHITE, (self.x, self.y), 8)
        # pygame.draw.circle(screen, tile_info.BLACK, (self.x, self.y), 8, 4)
        if local_info or self.selected:
            if self.route != []:
                pygame.draw.lines(screen, tile_info.BLACK, False, [self.tile.rect.center] + [x.rect.center for x in self.route], 3)
                pygame.draw.lines(screen, tile_info.WHITE, False, [self.tile.rect.center] + [x.rect.center for x in self.route], 1)

            for t in [x for x in self.visible_vinicity if x != self.tile]:
                # t.draw_heatmap(alpha, _type=parameters.getInstance().HEATMAP_TYPE)
                pygame.draw.rect(alpha, tuple(list([t.heat_color_score[0], t.heat_color_score[1], t.heat_color_score[2]]) + [int(parameters.getInstance().HEATMAP_ALPHA/1.2)]), t.rect)
            for t in self.explored_tiles:
                pygame.draw.rect(alpha, tuple(list(tile_info.WHITE) + [parameters.getInstance().HEATMAP_ALPHA/1.5]), t.rect, 1)
                # pygame.draw.line(alpha, tuple(list(tile_info.WHITE) + [parameters.getInstance().HEATMAP_ALPHA/2]), self.rect.center, t.rect.center, 1)                
            for t in self.possible_settlement_tile:
                pygame.draw.rect(alpha, tuple(list(tile_info.MAGENTA) + [parameters.getInstance().HEATMAP_ALPHA]), t.rect, 2)
                # pygame.draw.line(alpha, tuple(list(tile_info.MAGENTA) + [parameters.getInstance().HEATMAP_ALPHA]), self.rect.center, t.rect.center, 3)                

        screen.blit(self.image, self.rect)
        if self.selected:
            pygame.draw.rect(screen, tile_info.RED, self.rect, 2)

class Migrant_Village(Caravan):
    """docstring for Migrants"""
    def __init__(self, _tile, population_count=-1, name="migrants_village"):
        super(Migrant_Village, self).__init__(_tile, population_count, name)
        
        _sum = 0
        for vil in parameters.getInstance().VILLAGE_LIST:
            _sum += vil.population_count
        _dict = {}
        for vil in parameters.getInstance().VILLAGE_LIST:
            _dict[vil] = float(vil.population_count) / float(_sum)
        self.village_to_go = utils.weighted_choice(_dict)

        # self.village_to_go = random.choice(parameters.getInstance().VILLAGE_LIST)

        self.population_count /= 10
        
    def choose_destination(self):
        # self.destination = utils.getRandomTile(tilemap=list(set(parameters.getInstance().MAP_TILES).symmetric_difference(set(self.explored_tiles))))
        self.destination = self.village_to_go.tile
        
        self.route = pf.astar(self.tile, self.destination, forbidden=[])
        
    def next_step(self):
        self.visible_vinicity = utils.getTilesInRadius(self.tile, self.vision_range)

        if self.tile.village != None and self.tile.village == self.village_to_go:
            self.integrate()
            return

        if self.destination == None or len(self.route) == 0:
            self.choose_destination()

        if self.tile_goto == None and self.route != []:
            self.tile_goto = self.route[0]
            self.walking_left = max(1, int(round(self.tile_goto.getCost() * (self.speed_modifier) * 2, 2)))

        if self.tile_goto != None and self.walking_left > 0:
            self.walking_left -= 1
            if self.walking_left <= 0:
                self.set_next_tile()
                self.tile_goto = None

    def integrate(self):
        self.village_to_go.population_count += self.population_count
        self.self_destroy()

    def self_destroy(self):
        self.tile.caravan.remove(self)
        parameters.getInstance().MIGRANTS_VILLAGE_LIST.remove(self)
    
    def draw(self, screen, local_info):
        screen.blit(self.image, self.rect)
        if local_info:
            if self.route != []:
                pygame.draw.lines(screen, tile_info.BLACK, False, [self.tile.rect.center] + [x.rect.center for x in self.route], 3)
                pygame.draw.lines(screen, tile_info.WHITE, False, [self.tile.rect.center] + [x.rect.center for x in self.route], 1)

class Emissary_Village(Migrant_Village):
    def __init__(self, _tile, village, population_count=10, name="emissary"):
        super(Emissary_Village, self).__init__(_tile, population_count, name)
        self.village = village
        self.village_to_go = None

        self.explored_tiles = []

        self.village.population_count -= self.population_count

        self.vision_range = 8
        self.speed_modifier = 0.1

        self.r = None

        parameters.getInstance().EMISSARY_VILLAGE_LIST.append(self)

    def draw(self, screen, local_info, alpha):
        pygame.draw.circle(screen, tile_info.BLACK, self.rect.center, 6)
        pygame.draw.circle(screen, tile_info.YELLOW_3, self.rect.center, 4)
        if local_info:
            pygame.draw.line(alpha, tuple(list(tile_info.WHITE)+[128]), self.tile.rect.center, self.village.tile.rect.center, 2)
            if self.route != []:
                    pygame.draw.lines(screen, tile_info.BLACK, False, [self.tile.rect.center] + [x.rect.center for x in self.route], 3)
                    pygame.draw.lines(screen, tile_info.WHITE, False, [self.tile.rect.center] + [x.rect.center for x in self.route], 1)
            if self.village_to_go != None:
                pygame.draw.line(alpha, tuple(list(tile_info.RED)+[128]), self.tile.rect.center, self.village_to_go.tile.rect.center, 2)

    def choose_destination(self):
        if self.village_to_go == None:
            self.destination = utils.getRandomTile(tilemap=list(set(parameters.getInstance().MAP_TILES).symmetric_difference(set(self.explored_tiles))))
        else:
            self.destination = self.village_to_go.tile
        
        self.route = pf.astar(self.tile, self.destination, forbidden=[])

    def next_step(self):
        self.visible_vinicity = utils.getTilesInRadius(self.tile, self.vision_range)
        self.scanVinicity()

        if self.tile.village != None and self.tile.village == self.village_to_go:
            self.integrate()
            return

        if self.destination == None or len(self.route) == 0:
            self.choose_destination()

        if self.tile_goto == None and self.route != []:
            self.tile_goto = self.route[0]
            self.walking_left = max(1, int(round(self.tile_goto.getCost() * (self.speed_modifier) * 2, 2)))

        if self.tile_goto != None and self.walking_left > 0:
            self.walking_left -= 1
            if self.walking_left <= 0:
                self.set_next_tile()
                self.tile_goto = None

    # self.routes           = []
    # self.known_cities     = []
    # self.connected_cities = []
    # self.noroute_cities   = []
    def integrate(self):
        self.village_to_go.population_count += self.population_count

        self.village.connected_cities.append(self.village_to_go)
        self.village_to_go.connected_cities.append(self.village)

        if(self.r == None):
            print("IN INTEGRATE: R == NONE ==> BUG")
        self.village.routes.append(self.r)
        self.village_to_go.routes.append(self.r.reversed())

        self.village.nb_emissary -= 1

        self.self_destroy()

    def self_destroy(self):
        self.tile.caravan.remove(self)
        parameters.getInstance().EMISSARY_VILLAGE_LIST.remove(self)

    def scanVinicity(self):
        if self.village_to_go != None:
            return

        if self.r == None:
            for v in self.visible_vinicity:
                if v not in self.explored_tiles:
                    self.explored_tiles.append(v)
                if v.village != None:
                    if (v.village == self.village 
                        or v.village in self.village.connected_cities 
                        or v.village in self.village.noroute_cities):
                        continue
                    else:
                        self.village_to_go = v.village
        elif self.r == None and self.village_to_go != None:
            self.r = Route(self.village.tile, self.village_to_go.tile)

        if self.r != None and self.r.possible():
            self.village_to_go = v.village
        else:
            print("R == NONE || R NOT POSSIBLE")
            self.village.noroute_cities.append(self.village_to_go)
            self.r = None

class Village(pygame.sprite.Sprite):
    """docstring for Village"""
    def __init__(self, name, tile, population_count):
        super(Village, self).__init__()
        self.name = name
        self.population_count = population_count
        self.tile = tile

        self.tile.village = self
        self.tile.color = tile_info.BLACK

        self.grow_rate = -1.0

        self.effect_random_placement = (random.randrange(-2, 2), random.randrange(-2, 2))
        self.effect_size = random.randrange(7, 9)

        self.rect = self.tile.rect

        self.routes           = []
        self.known_cities     = []
        self.connected_cities = []
        self.noroute_cities   = []

        if parameters.getInstance().VILLAGE_LIST != []:
            route_village = random.choice(parameters.getInstance().VILLAGE_LIST)
            self.routes.append(Route(self.tile, route_village.tile))



        parameters.getInstance().VILLAGE_LIST.append(self)

        # self.tile.evaluate(forced=True)
        computeHeatMap_Score(forced=True)

        self.nb_emissary = 0



    def new_grow_rate(self):
        self.grow_rate = random.random()*0.04 + 0.985

    def next_step(self, _step):
        if _step%(30*3) == 0:
            self.new_grow_rate()
            self.population_count = int(self.population_count*self.grow_rate)

        # if self.population_count >= 50 and self.nb_emissary == 0:
            # Emissary_Village(_tile=self.tile, village=self, name="emissary_"+self.name)
            # self.nb_emissary += 1




    def draw(self, screen, alpha, local_info, _FAST_DISPLAY=parameters.getInstance().FAST_DISPLAY):
        for r in self.routes:
            pygame.draw.lines(screen, tile_info.BLACK, False, [self.tile.rect.center] + [x.rect.center for x in r.route], 5)
            pygame.draw.lines(screen, tile_info.WHITE, False, [self.tile.rect.center] + [x.rect.center for x in r.route], 1)

        if not _FAST_DISPLAY:
            pygame.draw.polygon(screen, 
                        tile_info.GRAY_EFFECT, 
                        utils.trianglePointsFromCenter((self.rect.center[0] + self.effect_random_placement[0], self.rect.center[1] + self.effect_random_placement[1]), self.effect_size))

        if local_info:
            for t in utils.getTilesInRadius(self.tile, 2):
                pygame.draw.rect(alpha, tuple(list(tile_info.BLACK) + [parameters.getInstance().HEATMAP_ALPHA/2]), t.rect, 1)

class Route(object):
    def __init__(self, departure, arrival):
        super(Route, self).__init__()
        self.departure = departure
        self.arrival = arrival

        self.route = pf.astar(self.departure, self.arrival, forbidden=["shallow_water", "deep_water"])
        # if self.route == []:
        #     print("No route possible")

    def possible(self):
        return self.route != None

    def reversed(self):
        return Route(arrival, departure)
        


def computeHeatMap_Score(forced=False):
    print("Compute heat map (score)")

    red = colour.Color("red")
    colors = list(red.range_to(colour.Color("green"),20))
    colors = [tuple([int(x*255) for x in c.rgb]) for c in colors]

    d_values = {}
    for mt in parameters.getInstance().MAP_TILES:
        d_values[mt] = mt.evaluate(forced=forced)

    parameters.getInstance().MAX_TILE_SCORE = round(max(d_values.iteritems(), key=operator.itemgetter(1))[1], 4)

    for mt in parameters.getInstance().MAP_TILES:
        index = int(round((len(colors)-1)*utils.normalise(d_values[mt], parameters.getInstance().MIN_TILE_SCORE, parameters.getInstance().MAX_TILE_SCORE)))
        mt.heat_color_score = tuple([x for x in colors[index]] + [parameters.getInstance().HEATMAP_ALPHA])

    print("parameters.getInstance().MAX_TILE_SCORE={}".format(parameters.getInstance().MAX_TILE_SCORE))


def computeHeatMap_Cost():
    print("Compute heat map (cost)")

    red = colour.Color("green")
    colors = list(red.range_to(colour.Color("red"),20))
    colors = [tuple([int(x*255) for x in c.rgb]) for c in colors]

    d_values = {}
    for mt in parameters.getInstance().MAP_TILES:
        d_values[mt] = mt.getCost()

    parameters.getInstance().MAX_TILE_COST = round(max(d_values.iteritems(), key=operator.itemgetter(1))[1], 4)

    for mt in parameters.getInstance().MAP_TILES:
        index = int(round((len(colors)-1)*utils.normalise(d_values[mt], parameters.getInstance().MIN_TILE_SCORE, parameters.getInstance().MAX_TILE_COST)))
        mt.heat_color_cost = tuple([x for x in colors[index]] + [parameters.getInstance().HEATMAP_ALPHA])

    print("parameters.getInstance().MAX_TILE_COST={}".format(parameters.getInstance().MAX_TILE_COST))

def generateRiver(starters = parameters.getInstance().RIVER_STARTERS, enders=parameters.getInstance().RIVER_ENDERS):
    print("Generate rivers")
    river_starters = [x for x in parameters.getInstance().MAP_TILES if x.getType() in starters]
    start = random.choice(river_starters)

    l_river_enders = [x for x in parameters.getInstance().MAP_TILES if (utils.distance2p(start.get2DCoord(), x.get2DCoord()) <= 30.0 and x.getType() in enders and set([y.getType() for y in utils.getNeighboursFrom1D(elem_i=x.index, eight_neigh=False)]).intersection(set(tile_info.LAND_TYPES)) == set([]) )]

    end = random.choice(l_river_enders)

    if l_river_enders == [] or river_starters == []:
        return []

    _route = [start] + pf.astar(start, end, diagonal_neighbourhood=True)
    route = []

    for s in _route:
        if s.getType() not in tile_info.WATER_TYPES:
            if s.river:
                print("Merge with crossing river")
                route.append(s)
                break
            s_neigh = utils.getNeighboursFrom1D(s.index, parameters.getInstance().MAP_TILES, parameters.getInstance().CANVAS_WIDTH, parameters.getInstance().CANVAS_HEIGHT)
            b = False
            for sn in s_neigh:
                if sn.river:
                    route.append(sn)
                    b=True
                    break
            if b: 
                print("Merge with neighbouring river")
                break
            route.append(s)
        else:
            print("Merge with shallow or deep")
            route.append(s)
            break

    for t in route:
        t.river = True

    parameters.getInstance().RIVERS.append(route)

def main():
    pygame.init()

    #FIRST INIT
    monitor = get_monitors()[0]

    clock = pygame.time.Clock()
        
    # main_surface_width, main_surface_height = 860, 680
    # screen_width, screen_height = int(monitor.width*0.8), int(monitor.height*0.8)
    screen_width, screen_height = parameters.getInstance().WINDOW_WIDTH, parameters.getInstance().WINDOW_HEIGHT
    # main_surface_width, main_surface_height = int(round(screen_width*parameters.getInstance().MAIN_WINDOW_PROPORTION)), screen_height
    # info_surface_width, info_surface_height = int(round(screen_width*(1-parameters.getInstance().MAIN_WINDOW_PROPORTION))), screen_height
    main_surface_width, main_surface_height = parameters.getInstance().MAP_WIDTH, parameters.getInstance().MAP_HEIGHT
    info_surface_width, info_surface_height = parameters.getInstance().INFO_WIDTH, parameters.getInstance().INFO_HEIGHT

    os.environ['SDL_VIDEO_WINDOW_POS'] = "%d,%d" % ((monitor.width/2)-(screen_width/2),(monitor.height/2)-(screen_height/2))
    
    window = pygame.display.set_mode((screen_width, screen_height))
    caption = "Paint Generator"
    pygame.display.set_caption(caption)

    screen = pygame.Surface((main_surface_width, main_surface_height))
    alpha_surface = pygame.Surface((main_surface_width, main_surface_height), pygame.SRCALPHA)
    info_surface = pygame.Surface((info_surface_width, info_surface_height))


    #INIT
    for i in xrange(0, parameters.getInstance().CANVAS_WIDTH):
        for j in xrange(0, parameters.getInstance().CANVAS_HEIGHT):
            index = len(parameters.getInstance().MAP_TILES)
            maptile = MapTile(i * (main_surface_width/parameters.getInstance().CANVAS_WIDTH), 
                            j * (main_surface_height/parameters.getInstance().CANVAS_HEIGHT), 
                            int(round(float(main_surface_width)/float(parameters.getInstance().CANVAS_WIDTH))), 
                            int(round(float(main_surface_height)/float(parameters.getInstance().CANVAS_HEIGHT))), index)
            parameters.getInstance().MAP_TILES.append(maptile)
    for mt in parameters.getInstance().MAP_TILES:
        for n in utils.getNeighboursFrom1D(mt.index, parameters.getInstance().MAP_TILES, parameters.getInstance().CANVAS_WIDTH, parameters.getInstance().CANVAS_HEIGHT):
            mt.distance_to_neighbours[n] = utils.distance2p(mt.getPose(), n.getPose())


    #RUN
    run = True
    start = False
    step_counter = 0
    days = 0
    paused = False
    selected_tile = None
    selected_caravan = None
    fixed = False
    stop_generation = False
    generation_done = False
    simulation_started = False
    caravan_lauched = False
    heatmap = False
    local_info = False

    t_loop = 0.01
    q_time = []

    #TEST VARS
    test_path = None
    start_pos = None
    goal_pos = None
    pos_changed = False

    while run:
        clock.tick(parameters.getInstance().FORCED_FPS)

        start_time = time.time()
        
        t_update = start_time #time.time() if moved from this line

        step_counter += 1
        # if(step_counter%100000 == 0): step_counter = 0

        info_surface.fill(tile_info.WHITE)
        alpha_surface.fill(tile_info.EMPTY)

        for event in pygame.event.get():
            if event.type == pygame.QUIT :
                    run = False
            if event.type == pygame.KEYDOWN:
                if event.key == K_ESCAPE:
                    run = False
                if event.key == pygame.K_r and pygame.key.get_mods() & pygame.KMOD_CTRL:
                    for cp in parameters.getInstance().MAP_TILES:
                        cp.reset()
                    
                    simulation_started = False
                    generation_done = False
                    stop_generation = False

                    test_path = None

                    fixed = False

                    del parameters.getInstance().CARAVAN_LIST[:]
                    caravan_lauched = False

                    del parameters.getInstance().RIVERS[:]
                    del parameters.getInstance().MIGRANTS_VILLAGE_LIST[:]

                    paused = False

                if event.key == pygame.K_r and simulation_started:
                    test_path = None
                # if event.key == pygame.K_f and pygame.key.get_mods() & pygame.KMOD_CTRL:
                #     print fix_tiles()
                elif event.key == pygame.K_f:
                    parameters.getInstance().FAST_DISPLAY = not parameters.getInstance().FAST_DISPLAY
                elif event.key == pygame.K_h:
                    heatmap = not heatmap
                if event.key == pygame.K_l:
                    local_info = not local_info
                if event.key == pygame.K_RIGHT:
                    parameters.getInstance().HEATMAP_TYPE = ((parameters.getInstance().HEATMAP_TYPE+1)%2)
                    # print(parameters.getInstance().HEATMAP_TYPE)
                if event.key == pygame.K_SPACE and pygame.key.get_mods() & pygame.KMOD_CTRL or event.key == pygame.K_END:
                    stop_generation = True
                elif event.key == pygame.K_SPACE:
                    paused = not paused
                if event.key == pygame.K_RIGHT:
                    if paused:
                        pass
            elif event.type == pygame.MOUSEBUTTONDOWN:
                #LMB
                if event.button == 1 and pygame.key.get_mods() & pygame.KMOD_CTRL:
                    if simulation_started:
                        for cp in parameters.getInstance().MAP_TILES:
                            if cp.collidepoint(pygame.mouse.get_pos()) and cp != goal_pos:
                                start_pos = cp
                                pos_changed = True
                                break
                elif event.button == 1:
                    for cp in parameters.getInstance().MAP_TILES:
                        if cp.collidepoint(pygame.mouse.get_pos()):
                            selected_tile = cp
                            if len(cp.caravan) > 0:
                                selected_caravan = cp.caravan[0]
                            else:
                                selected_caravan = None
                    # for car in parameters.getInstance().CARAVAN_LIST:
                    #     if car.collidepoint(pygame.mouse.get_pos()) and car != selected_caravan:
                    #         selected_caravan = car 
                    pass
                #MMB
                if event.button == 2:
                    if selected_tile != None:
                        selected_tile.selected = False
                        selected_tile = None
                    if selected_caravan != None:
                        selected_caravan.selected = False
                        selected_caravan = None
                    pass
                #RMB
                if event.button == 3:
                    pass
                if event.button == 3 and pygame.key.get_mods() & pygame.KMOD_CTRL:
                    if simulation_started:
                        for cp in parameters.getInstance().MAP_TILES:
                            if cp.collidepoint(pygame.mouse.get_pos()) and cp != start_pos:
                                # selected_tile = cp
                                goal_pos = cp
                                pos_changed = True
                                break
                    pass
            #For a update while holding the mouse buttons pressed
            elif pygame.mouse.get_pressed()[0] and simulation_started and pygame.key.get_mods() & pygame.KMOD_CTRL:
                try:
                    for cp in parameters.getInstance().MAP_TILES:
                        if cp.collidepoint(pygame.mouse.get_pos()) and cp != goal_pos and cp != start_pos:
                            start_pos = cp
                            pos_changed = True
                            break
                except AttributeError:
                    pass
            elif pygame.mouse.get_pressed()[0]:
                try:
                    for cp in parameters.getInstance().MAP_TILES:
                        if cp.collidepoint(pygame.mouse.get_pos()):
                            selected_tile = cp
                            # if len(cp.caravan) > 0:
                            #     selected_caravan = cp.caravan[0]
                            break
                except AttributeError:
                    pass
            elif pygame.mouse.get_pressed()[2] and simulation_started:
                try:
                    for cp in parameters.getInstance().MAP_TILES:
                        if cp.collidepoint(pygame.mouse.get_pos()) and cp != goal_pos and cp != start_pos:
                            goal_pos = cp
                            pos_changed = True
                            break
                except AttributeError:
                    pass

        #UPDATE
        if not generation_done and step_counter%100==0:
            pass

        if stop_generation and not generation_done:
            for cp in parameters.getInstance().MAP_TILES:
                cp.color_fixed = True
            simulation_started = True
            generation_done = True

        if selected_tile != None:
            selected_tile.selected = True
        if selected_caravan != None:
            selected_caravan.selected = True
        if step_counter % max(int(parameters.getInstance().FORCED_FPS/parameters.getInstance().REFRESH_FREQ), 1) == 0 and not paused:
            for cp in parameters.getInstance().MAP_TILES:
                cp.update()

        if simulation_started:
            if not fixed:
                fix_tiles()
                parameters.getInstance().computeNbRivers()
                for i in range(0, parameters.getInstance().NB_RIVERS):
                    generateRiver()
                fixed = True
            if not caravan_lauched:
                computeHeatMap_Score()
                computeHeatMap_Cost()

                for i in xrange(0,parameters.getInstance().STARTING_NB_CARAVAN):
                    _t = utils.getEdgeTile(forbidden=["shallow_water", "deep_water"])
                    while len(_t.caravan) > 1:
                        _t = utils.getEdgeTile(forbidden=["shallow_water", "deep_water"])
                    car = Caravan(_t, name="caravan"+str(i))
                    parameters.getInstance().CARAVAN_LIST.append(car)
                caravan_lauched = True

            elif not paused:
                days += 1

                if step_counter%30 == 0:
                    if random.random() < len(parameters.getInstance().VILLAGE_LIST)*0.01:
                        for i in range(1, 3):
                            parameters.getInstance().MIGRANTS_VILLAGE_LIST.append(Migrant_Village(utils.getEdgeTile(forbidden=["shallow_water", "deep_water"])))

                for car in parameters.getInstance().CARAVAN_LIST:
                    car.next_step(step_counter)
                for vil in parameters.getInstance().VILLAGE_LIST:
                    vil.next_step(step_counter)
                for mig in parameters.getInstance().MIGRANTS_VILLAGE_LIST:
                    mig.next_step()
                for emis in parameters.getInstance().EMISSARY_VILLAGE_LIST:
                    emis.next_step()
        t_update = time.time() - t_update

        #DRAW
        t_display = time.time()
        if not parameters.getInstance().FAST_DISPLAY or (parameters.getInstance().FAST_DISPLAY and step_counter%1 == 0):
            for cp in parameters.getInstance().MAP_TILES:
                if cp != selected_tile and cp.selected:
                    cp.selected = False
                cp.draw(screen,  _FAST_DISPLAY=parameters.getInstance().FAST_DISPLAY)
                if heatmap:
                    cp.draw_heatmap(alpha_surface, _type=parameters.getInstance().HEATMAP_TYPE)

            for r in parameters.getInstance().RIVERS:
                len_r = len(r)
                if len_r > 1:
                    # print(len(r))
                    pygame.draw.lines(screen, tile_info.CYAN, False, [x.rect.center for x in r], 4) 

            for car in parameters.getInstance().CARAVAN_LIST:
                if car != selected_caravan and car.selected:
                    car.selected = False
                car.draw(screen, local_info, alpha_surface)

            for mig in parameters.getInstance().MIGRANTS_VILLAGE_LIST:
                mig.draw(screen, local_info)

            for emis in parameters.getInstance().EMISSARY_VILLAGE_LIST:
                emis.draw(screen, local_info, alpha_surface)
                

            for vil in parameters.getInstance().VILLAGE_LIST:
                vil.draw(screen, alpha_surface, local_info, _FAST_DISPLAY=parameters.getInstance().FAST_DISPLAY)


            # if test_path != None and len(test_path) > 1:
            #     pygame.draw.circle(screen, tile_info.GREEN, start_pos.rect.center, 5)
            #     pygame.draw.circle(screen, tile_info.BLACK, start_pos.rect.center, 5, 2)
            #     pygame.draw.circle(screen, tile_info.RED, goal_pos.rect.center, 5)
            #     pygame.draw.circle(screen, tile_info.BLACK, goal_pos.rect.center, 5, 2)


            #     pygame.draw.lines(screen, tile_info.BLACK, False, [x.rect.center for x in test_path], 3)
            #     pygame.draw.lines(screen, tile_info.WHITE, False, [x.rect.center for x in test_path], 1)

        t_display = time.time() - t_display

        #DRAW INFO PANEL

        #info text
        fontsize = int(info_surface_height*0.02)
        font = pygame.font.SysFont('Sans', fontsize)

        t_temp = time.time()
        diff_t = (t_temp - start_time) if (t_temp - start_time) > 0 else 0.0001

        fps = round(1.0 / t_loop, 0)
        q_time.append(round(fps))
        if len(q_time) >= 20 : q_time = q_time[1:]

        tmp = int(round(np.mean(q_time)))
        text = "{0:03d} LPS (~{1:.4f}s/loop)".format(tmp, round(diff_t, 4))#, len(str(tmp)) - len(str(int(tmp))) - 2 )
        if paused:
            text += " PAUSED"
        displ_text = font.render(text, True, tile_info.BLACK)
        info_surface.blit(displ_text, (10, fontsize*1.2))
        shift = fontsize*1.2
        
        text2 = "{0:03d}% logic, {1:03d}% display".format(int(round((round(t_update, 4) / diff_t)*100)), int(round((round(t_display, 4) / diff_t)*100)))
        displ_text2 = font.render(text2, True, tile_info.BLACK)
        info_surface.blit(displ_text2, (10, fontsize*1.2 + shift))
        shift = fontsize*1.2 + shift

        nb_years  = days/(30*12)
        nb_months = (days%(30*12))/30
        nb_days   = (days%(30*12))%30
        text_date = "{} days {} months {} years since first colons".format(nb_days, nb_months, nb_years)
        displ_text_date = font.render(text_date, True, tile_info.BLACK)
        info_surface.blit(displ_text_date, (10, fontsize*1.2 + shift))
        shift = fontsize*1.2 + shift

        shift = fontsize + shift


        if selected_tile != None:
            text3 = "Selected Tile info".format()
            displ_text3 = font.render(text3, True, tile_info.BLACK)
            info_surface.blit(displ_text3, (10, fontsize*1.2 + shift))
            shift = fontsize*1.2 + shift
        
            header = "Tile {} {}".format(selected_tile.index, selected_tile.get2DCoord())
            displ_header = font.render(header, True, tile_info.BLACK)
            info_surface.blit(displ_header, (10, shift + fontsize + 2))
            shift = shift + fontsize + 2

            selected_tile_info = "{} ({}), {} eval{}/{}".format(selected_tile.getType(), selected_tile.getCost(), "" if not selected_tile.river else "river" ,selected_tile.evaluate(), parameters.getInstance().MAX_TILE_SCORE)
            displ_selected_tile_info = font.render(selected_tile_info, True, tile_info.BLACK)
            info_surface.blit(displ_selected_tile_info, (10, shift + fontsize + 2))
            shift = shift + fontsize

            # print(selected_tile.detail_score)

            for car in selected_tile.caravan:
                selected_tile_caravan = "{}, {} people, {} tiles explored".format(car.name
                                                                , car.population_count
                                                                , len(caravan.explored_tiles))
                displ_selected_tile_info = font.render(selected_tile_caravan, True, tile_info.BLACK)
                info_surface.blit(displ_selected_tile_info, (10, shift + fontsize + 2))
                shift = shift + fontsize

            if selected_tile.village != None:
                selected_tile_village = "{}, {} people".format(selected_tile.village.name
                                                                , selected_tile.village.population_count
                                                                )
                displ_selected_tile_info = font.render(selected_tile_village, True, tile_info.BLACK)
                info_surface.blit(displ_selected_tile_info, (10, shift + fontsize + 2))
                shift = shift + fontsize
        # else:
        #     header = "No Tile selected"
        #     displ_header = font.render(header, True, tile_info.BLACK)
        #     info_surface.blit(displ_header, (10, shift + fontsize + 2))
        #     shift = shift + fontsize + 2

        shift = fontsize + shift

        text4 = "Caravans info".format()
        displ_text4 = font.render(text4, True, tile_info.BLACK)
        info_surface.blit(displ_text4, (10, fontsize*1.2 + shift))
        shift = fontsize*1.2 + shift

        # if selected_caravan != None:
        for caravan in parameters.getInstance().CARAVAN_LIST:
            selected_caravan_text = "   {}, {} ppl, x{} spd, {} thresh".format(caravan.name
                                                                , caravan.population_count
                                                                , (caravan.speed_modifier)
                                                                , round(caravan.score_thresh, 2))
            displ_selected_caravan = font.render(selected_caravan_text, True, tile_info.BLACK)
            info_surface.blit(displ_selected_caravan, (10, shift + fontsize + 2))
            shift = shift + fontsize

            selected_caravan_text = (
                                    "      {}% explored, {}/{} possible tiles".format(
                                        #   len(caravan.explored_tiles)),
                                            round((float(len(caravan.explored_tiles))/float(len(parameters.getInstance().MAP_TILES)))*100.0, 1)
                                            , len(caravan.possible_settlement_tile)
                                            , caravan.location_memory
                                        )
                                    )
            displ_selected_caravan = font.render(selected_caravan_text, True, tile_info.BLACK)
            info_surface.blit(displ_selected_caravan, (10, shift + fontsize + 2))
            shift = shift + fontsize

            # selected_caravan_text = "{} vision range".format(caravan.vision_range)
            # displ_selected_caravan = font.render(selected_caravan_text, True, tile_info.BLACK)
            # info_surface.blit(displ_selected_caravan, (10, shift + fontsize + 2))
            # shift = shift + fontsize
        # else:
        #     text = "No Caravan selected"
        #     displ_header = font.render(text, True, tile_info.BLACK)
        #     info_surface.blit(displ_header, (10, shift + fontsize + 2))
        #     shift = shift + fontsize + 2

        shift = fontsize*1.2 + shift

        text4 = "Villages info".format()
        displ_text4 = font.render(text4, True, tile_info.BLACK)
        info_surface.blit(displ_text4, (10, fontsize*1.2 + shift))
        shift = fontsize*1.2 + shift

        for village in parameters.getInstance().VILLAGE_LIST:
            villages_text = "   {}, {} ppl (x{})".format(village.name
                                                    , village.population_count
                                                    # , round((1.0-village.grow_rate)*100.0, 2))
                                                    , round((village.grow_rate), 4))
            displ_villages_text = font.render(villages_text, True, tile_info.BLACK)
            info_surface.blit(displ_villages_text, (10, shift + fontsize + 2))
            shift = shift + fontsize

        for migr in parameters.getInstance().MIGRANTS_VILLAGE_LIST:
            migrants_txt = "{}, {} ppl towards {}".format(migr.name
                                                    , migr.population_count
                                                    , migr.village_to_go.name
                                                    )

            displ_migrants_txt = font.render(migrants_txt, True, tile_info.BLACK)
            info_surface.blit(displ_migrants_txt, (10, shift + fontsize + 2))
            shift = shift + fontsize

        for emis in parameters.getInstance().EMISSARY_VILLAGE_LIST:
            text = "{} out there".format(emis.name)

            displ_text = font.render(text, True, tile_info.BLACK)
            info_surface.blit(displ_text, (10, shift + fontsize + 2))
            shift = shift + fontsize

        #Blit and Flip surfaces
        if not parameters.getInstance().FAST_DISPLAY or (parameters.getInstance().FAST_DISPLAY and step_counter%1 == 0):
            window.blit(screen, (0, 0))
            window.blit(alpha_surface, (0, 0))
        window.blit(info_surface, (main_surface_width, 0))


        # pygame.display.update([x.rect for x in parameters.getInstance().MAP_TILES if not x.color_fixed] + [pygame.Rect(main_surface_width, 0, info_surface.get_width(), info_surface.get_height())])
        pygame.display.update()

        t_loop = time.time() - start_time

def fix_tiles():
    print("Fix tiles")
    changed = False
    for mt in parameters.getInstance().MAP_TILES:
        d = {}
        for n in utils.getNeighboursFrom1D(elem_i=mt.index, eight_neigh=False):
            if n.color in d.keys():
                d[n.color] += 1
            else:
                d[n.color] = 1

        if not mt.color in d.keys(): #or d[mt.color] <= 1:
            mt.color = max(d.iteritems(), key=operator.itemgetter(1))[0]
            changed = True
    return changed

if __name__ == '__main__':
    main()