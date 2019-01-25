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

    def reset(self):
        # t = time.time()
        self.heat_color_score = tile_info.EMPTY
        self.heat_color_cost = tile_info.EMPTY
        if parameters.DEFAULT_DRAWING:
            self.color = random.choice(parameters.COLOR_PALETTE)
        else:
            # print(parameters.COLOR_PALETTE)
            # print(parameters.COLOR_PROBA)
            # self.color = tuple(np.random.choice(np.array(parameters.COLOR_PALETTE,dtype='i,i,i'), p=parameters.COLOR_PROBA))
            self.color = utils.weighted_choice(parameters.BIOME)
        self.color_fixed = False
        self.caravan = []
        self.river = False
        self.village = None
        # print (time.time() - t)

    def getPose(self):
        return (self.x, self.y)

    def update(self):
        if not self.color_fixed:
            neighs = utils.getNeighboursFrom1D(self.index, parameters.MAP_TILES, parameters.CANVAS_WIDTH, parameters.CANVAS_HEIGHT)
            
            self.color = random.choice([c.color for c in neighs])

            self.randomEffectSettings()
        else:
            pass

        self.image.fill(self.color)

    def get2DCoord(self):
        #k =     i * width + j. Thus i = k / width, j = k % width
        return (self.index / parameters.CANVAS_WIDTH, self.index%parameters.CANVAS_WIDTH)

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

    def evaluate(self, radius=2):
        vinicity = utils.getTilesInRadius(self, radius)
        vinicity_type = [x.getType() for x in vinicity]
        freq = utils.countFreq(vinicity_type)
        #1.0 MAX => MAX Diversity
        diversity = float(len(freq.keys())) / float(len(tile_info.USED_TYPES))

        neighbouring_river = sum([x.river*0.2 for x in vinicity])
        # if neighbouring_river != 0.0: print(neighbouring_river)

        score = 0.0

        for t in tile_info.USED_TYPES:
            if t not in freq.keys():
                freq[t] = 0.0

        if self.getType() in ["sea", "ocean", "city"]:
            return 0.0

        score = (
                    (1.5*freq["plain"] + 1.4*freq["sea"] + 0.9*freq["forest"] + 0.6*freq["hill"] + 0.2*freq["ocean"]
                     - 0.3*freq["desert"] - 0.4*freq["mountain"] - 3.0*freq["city"]) 
                    # (freq["plain"] + freq["sea"] + freq["forest"] + freq["hill"]
                    # - freq["ocean"] - freq["desert"] - freq["mountain"] - freq["city"]) #MAX 2.0
                    # (freq["plain"] + freq["sea"] + freq["forest"] + freq["hill"]
                    # + freq["ocean"] + freq["desert"] + freq["mountain"] + freq["city"]) #MAX 2.0
                    +
                    (diversity if diversity <= 0.5 else (1.0 - diversity)) * 1.2
                    +
                    self.river * 0.4 + neighbouring_river
                )

        return max(0.0, round(score, 4))

