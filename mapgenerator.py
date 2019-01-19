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
        self.color = random.choice(parameters.COLOR_PALETTE)

        self.rect = pygame.Rect(self.x, self.y, self.w, self.h)

        self.color_fixed = False

        self.distance_to_neighbours = {}

        self.selected = False
        
    def randomise(self):
        self.color = random.choice(parameters.COLOR_PALETTE)
        self.color_fixed = False

    def getPose(self):
        return (self.x, self.y)

    def update(self):

        if not self.color_fixed:
            neighs = utils.getNeighboursFrom1D(self.index, parameters.MAP_TILES, parameters.CANVAS_WIDTH, parameters.CANVAS_HEIGHT)
            if random.random() < 0.05:
                self.color = random.choice([c.color for c in neighs])
                # self.color_fixed = True
            else:
                # self.color = random.choice(parameters.COLOR_PALETTE)
                self.color = random.choice([c.color for c in neighs])
        else:
            pass

    def draw(self, screen):
        pygame.draw.rect(screen, self.color, self.rect)
        if self.selected:
            pygame.draw.rect(screen, tile_info.RED, self.rect, 2)
            print(self.toString())

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
    def __init__(self, x, y, count=int(random.random()*50)+30, speed=1):
        super(Group, self).__init__()
        self.x = x
        self.y = y
        self.count = count
        self.speed = speed
        

