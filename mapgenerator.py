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

import tile_info
import utils
import parameters
import pathfinding as pf

class MapTile(object):
    def __init__(self, x, y, w, h, index):
        super(MapTile, self).__init__()
        self.x = x
        self.y = y
        self.h = h
        self.w = w

        self.index = index

        # self.color = (int(random.random() * 255), int(random.random() * 255), int(random.random() * 255))
        self.randomise()

        self.rect = pygame.Rect(self.x, self.y, self.w, self.h)

        self.distance_to_neighbours = {}

        self.selected = False
        self.effect = True
        self.randomEffectSettings()

    def randomise(self):
        if parameters.DEFAULT_DRAWING:
            self.color = random.choice(parameters.COLOR_PALETTE)
        else:
            # print(parameters.COLOR_PALETTE)
            # print(parameters.COLOR_PROBA)
            self.color = tuple(np.random.choice(np.array(parameters.COLOR_PALETTE,dtype='i,i,i'), p=parameters.COLOR_PROBA))
        self.color_fixed = False

    def getPose(self):
        return (self.x, self.y)

    def update(self):

        if not self.color_fixed:
            neighs = utils.getNeighboursFrom1D(self.index, parameters.MAP_TILES, parameters.CANVAS_WIDTH, parameters.CANVAS_HEIGHT)
            
            self.color = random.choice([c.color for c in neighs])

            self.randomEffectSettings()
        else:
            pass

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
        pygame.draw.rect(screen, self.color, self.rect)
        if self.selected:
            pygame.draw.rect(screen, tile_info.RED, self.rect, 2)
            print(self.toString())
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

    def getType(self):
        return tile_info.COLOR_TO_TYPE[self.color]

    def getCost(self):
        return tile_info.TYPE_TO_COST[self.getType()]

    def collidepoint(self, pos):
        return self.rect.collidepoint(pos)

    def toString(self):
        return ("({}, {}) {} ({})"
                    .format(self.x, self.y, self.getType(), self.getCost()))

class Group(object):
    def __init__(self, c, population_count=int(random.random()*50)+30, speed=1):
        super(Group, self).__init__()
        self.x = c[0]
        self.y = c[1]
        self.population_count = population_count
        self.speed = speed

    def draw(self, screen):
        pygame.draw.circle(screen, tile_info.WHITE, (self.x, self.y), 8)
        pygame.draw.circle(screen, tile_info.BLACK, (self.x, self.y), 8, 4)
        