class Caravan(pygame.sprite.Sprite):
    def __init__(self, _tile, population_count=-1, name="caravan"):
        # Call the parent class (Sprite) constructor
        super(Caravan, self).__init__()

        self.tile = _tile
        self.tile.caravan.append(self)
        self.x = self.tile.rect.center[0]
        self.y = self.tile.rect.center[1]

        if population_count == -1:
            self.population_count = int(random.random()*(parameters.MAX_POP_PER_CARAVAN - parameters.MIN_POP_PER_CARAVAN) + parameters.MIN_POP_PER_CARAVAN)
        else:
            self.population_count = population_count

        self.speed_modifier = round(utils.normalise(self.population_count, parameters.MIN_POP_PER_CARAVAN*0.8, parameters.MAX_POP_PER_CARAVAN*1.2), 3)

        # self.speed_modifier = 1 + round(self.population_count / parameters.MAX_POP_PER_CARAVAN, 2)

        self.name = name

        self.selected = False

        # Create an image of the block, and fill it with a color.
        # This could also be an image loaded from the disk.
        # self.image = pygame.Surface([width, height])
        # self.image.fill(color)
        self.image = pygame.image.load(os.path.join('Sprites', 'caravan.png'))
        # self.image = pygame.transform.scale(self.image, (parameters.MAP_TILES[0].w, parameters.MAP_TILES[0].h))

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

        self.score_thresh = utils.normalise(self.population_count, parameters.MIN_POP_PER_CARAVAN*0.6, parameters.MAX_POP_PER_CARAVAN*1.4)*parameters.MAX_TILE_SCORE
        # print("{} ({}*{}) ==>  {} < {} < {}".format(self.score_thresh,  utils.normalise(self.population_count, parameters.MIN_POP_PER_CARAVAN*0.6, parameters.MAX_POP_PER_CARAVAN*1.4), parameters.MAX_TILE_SCORE, parameters.MIN_POP_PER_CARAVAN, self.population_count, parameters.MAX_POP_PER_CARAVAN))

    #Choose the destination of the caravan if None
    def choose_destination(self, forbidden=[]):
        self.destination = utils.getRandomTile()
        self.route = pf.astar(self.tile, self.destination, forbidden=[])

    #Move to the next tile in the route or choose to change course or action
    def next_step(self):
        self.visible_vinicity = utils.getTilesInRadius(self.tile, self.vision_range)

        if self.destination == None or len(self.route) == 0:
            self.choose_destination()

        if self.tile_goto == None:
            self.tile_goto = self.route[0]
            self.walking_left = int(round(self.tile_goto.getCost() * (1 + self.speed_modifier) * 2, 2))

        if self.tile_goto != None and self.walking_left > 0:
            self.walking_left -= 1
            if self.walking_left <= 0:
                self.set_next_tile()
                self.tile_goto = None

    def settle(self):
        pass

    def scanVinicity(self):
        pass

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

    def draw(self, screen, heatmap, alpha):
        # pygame.draw.circle(screen, tile_info.WHITE, (self.x, self.y), 8)
        # pygame.draw.circle(screen, tile_info.BLACK, (self.x, self.y), 8, 4)
        screen.blit(self.image, self.rect)
        if self.selected:
            pygame.draw.rect(screen, tile_info.RED, self.rect, 2)
        if self.route != []:
            pygame.draw.lines(screen, tile_info.BLACK, False, [self.tile.rect.center] + [x.rect.center for x in self.route], 3)
            pygame.draw.lines(screen, tile_info.WHITE, False, [self.tile.rect.center] + [x.rect.center for x in self.route], 1)

        if heatmap:
            for t in self.visible_vinicity:
                t.draw_heatmap(alpha, _type=parameters.HEATMAP_TYPE )
                # pygame.draw.rect(screen, tile_info.RED, t.rect, 1)

class Village(pygame.sprite.Sprite):
    """docstring for Village"""
    def __init__(self, name, tile, population_count):
        super(Village, self).__init__()
        self.name = name
        self.population_count = population_count
        self.tile = tile

        self.tile.village = self
        self.tile.color = tile_info.GRAY

        computeHeatMap_Score()

        self.grow_rate = random.random()*0.2 + 0.95

        # Create an image of the block, and fill it with a color.
        # This could also be an image loaded from the disk.
        # self.image = pygame.Surface([width, height])
        # self.image.fill(color)
        # self.image = pygame.image.load(os.path.join('Sprites', 'caravan.png'))

        # Fetch the rectangle object that has the dimensions of the image
        # Update the position of this object by setting the values of rect.x and rect.y
        # self.rect = pygame.Rect(self.x-(self.image.get_rect().size[0]/2), 
        #                         self.y-(self.image.get_rect().size[1]/2),
        #                         self.image.get_rect().size[0],
        #                         self.image.get_rect().size[1])
        # self.rect = self.image.get_rect()

        parameters.VILLAGE_LIST.append(self)

    def update(self):
        self.population_count *= self.grow_rate
        self.grow_rate = random.random()*0.2 + 0.95

    def draw(self, screen):
        pass