def main():
    pygame.init()

    #FIRST INIT
    monitor = get_monitors()[0]

    clock = pygame.time.Clock()
        
    # main_surface_width, main_surface_height = 860, 680
    # screen_width, screen_height = int(monitor.width*0.8), int(monitor.height*0.8)
    screen_width, screen_height = parameters.WINDOW_WIDTH, parameters.WINDOW_HEIGHT
    main_surface_width, main_surface_height = int(screen_width*0.75), int(screen_height)
    info_surface_width, info_surface_height = int(screen_width*0.25), int(screen_height)
    os.environ['SDL_VIDEO_WINDOW_POS'] = "%d,%d" % ((monitor.width/2)-(screen_width/2),(monitor.height/2)-(screen_height/2))
    
    window = pygame.display.set_mode((screen_width, screen_height))
    caption = "Paint Generator"
    pygame.display.set_caption(caption)

    screen = pygame.Surface((main_surface_width, main_surface_height))
    info_surf = pygame.Surface((info_surface_width, info_surface_height))


    #INIT
    for i in xrange(0, parameters.CANVAS_WIDTH):
        for j in xrange(0, parameters.CANVAS_HEIGHT):
            index = len(parameters.MAP_TILES)
            maptile = MapTile(i * (main_surface_width/parameters.CANVAS_WIDTH), j * (main_surface_height/parameters.CANVAS_HEIGHT), int(main_surface_width/parameters.CANVAS_WIDTH), int(main_surface_height/parameters.CANVAS_HEIGHT), index)
            parameters.MAP_TILES.append(maptile)
    for mt in parameters.MAP_TILES:
        for n in utils.getNeighboursFrom1D(mt.index, parameters.MAP_TILES, parameters.CANVAS_WIDTH, parameters.CANVAS_HEIGHT):
            mt.distance_to_neighbours[n] = utils.distance2p(mt.getPose(), n.getPose())


    #RUN
    run = True
    start = False
    groups_launched = False
    step_counter = 0
    pause = False
    selected_tile = None
    fixed = False

    #TEST VARS
    test_path = None
    start_pos = None
    goal_pos = None
    pos_changed = False

    while run:
        clock.tick(parameters.FORCED_FPS)

        step_counter += 1
        if(step_counter%100000 == 0): step_counter = 0

        for event in pygame.event.get():
            if event.type == pygame.KEYDOWN:
                if event.key == K_ESCAPE :
                    run = False
                if event.key == pygame.K_r and pygame.key.get_mods() & pygame.KMOD_CTRL:
                    for cp in parameters.MAP_TILES:
                        cp.randomise()
                    groups_launched = False
                    test_path = None
                    fixed = False
                if event.key == pygame.K_r and groups_launched:
                    test_path = None
                if event.key == pygame.K_f:
                    fix_tiles()
                if event.key == pygame.K_SPACE:
                    pause = not pause
                if event.key == pygame.K_SPACE and pygame.key.get_mods() & pygame.KMOD_CTRL:
                    for cp in parameters.MAP_TILES:
                        cp.color_fixed = True
                    groups_launched = True
                if event.key == pygame.K_RIGHT:
                    if pause:
                        pass
            elif event.type == pygame.MOUSEBUTTONDOWN:
                #LMB
                if event.button == 1:
                    if groups_launched:
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
                    if groups_launched:
                        for cp in parameters.MAP_TILES:
                            if cp.collidepoint(pygame.mouse.get_pos()) and cp != start_pos:
                                # selected_tile = cp
                                goal_pos = cp
                                pos_changed = True
                                break
                    pass
            elif pygame.mouse.get_pressed()[0] and groups_launched:
                try:
                    for cp in parameters.MAP_TILES:
                        if cp.collidepoint(pygame.mouse.get_pos()) and cp != goal_pos and cp != start_pos:
                            start_pos = cp
                            pos_changed = True
                            break
                except AttributeError:
                    pass
            elif pygame.mouse.get_pressed()[2] and groups_launched:
                try:
                    for cp in parameters.MAP_TILES:
                        if cp.collidepoint(pygame.mouse.get_pos()) and cp != goal_pos and cp != start_pos:
                            goal_pos = cp
                            pos_changed = True
                            break
                except AttributeError:
                    pass

        #UPDATE
        if selected_tile != None:
            selected_tile.selected = True
        if step_counter % max(int(parameters.FORCED_FPS/parameters.REFRESH_FREQ), 1) == 0 and not pause:
            for cp in parameters.MAP_TILES:
                cp.update()

        if groups_launched:
            if not fixed:
                fix_tiles()
                fixed = True
            if test_path == None:
                start_pos = random.choice(parameters.MAP_TILES)
                goal_pos = random.choice([x for x in parameters.MAP_TILES if x != start_pos])
            if test_path == None or pos_changed:
                pos_changed = False
                test_path = pf.astar(start_pos, goal_pos, forbidden=[]) #
                print(pf.computePathLength(test_path))

                # print("No path from {} to {}".format(start_pos.getPose(), goal_pos.getPose()))
                

        # if step_counter % 30*10 == 0 and not pause:
        #     for x in xrange(0, int(0.05*(parameters.CANVAS_HEIGHT*parameters.CANVAS_WIDTH))):
        #         random.choice(parameters.MAP_TILES).randomise()

        #DRAW
        for cp in parameters.MAP_TILES:
            if cp != selected_tile and cp.selected:
                cp.selected = False
            cp.draw(screen)

        if test_path != None and len(test_path) > 1:
            pygame.draw.circle(screen, tile_info.GREEN, start_pos.rect.center, 5)
            pygame.draw.circle(screen, tile_info.BLACK, start_pos.rect.center, 5, 2)
            pygame.draw.circle(screen, tile_info.RED, goal_pos.rect.center, 5)
            pygame.draw.circle(screen, tile_info.BLACK, goal_pos.rect.center, 5, 2)


            pygame.draw.lines(screen, tile_info.BLACK, False, [x.rect.center for x in test_path], 3)
            pygame.draw.lines(screen, tile_info.WHITE, False, [x.rect.center for x in test_path], 1)

        #Blit and Flip surfaces
        info_surf.fill(tile_info.WHITE)
        window.blit(screen, (0, 0))
        window.blit(info_surf, (main_surface_width, 0))


        pygame.display.flip()

def fix_tiles():
    for mt in parameters.MAP_TILES:
        d = {}
        for n in utils.getNeighboursFrom1D(elem_i=mt.index, eight_neigh=False):
            if n.color in d.keys():
                d[n.color] += 1
            else:
                d[n.color] = 1
        if not mt.color in d.keys():
            mt.color = max(d.iteritems(), key=operator.itemgetter(1))[0]

if __name__ == '__main__':
    main()