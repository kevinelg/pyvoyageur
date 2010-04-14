#!/usr/bin/env python
# encoding: utf-8
"""
GuyeNeuhaus.py

Created by Raphael Guye and Jonathan Neuhaus on 2010-04-14.
Copyright (c) 2010 HE-Arc. All rights reserved.
"""

import pygame
from pygame.locals import KEYDOWN, QUIT, MOUSEBUTTONDOWN, K_RETURN, K_ESCAPE
import sys


#================================================
#              VARIABLES GLOBALES
#================================================

cities = []
screen_x = 500
screen_y = 500

city_color = [10,10,200] # blue
city_radius = 3
font_color = [255,255,255] # white


#================================================
#              Classes
#================================================

class City(object):
    """Representation of a city"""
    def __init__(self, x, y, name):
        self.x = x
        self.y = y
        self.name = name


#================================================
#              Main
#================================================

def main():
    global text
    initPygame()
    draw(cities)

    collecting = True
	
    while collecting:
        for event in pygame.event.get():
            if event.type == QUIT:
                sys.exit(0)
            elif event.type == KEYDOWN and event.key == K_RETURN:
                collecting = False
            elif event.type == MOUSEBUTTONDOWN:
                (x,y) = pygame.mouse.get_pos()
                cities.append(City(x,y,"v" + str(len(cities))))
                draw(cities)
                print "draw() called"
                #print cities
    screen.fill(0)
    
    ga_solve(cities)
    
    pos = []
    [pos.append((c.x,c.y)) for c in cities]
    pygame.draw.lines(screen,city_color,True,pos)
    text = font.render("Un chemin, pas le meilleur!", True, font_color)
    textRect = text.get_rect()
    screen.blit(text, textRect)
    pygame.display.flip()
    while True:
        event = pygame.event.wait()
        if event.type == KEYDOWN: break

#================================================
#              Methodes
#================================================

def initPygame():
    global screen
    global font
    pygame.init() 
    window = pygame.display.set_mode((screen_x, screen_y)) 
    pygame.display.set_caption('Exemple') 
    screen = pygame.display.get_surface() 
    font = pygame.font.Font(None,30)

def draw(cities):
    screen.fill(0)
    for c in cities:
        pygame.draw.circle(screen,city_color,(c.x,c.y),city_radius)
    text = font.render("Nombre: %i" % len(cities), True, font_color)
    textRect = text.get_rect()
    screen.blit(text, textRect)
    pygame.display.flip()

def ga_solve(file=None, gui=True, maxtime=0):
    """ Salesman resolution """
    global cities
    new = []
    for c in cities:
            new.insert(0,c)
    cities = new
    pass

if __name__ == '__main__':
    main()