def computeHeatMap_Score():
    print("Compute heat map (score)")

    red = colour.Color("red")
    colors = list(red.range_to(colour.Color("green"),15))
    colors = [tuple([int(x*255) for x in c.rgb]) for c in colors]

    d_values = {}
    for mt in parameters.MAP_TILES:
        d_values[mt] = mt.evaluate()

    parameters.MAX_TILE_SCORE = round(max(d_values.iteritems(), key=operator.itemgetter(1))[1], 4)

    for mt in parameters.MAP_TILES:
        index = int(round((len(colors)-1)*utils.normalise(d_values[mt], parameters.MIN_TILE_SCORE, parameters.MAX_TILE_SCORE)))
        mt.heat_color_score = tuple([x for x in colors[index]] + [parameters.HEATMAP_ALPHA])

    print("parameters.MAX_TILE_SCORE={}".format(parameters.MAX_TILE_SCORE))


def computeHeatMap_Cost():
    print("Compute heat map (cost)")

    red = colour.Color("green")
    colors = list(red.range_to(colour.Color("red"),15))
    colors = [tuple([int(x*255) for x in c.rgb]) for c in colors]

    d_values = {}
    for mt in parameters.MAP_TILES:
        d_values[mt] = mt.getCost()

    parameters.MAX_TILE_COST = round(max(d_values.iteritems(), key=operator.itemgetter(1))[1], 4)

    for mt in parameters.MAP_TILES:
        index = int(round((len(colors)-1)*utils.normalise(d_values[mt], parameters.MIN_TILE_SCORE, parameters.MAX_TILE_COST)))
        mt.heat_color_cost = tuple([x for x in colors[index]] + [parameters.HEATMAP_ALPHA])

    print("parameters.MAX_TILE_COST={}".format(parameters.MAX_TILE_COST))

def generateRiver(starters = ["mountain"], enders=["sea", "ocean"]):
    print("Generate rivers")
    river_starters = [x for x in parameters.MAP_TILES if x.getType() in starters]
    start = random.choice(river_starters)

    l_river_enders = [x for x in parameters.MAP_TILES if (utils.distance2p(start.get2DCoord(), x.get2DCoord()) <= 30.0 and x.getType() in enders and set([y.getType() for y in utils.getNeighboursFrom1D(elem_i=x.index, eight_neigh=False)]).intersection(set(tile_info.LAND_TYPES)) == set([]) )]

    end = random.choice(l_river_enders)

    if l_river_enders == [] or river_starters == []:
        return []

    _route = [start] + pf.astar(start, end)
    route = []

    for s in _route:
        if s.getType() not in tile_info.WATER_TYPES:
            route.append(s)
        else:
            route.append(s)
            break

    for t in route:
        t.river = True

    parameters.RIVERS.append(route)