def main():
    pygame.init()

    #FIRST INIT
    monitor = get_monitors()[0]

    clock = pygame.time.Clock()
        
    # main_surface_width, main_surface_height = 860, 680
    # screen_width, screen_height = int(monitor.width*0.8), int(monitor.height*0.8)
    screen_width, screen_height = parameters.WINDOW_WIDTH, parameters.WINDOW_HEIGHT
    main_surface_width, main_surface_height = int(screen_width*parameters.MAIN_WINDOW_PROPORTION), int(screen_height)
    info_surface_width, info_surface_height = int(screen_width*(1-parameters.MAIN_WINDOW_PROPORTION)), int(screen_height)
    os.environ['SDL_VIDEO_WINDOW_POS'] = "%d,%d" % ((monitor.width/2)-(screen_width/2),(monitor.height/2)-(screen_height/2))
    
    window = pygame.display.set_mode((screen_width, screen_height))
    caption = "Paint Generator"
    pygame.display.set_caption(caption)

    screen = pygame.Surface((main_surface_width, main_surface_height))
    info_surface = pygame.Surface((info_surface_width, info_surface_height))


    #INIT
    for i in xrange(0, parameters.CANVAS_WIDTH):
        for j in xrange(0, parameters.CANVAS_HEIGHT):
            index = len(parameters.MAP_TILES)
            maptile = MapTile(i * (main_surface_width/parameters.CANVAS_WIDTH), j * (main_surface_height/parameters.CANVAS_HEIGHT), round(main_surface_width/parameters.CANVAS_WIDTH), round(main_surface_height/parameters.CANVAS_HEIGHT), index)
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
    fixed = False
    stop_generation = False
    generation_done = False
    simulation_started = False
    group_lauched = False

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

        for event in pygame.event.get():
            if event.type == pygame.QUIT :
                    run = False
            if event.type == pygame.KEYDOWN:
                if event.key == K_ESCAPE:
                    run = False
                if event.key == pygame.K_r and pygame.key.get_mods() & pygame.KMOD_CTRL:
                    for cp in parameters.MAP_TILES:
                        cp.randomise()
                    
                    simulation_started = False
                    generation_done = False
                    stop_generation = False

                    test_path = None

                    fixed = False

                    del parameters.GROUP_LIST[:]
                    group_lauched = False

                if event.key == pygame.K_r and simulation_started:
                    test_path = None
                if event.key == pygame.K_f and pygame.key.get_mods() & pygame.KMOD_CTRL:
                    print fix_tiles()
                elif event.key == pygame.K_f:
                    parameters.FAST_DISPLAY = not parameters.FAST_DISPLAY
                if event.key == pygame.K_SPACE:
                    paused = not paused
                if event.key == pygame.K_SPACE and pygame.key.get_mods() & pygame.KMOD_CTRL:
                    stop_generation = True
                if event.key == pygame.K_RIGHT:
                    if paused:
                        pass
            elif event.type == pygame.MOUSEBUTTONDOWN:
                #LMB
                if event.button == 1:
                    if simulation_started:
                        for cp in parameters.MAP_TILES:
                            if cp.collidepoint(pygame.mouse.get_pos()) and cp != goal_pos:
                                # selected_tile = cp
                                start_pos = cp
                                pos_changed = True
                                break
                    pass
                #MMB
                if event.button == 2:
                    selected_tile = None
                    pass
                #RMB
                if event.button == 3:
                    if simulation_started:
                        for cp in parameters.MAP_TILES:
                            if cp.collidepoint(pygame.mouse.get_pos()) and cp != start_pos:
                                # selected_tile = cp
                                goal_pos = cp
                                pos_changed = True
                                break
                    pass
            elif pygame.mouse.get_pressed()[0] and simulation_started:
                try:
                    for cp in parameters.MAP_TILES:
                        if cp.collidepoint(pygame.mouse.get_pos()) and cp != goal_pos and cp != start_pos:
                            start_pos = cp
                            pos_changed = True
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
        if step_counter % max(int(parameters.FORCED_FPS/parameters.REFRESH_FREQ), 1) == 0 and not paused:
            for cp in parameters.MAP_TILES:
                cp.update()

        if simulation_started:

            if not group_lauched:
                grp = Group(utils.getEdgeCoord())
                parameters.GROUP_LIST.append(grp)
                group_lauched = True

            if not fixed:
                tile_changed = fix_tiles()

                fixed = True
            if test_path == None:
                start_pos = random.choice(parameters.MAP_TILES)
                goal_pos = random.choice([x for x in parameters.MAP_TILES if x != start_pos])
            if test_path == None or pos_changed:
                pos_changed = False
                test_path = pf.astar(start_pos, goal_pos, forbidden=[]) #
                print(pf.computePathLength(test_path))

                # print("No path from {} to {}".format(start_pos.getPose(), goal_pos.getPose()))
        t_update = time.time() - t_update

        #DRAW
        t_display = time.time()
        if not parameters.FAST_DISPLAY or (parameters.FAST_DISPLAY and step_counter%5 == 0):
            for cp in parameters.MAP_TILES:
                if cp != selected_tile and cp.selected:
                    cp.selected = False
                cp.draw(screen,  _FAST_DISPLAY=parameters.FAST_DISPLAY)

            for grp in parameters.GROUP_LIST:
                grp.draw(screen)

            if test_path != None and len(test_path) > 1:
                pygame.draw.circle(screen, tile_info.GREEN, start_pos.rect.center, 5)
                pygame.draw.circle(screen, tile_info.BLACK, start_pos.rect.center, 5, 2)
                pygame.draw.circle(screen, tile_info.RED, goal_pos.rect.center, 5)
                pygame.draw.circle(screen, tile_info.BLACK, goal_pos.rect.center, 5, 2)


                pygame.draw.lines(screen, tile_info.BLACK, False, [x.rect.center for x in test_path], 3)
                pygame.draw.lines(screen, tile_info.WHITE, False, [x.rect.center for x in test_path], 1)

        t_display = time.time() - t_display

        #DRAW INFO PANEL

        #info text
        fontsize = int(info_surface_height*0.02)
        font = pygame.font.SysFont('Sans', fontsize)

        t_temp = time.time()
        diff_t = (t_temp - start_time) if (t_temp - start_time) > 0 else 0.0001

        fps = round(1.0 / t_loop, 0)
        q_time.append(round(fps))
        if len(q_time) >= 50 : q_time = q_time[1:]

        tmp = int(round(np.mean(q_time)))
        text = "{0:03d} LPS (~{1:.4f}s/loop)".format(tmp, round(diff_t, 4))#, len(str(tmp)) - len(str(int(tmp))) - 2 )
        if paused:
            text += " PAUSED"
        text2 = "{0:03d}% logic, {1:03d}% display".format(int(round((round(t_update, 4) / diff_t)*100)), int(round((round(t_display, 4) / diff_t)*100)))
        displ_text = font.render(text, True, tile_info.BLACK)
        displ_text2 = font.render(text2, True, tile_info.BLACK)
        info_surface.blit(displ_text, (10, fontsize*1.2))
        shift = fontsize*1.2
        info_surface.blit(displ_text2, (10, fontsize*1.2 + shift))
        shift = fontsize*1.2 + shift

        #Blit and Flip surfaces
        if not parameters.FAST_DISPLAY or (parameters.FAST_DISPLAY and step_counter%5 == 0):
            window.blit(screen, (0, 0))
        window.blit(info_surface, (main_surface_width, 0))


        # pygame.display.update([x.rect for x in parameters.MAP_TILES if not x.color_fixed] + [pygame.Rect(main_surface_width, 0, info_surface.get_width(), info_surface.get_height())])
        pygame.display.update()

        t_loop = time.time() - start_time

def fix_tiles():
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