def main():
    pygame.init()

    #FIRST INIT
    monitor = get_monitors()[0]

    clock = pygame.time.Clock()
        
    # main_surface_width, main_surface_height = 860, 680
    # screen_width, screen_height = int(monitor.width*0.8), int(monitor.height*0.8)
    screen_width, screen_height = parameters.WINDOW_WIDTH, parameters.WINDOW_HEIGHT
    main_surface_width, main_surface_height = int(round(screen_width*parameters.MAIN_WINDOW_PROPORTION)), screen_height
    info_surface_width, info_surface_height = int(round(screen_width*(1-parameters.MAIN_WINDOW_PROPORTION))), screen_height
    os.environ['SDL_VIDEO_WINDOW_POS'] = "%d,%d" % ((monitor.width/2)-(screen_width/2),(monitor.height/2)-(screen_height/2))
    
    window = pygame.display.set_mode((screen_width, screen_height))
    caption = "Paint Generator"
    pygame.display.set_caption(caption)

    screen = pygame.Surface((main_surface_width, main_surface_height))
    alpha_surface = pygame.Surface((main_surface_width, main_surface_height), pygame.SRCALPHA)
    info_surface = pygame.Surface((info_surface_width, info_surface_height))


    #INIT
    for i in xrange(0, parameters.CANVAS_WIDTH):
        for j in xrange(0, parameters.CANVAS_HEIGHT):
            index = len(parameters.MAP_TILES)
            maptile = MapTile(i * (main_surface_width/parameters.CANVAS_WIDTH), 
                            j * (main_surface_height/parameters.CANVAS_HEIGHT), 
                            int(round(float(main_surface_width)/float(parameters.CANVAS_WIDTH))), 
                            int(round(float(main_surface_height)/float(parameters.CANVAS_HEIGHT))), index)
            parameters.MAP_TILES.append(maptile)
    for mt in parameters.MAP_TILES:
        for n in utils.getNeighboursFrom1D(mt.index, parameters.MAP_TILES, parameters.CANVAS_WIDTH, parameters.CANVAS_HEIGHT):
            mt.distance_to_neighbours[n] = utils.distance2p(mt.getPose(), n.getPose())


    #RUN
    run = True
    start = False
    step_counter = 0
    paused = False
    selected_tile = None
    selected_caravan = None
    fixed = False
    stop_generation = False
    generation_done = False
    simulation_started = False
    caravan_lauched = False
    heatmap = False

    t_loop = 0.01
    q_time = []

    #TEST VARS
    test_path = None
    start_pos = None
    goal_pos = None
    pos_changed = False

    while run:
        clock.tick(parameters.FORCED_FPS)

        start_time = time.time()
        
        t_update = start_time #time.time() if moved from this line

        step_counter += 1
        if(step_counter%100000 == 0): step_counter = 0

        info_surface.fill(tile_info.WHITE)
        alpha_surface.fill(tile_info.EMPTY)

        for event in pygame.event.get():
            if event.type == pygame.QUIT :
                    run = False
            if event.type == pygame.KEYDOWN:
                if event.key == K_ESCAPE:
                    run = False
                if event.key == pygame.K_r and pygame.key.get_mods() & pygame.KMOD_CTRL:
                    for cp in parameters.MAP_TILES:
                        cp.reset()
                    
                    simulation_started = False
                    generation_done = False
                    stop_generation = False

                    test_path = None

                    fixed = False

                    del parameters.CARAVAN_LIST[:]
                    caravan_lauched = False

                    del parameters.RIVERS[:]

                    paused = False

                if event.key == pygame.K_r and simulation_started:
                    test_path = None
                # if event.key == pygame.K_f and pygame.key.get_mods() & pygame.KMOD_CTRL:
                #     print fix_tiles()
                elif event.key == pygame.K_f:
                    parameters.FAST_DISPLAY = not parameters.FAST_DISPLAY
                elif event.key == pygame.K_h:
                    heatmap = not heatmap
                if event.key == pygame.K_RIGHT:
                    parameters.HEATMAP_TYPE = ((parameters.HEATMAP_TYPE+1)%2)
                    # print(parameters.HEATMAP_TYPE)
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
                        for cp in parameters.MAP_TILES:
                            if cp.collidepoint(pygame.mouse.get_pos()) and cp != goal_pos:
                                start_pos = cp
                                pos_changed = True
                                break
                elif event.button == 1:
                    for cp in parameters.MAP_TILES:
                        if cp.collidepoint(pygame.mouse.get_pos()) and cp != goal_pos:
                            selected_tile = cp
                            if len(cp.caravan) > 0:
                                selected_caravan = cp.caravan[0]
                    # for car in parameters.CARAVAN_LIST:
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
                        for cp in parameters.MAP_TILES:
                            if cp.collidepoint(pygame.mouse.get_pos()) and cp != start_pos:
                                # selected_tile = cp
                                goal_pos = cp
                                pos_changed = True
                                break
                    pass
            #For a update while holding the mouse buttons pressed
            elif pygame.mouse.get_pressed()[0] and simulation_started and pygame.key.get_mods() & pygame.KMOD_CTRL:
                try:
                    for cp in parameters.MAP_TILES:
                        if cp.collidepoint(pygame.mouse.get_pos()) and cp != goal_pos and cp != start_pos:
                            start_pos = cp
                            pos_changed = True
                            break
                except AttributeError:
                    pass
            elif pygame.mouse.get_pressed()[0]:
                try:
                    for cp in parameters.MAP_TILES:
                        if cp.collidepoint(pygame.mouse.get_pos()):
                            selected_tile = cp
                            if len(cp.caravan) > 0:
                                selected_caravan = cp.caravan[0]
                            break
                except AttributeError:
                    pass
            elif pygame.mouse.get_pressed()[2] and simulation_started:
                try:
                    for cp in parameters.MAP_TILES:
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
            for cp in parameters.MAP_TILES:
                cp.color_fixed = True
            simulation_started = True
            generation_done = True

        if selected_tile != None:
            selected_tile.selected = True
        if selected_caravan != None:
            selected_caravan.selected = True
        if step_counter % max(int(parameters.FORCED_FPS/parameters.REFRESH_FREQ), 1) == 0 and not paused:
            for cp in parameters.MAP_TILES:
                cp.update()

        if simulation_started:
            if not fixed:
                fix_tiles()
                for i in range(0, 10):
                    generateRiver()
                fixed = True
            if not caravan_lauched:
                computeHeatMap_Score()
                computeHeatMap_Cost()

                for i in xrange(0,parameters.STARTING_NB_CARAVAN):
                    _t = utils.getEdgeTile(forbidden=["sea", "ocean"])
                    while len(_t.caravan) > 1:
                        _t = utils.getEdgeTile(forbidden=["sea", "ocean"])
                    car = Caravan(_t, name="caravan"+str(i))
                    parameters.CARAVAN_LIST.append(car)
                caravan_lauched = True

            elif not paused:
                for car in parameters.CARAVAN_LIST:
                    car.next_step()
        t_update = time.time() - t_update

        #DRAW
        t_display = time.time()
        if not parameters.FAST_DISPLAY or (parameters.FAST_DISPLAY and step_counter%5 == 0):
            for cp in parameters.MAP_TILES:
                if cp != selected_tile and cp.selected:
                    cp.selected = False
                cp.draw(screen,  _FAST_DISPLAY=parameters.FAST_DISPLAY)
                if heatmap:
                    cp.draw_heatmap(alpha_surface, _type=parameters.HEATMAP_TYPE)

            for r in parameters.RIVERS:
                if len(r) > 1 and r != [] and r != None:
                    # print(len(r))
                    pygame.draw.lines(screen, tile_info.BLUE_2, False, [x.rect.center for x in r], 6) 

            for car in parameters.CARAVAN_LIST:
                car.draw(screen, heatmap, alpha_surface)

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

            selected_tile_info = "{} ({}) eval{}/{}".format(selected_tile.getType(), selected_tile.getCost(), selected_tile.evaluate(), parameters.MAX_TILE_SCORE)
            displ_selected_tile_info = font.render(selected_tile_info, True, tile_info.BLACK)
            info_surface.blit(displ_selected_tile_info, (10, shift + fontsize + 2))
            shift = shift + fontsize

            for car in selected_tile.caravan:
                selected_tile_caravan = "{}, {} people".format(car.name
                                                                , car.population_count)
                displ_selected_tile_info = font.render(selected_tile_caravan, True, tile_info.BLACK)
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
        for caravan in parameters.CARAVAN_LIST:
            selected_caravan_text = "   {}, {} people, {}% spd".format(caravan.name
                                                                , caravan.population_count
                                                                , (1.0-caravan.speed_modifier)*100)
            displ_selected_caravan = font.render(selected_caravan_text, True, tile_info.BLACK)
            info_surface.blit(displ_selected_caravan, (10, shift + fontsize + 2))
            shift = shift + fontsize

            selected_caravan_text = "      {} walking left, {} tile(s) left".format(caravan.walking_left, len(caravan.route))
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

        for village in parameters.VILLAGE_LIST:
            villages_text = "   {}, {} people".format(village.name
                                                    , village.population_count)
            displ_villages_text = font.render(villages_text, True, tile_info.BLACK)
            info_surface.blit(displ_villages_text, (10, shift + fontsize + 2))
            shift = shift + fontsize

        #Blit and Flip surfaces
        if not parameters.FAST_DISPLAY or (parameters.FAST_DISPLAY and step_counter%5 == 0):
            window.blit(screen, (0, 0))
            window.blit(alpha_surface, (0, 0))
        window.blit(info_surface, (main_surface_width, 0))


        # pygame.display.update([x.rect for x in parameters.MAP_TILES if not x.color_fixed] + [pygame.Rect(main_surface_width, 0, info_surface.get_width(), info_surface.get_height())])
        pygame.display.update()

        t_loop = time.time() - start_time

def fix_tiles():
    print("Fix tiles")
    changed = False
    for mt in parameters.MAP_TILES:
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