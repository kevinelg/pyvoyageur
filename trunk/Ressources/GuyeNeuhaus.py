#!/usr/bin/env python
# encoding: utf-8
''' 
GuyeNeuhaus.py

Created by Raphael Guye and Jonathan Neuhaus on 2010-04-14.
Copyright (c) 2010 HE-Arc. All rights reserved.
''' 

import pygame
from pygame.locals import KEYDOWN, QUIT, MOUSEBUTTONDOWN, K_RETURN, K_ESCAPE
import sys
import os
from string import strip
from optparse import OptionParser
from MyUtils import speedMeasure
import math
from random import randint
import time
import threading
from Queue import *
try:
	import psyco
	psyco.full()
except ImportError:
	pass

#================================================
#              VARIABLES GLOBALES
#================================================

# -------- GUI -------- #
text = None
screen = None
font = None
screen_x = 500
screen_y = 500
city_color = [255,0,0]      # blue graph between listCities
city_radius = 3             # circle radius when user click a city
font_color = [255,255,255]  # white font for text

# ------ ga tools ----- #
result = Queue(1)           # finish result - best routes
#listCities = []             # each cities click bye user
stopRunning = False         # True when maxime is done

# ---- ga constants --- #
initialRoutesNumber = 100   # maximum number of initial routes
pe1 = 0                    # % of the population to eliminate and then add by crossover
pe2 = 100                    # % of the population to choose for mutation (dynamic)
epsilonDistCities = 5       # minimum distance between 2 listCities for natural selection


#================================================
#              Classes
#================================================

class City(object):
    ''' Representation of a city''' 
    __slots__ = ['x','y','name']
    def __init__(self, x, y, name):
        self.x = x
        self.y = y
        self.name = name

    def __str__(self):
        return self.name

    def nearest(self, listCities, listCitiesCheck):
        ''' In  :   listCities as the list contains ALL of the cities
        listCitiesCheck as the list contains all the cities already treated
        Out :   The nearest city of self that it isn't contained in listCitiesCheck.'''
        cityNearest = listCities[0]
        i=1
        while cityNearest == self or cityNearest in listCitiesCheck:
            cityNearest = listCities[i]
            i+=1
        smallDistance = dist2City(self,cityNearest)

        for c in listCities:
            if dist2City(self, c) < smallDistance and c <> self and c not in listCitiesCheck:
                cityNearest = c
                smallDistance = dist2City(self,cityNearest)

        return cityNearest

class Route(object):
    ''' Route with each cities '''
    __slots__ = ['cityList']
    def __init__(self, cityList):
    	self.cityList = cityList[:]
        
    def len(self):
        ''' Process the length of a route''' 
    	length = sum([dist2City(self.cityList[i], self.cityList[i+1]) for i in range(len(self.cityList)-1)])
                
    	# Add the distance between the first and last element of the cityList
    	length += dist2City(self.cityList[0], self.cityList[-1])
        return length
        
    def isEgal(self, route):
        ''' Check if the 2 listRoutes are equal''' 
        if (len(self.cityList) <> route.len()):
            return False
        
        for i in range(len(self.cityList)):
            if (self.cityList[i]<>route[i]):
                return False
        return True

    def isContained(self, listRoutes):
        ''' Check if the self route is contained in the listRoutes ''' 
        for r in listRoutes:
            if r.isEgal(self):
                return True
        return False
        
    def __str__(self):
        tmp = "len : " + str(self.len()) + "\n"
        for c in self.cityList:
            tmp += str(c) + " / "
        return tmp
        
class GeneticAlgorithm(object):
    ''' Contains all the genetics methodes to solve the problem '''
    def __init__(self,listCities):
        self.listRoutes = []
        self.initialRoutesNumber = 0
        # First base route (random => so very bad route...)
        self.badRoute = Route(listCities)

        # Optimize the base route
        self.listCities = notTooBadSorting(listCities)
        self.baseRoute = Route(self.listCities)
        
        self.pe1 = 0
        # Dynamic adaptation of the factors
        if len(self.baseRoute.cityList)<50:
            self.pe2 = 100
            self.initialRoutesNumber = 100
        else:
            # Linear scaling to have: 50 cities > pe2=100 / 300 cities > pe2=30
            self.pe2 = 114 - 7.0/25*len(baseRoute.cityList)
            # Linear scaling to have: 50 cities > pop=100 / 200 cities > pop=200
            self.initialRoutesNumber = 67 + 2.0/3*len(baseRoute.cityList)
        if pe2<10:
            self.pe2 = 10
        
    # -------------------------------- #
    # -- Central algorithm methods -- #
    # -------------------------------- #
    #@speedMeasure
    def generateRoutes(self):
        ''' Generate the number of listRoutes required ''' 
        cpt=1
        lenCityList = len(self.baseRoute.cityList)    
        # Generate a random indexList
        indexList = []
        indexList.append(range(lenCityList))
        while cpt <= (self.initialRoutesNumber - 1) and cpt <= (self.maxPossibilities(lenCityList) - 1):
            tmp = self.shake(lenCityList)
            while tmp in indexList:
                tmp = self.shake(lenCityList)
            indexList.append(tmp)
            cpt += 1

        # Generate the baseRoute list with the generated indexList
        for j in indexList:
            cityList = []
            [cityList.append(self.baseRoute.cityList[i]) for i in j]
            self.listRoutes.append(Route(cityList))

        self.initialRoutesNumber = len(self.listRoutes)
    
    #@speedMeasure
    def selection(self):
        ''' Process a selection by eliminating the similar individuals '''
        R = int(self.initialRoutesNumber * (self.pe1/100.0))
        # We sort the individual in lenght-value order
        self.sortListRoutesByLength()
            
        # Eliminate all similar individuals if the difference < epsilonDistCities
        i=0
        while i<len(self.listRoutes)-1 and R > 0:
            if (self.listRoutes[i].len() - self.listRoutes[i+1].len() < epsilonDistCities):
                j = i+1
                while (j <len(self.listRoutes) and self.listRoutes[i].len() - self.listRoutes[j].len() < epsilonDistCities and R > 0):
                    self.listRoutes.remove(self.listRoutes[j])
                    j += 1
                    R -= 1
            i += 1
            
        # Eliminate the other individuals in the order of lowest lenght-value order
        while R > 0:
            self.listRoutes.pop(len(self.listRoutes)-1)
            R -= 1
    
    #@speedMeasure
    def crossover(self):
        ''' Process a crossover between routes '''
        R = int(self.initialRoutesNumber * (self.pe1/100.0))
            
        pairList = []    
        # Select R number of pair city
        while R > 0:
            route1 = self.listRoutes[randint(0,len(self.listRoutes)-1)]
            route2 = self.listRoutes[randint(0,len(self.listRoutes)-1)]
            while route1 == route2 or (route1,route2) in pairList or (route2,route1) in pairList:
                route1 = self.listRoutes[randint(0,len(self.listRoutes)-1)]
                route2 = self.listRoutes[randint(0,len(self.listRoutes)-1)]
            pairList.append((route1,route2))
            R -= 1
            
        # Make the crossover
        for p in pairList:
            # Route length - first city - last city
            lenRoute = len(p[0].cityList)-1
            # Choose a random city (except the starting city: first and last in list)
            city = p[0].cityList[randint(1,lenRoute)]
            
            iRoute1 = p[0].cityList.index(city)
            iRoute2 = p[1].cityList.index(city)
            listCities = p[0].cityList[:]
            genRoute = []
            genRoute.append(city)
            
            canMove1 = True
            canMove2 = True
            while canMove1 or canMove2:
                # Must vary from 1 to lenRoute-1
                iRoute1 = (iRoute1-1) % lenRoute
                iRoute2 = (iRoute2+1) % lenRoute
                if canMove1:
                    if p[0].cityList[iRoute1] not in genRoute:
                        # Add the new city at the beginning of the generate list
                        listCities.remove(p[0].cityList[iRoute1])
                        genRoute.insert(0, p[0].cityList[iRoute1])
                    else:
                        canMove1 = False
                if canMove2:
                    if p[1].cityList[iRoute2] not in genRoute:
                        # Add the new city at the end of the generate list
                        listCities.remove(p[1].cityList[iRoute2])
                        genRoute.append(p[1].cityList[iRoute2])
                    else:
                        canMove2 = False
        
            # Add randomly the remaining listCities
            genRoute = genRandomCities(genRoute, lenRoute, listCities)
    
            # if the genRoute already exist, we generate a random route. So: no redundancy (no improvement)
            # while (genRoute in self.listRoutes):
            #     genRoute = []
            #     genRoute = genRandomCities(genRoute, lenRoute, listCities)
                        
            self.listRoutes.append(Route(genRoute))
    
    #@speedMeasure
    def mutation(self, stopRunning):
        ''' Process a mutation based on the 2opt method '''
        # Retrieve pe% of individuals (- the elite individual)
        R = int(self.initialRoutesNumber * (self.pe2/100.0)) - 1
        mutationPop = []
        
        # Allways add the elite individual
        mutationPop.append(self.listRoutes[0])
        self.listRoutes.remove(self.listRoutes[0])
        while R > 0:
            route1 = self.listRoutes[randint(0,len(self.listRoutes)-1)]
            while route1 in mutationPop:
                route1 = self.listRoutes[randint(0,len(self.listRoutes)-1)]
            mutationPop.append(route1)
            self.listRoutes.remove(route1)
            R -= 1
        
        # Find a mutation that minimize the length
        for route in mutationPop:
            for i in range(len(route.cityList)):
                for j in range(i+1,len(route.cityList)):
                    if stopRunning:
                        break
                    # Check if a cities inversion is better (Method give not good results)
                    #if self.gainSwapCities(route,i,j) > 0:
                    #    route = self.swapCities(route,i,(j)%len(route.cityList))
                    # Check if a route inversion is better
                    if self.gainSwapRoute(route,i,j) > 0:
                        route = self.swapRoute(route,i,(j+1)%len(route.cityList))
                if stopRunning:
                    break
            self.listRoutes.append(route)
            if stopRunning:
                break
            
    
    # ------------------------------ #
    # -- Tools algorithm methods -- #
    # ------------------------------ #
    
    
    def fac(self, n):
        ''' Return the factorial of a number 
        This functions is only needed if python version <= 2.5
        There is math.factorial available then ''' 
        p=1
        for i in range(1,n+1):
            p*=i
        return p

    def shake(self, initialList):
        ''' Return a list of index shaken ''' 
        indexList = []
        # The first element is allways the starting city
        indexList.append(0)

        for cpt in range(initialList-1):
            i = randint(1,initialList-1)
            while (i in indexList):
                i = randint(1,initialList-1)
            indexList.append(i)
        return indexList

    def maxPossibilities(self, lenCityList):
        ''' return the maximum number of different listRoutes '''
        #return math.factorial(lenCityList-1) # Works only with Python 2.6
        return self.fac(lenCityList-1)

    
    def sortListRoutesByLength(self):
        ''' Sort the routes by length '''
        self.listRoutes.sort(key=lambda r:r.len())
    
    def genRandomCities(self,genRoute, lenRoute, listCities):
        ''' Generate a random route from the cities of listCities '''
        while (len(genRoute)-1 < lenRoute):
            iCity = randint(0, len(listCities)-1)
            while listCities[iCity] in genRoute:
                iCity = randint(0, len(listCities)-1)
            genRoute.append(listCities[iCity])
        return genRoute
    
    def swapRoute(self,route,i,j):
        ''' Swap the route between i and j and return a new Route '''
        # Method 1
        tmp = route.cityList[i:j]
        tmpRoute = Route(route.cityList)
        tmpRoute.cityList[i:j] = tmp[::-1]
            
        # Method 2: OTHER SOLUTION (a bit slower)        
        # tmpRoute = Route(route.cityList)
        # tmpRoute.cityList[i:j] = route.cityList[i:j][::-1]
        return tmpRoute
    
    def swapCities(self,route,i,j):
        ''' Swap cities i and j and return a new Route '''
        tmpRoute = Route(route.cityList)
        tmpRoute.cityList[i], tmpRoute.cityList[j] = tmpRoute.cityList[j], tmpRoute.cityList[i]
        return tmpRoute
    
    def gainSwapRoute(self,route,i,j):
        ''' Process the gain between a swap of a route (between i to j) '''
        lenRoute = len(route.cityList)
        return dist2City(route.cityList[(i-1)%lenRoute], route.cityList[i]) + dist2City(route.cityList[(j+1)%lenRoute], route.cityList[j]) - (dist2City(route.cityList[(i-1)%lenRoute], route.cityList[j]) + dist2City(route.cityList[(j+1)%lenRoute], route.cityList[i]))
    
    def gainSwapCities(self,route,i,j):
        ''' Process the gain between a swap of 2 cities (i and j)'''
        lenRoute = len(route.cityList)
        tmp1 = dist2City(route.cityList[(i-1)%lenRoute], route.cityList[i]) + dist2City(route.cityList[(i+1)%lenRoute], route.cityList[i]) + dist2City(route.cityList[(j+1)%lenRoute], route.cityList[j]) + dist2City(route.cityList[(j-1)%lenRoute], route.cityList[j])
        tmp2 = dist2City(route.cityList[(i-1)%lenRoute], route.cityList[j]) + dist2City(route.cityList[(i+1)%lenRoute], route.cityList[j]) + dist2City(route.cityList[(j+1)%lenRoute], route.cityList[i]) + dist2City(route.cityList[(j-1)%lenRoute], route.cityList[i])
        return tmp1 - tmp2
        
        
        
class Resolution(threading.Thread):
    ''' Class called to solve the problem in a thread '''
    def __init__(self, listCities, gui):
        threading.Thread.__init__(self)
        self._stopevent = threading.Event()
        self.listCities = listCities
        self.gui = gui
        self.stopRunning = False
    
    def join(self, timeout = None):
        ''' Redefinition of the join method '''
        if timeout > 0:
            time.sleep(timeout)
            self._stopevent.set()
            self.stopRunning = True
        
    def run(self):
        ''' The main loop to solve the problem '''
        lastResults= [0,0]
        sd = sys.maxint
        genAlgo = GeneticAlgorithm(self.listCities, pe1)
        bestRoute = genAlgo.baseRoute
        genAlgo.generateRoutes()
        while(sd > 1 and not self._stopevent.isSet() and not self.stopRunning):
            genAlgo.selection()
            genAlgo.crossover()
            genAlgo.mutation(self.stopRunning)
            
            genAlgo.sortListRoutesByLength()
            
            # Process the standard deviation
            if not self.stopRunning:
                bestRoute = genAlgo.listRoutes[0]
                lastResults.pop()
                lastResults[1:] = lastResults[0:]
                lastResults[0] = bestRoute.len()
            
                sd = standardDeviation(lastResults)

            if self.gui:
                drawRoute(bestRoute)
        result.put(bestRoute)

#================================================
#              Main
#================================================

def main():
    global text
    usage =''' usage: %prog [options] [filename]
This script is intend to solve the Travel Salesman problem (TSP) problem.
        
[filename] is a file that contains the coordinates of the cities.
The format of this file is: NAME1 XPos1 YPos1
It is an optional argument.''' 
        
    parser = OptionParser(usage)
    parser.add_option("-n","--nogui", action="store_false", dest="gui", default=True, help="Do not use a graphical representation")
    parser.add_option("-m","--maxtime", type="int", dest="maxtime", default=0, help="Force the algorithm to stop after the given time (in seconds)")
    (options, args) = parser.parse_args()
        
    # Retrieve the options
    filename = None
    collecting = True
    if args<>[] and os.path.isfile(args[-1]):
        filename = args[-1]
        collecting = False
    else:
        if not options.gui:
            print "You cannot disabled the GUI and enter the points manually."
            sys.exit()
            
    if options.gui:
        initPygame()
    listCities = []
    while collecting:
        for event in pygame.event.get():
            if event.type == QUIT:
                sys.exit(0)
            elif event.type == KEYDOWN and event.key == K_RETURN:
                collecting = False
            elif event.type == MOUSEBUTTONDOWN:
                (x,y) = pygame.mouse.get_pos()
                listCities.append(City(x,y,"v" + str(len(listCities))))
                drawCities(listCities)
                
    ga_solve(filename, options.gui, options.maxtime, listCities)
        
    if options.gui:
        while True:
            event = pygame.event.wait()
            if event.type == KEYDOWN: break

#================================================
#              Methods
#================================================
def dist2City(city1, city2):
    ''' Return the distance between 2 listCities ''' 
    return math.sqrt((city1.x-city2.x)**2 + (city1.y-city2.y)**2)

def standardDeviation(tab):
    ''' Process and return the standard deviation ''' 
    moyenne = float(sum(tab)) / len(tab)
    et = sum([(t-moyenne)**2 for t in tab])
    return math.sqrt(et)

# ------------------ #
# -- GUI methods -- #
# ------------------ #

def initPygame():
    ''' Initialise Pygame '''
    global screen
    global font
    pygame.init() 
    window = pygame.display.set_mode((screen_x, screen_y)) 
    pygame.display.set_caption('Exemple') 
    screen = pygame.display.get_surface() 
    font = pygame.font.Font(None,30)

def drawCities(listCities):
    ''' Draw all cities with a circle '''
    screen.fill(0)
    [pygame.draw.circle(screen,city_color,(c.x,c.y),city_radius) for c in listCities]
    text = font.render("Nombre: %i" % len(listCities), True, font_color)
    textRect = text.get_rect()
    screen.blit(text, textRect)
    pygame.display.flip()

def drawRoute(route):
    ''' Draw the route with lines and display its length '''
    screen.fill(0)
    pos = []
    [pos.append((c.x,c.y)) for c in route.cityList]
    [pygame.draw.lines(screen,city_color,True,pos) for c in pos]
    text = font.render("Length = "+str(route.len()) , True, font_color)
    textRect = text.get_rect()
    screen.blit(text, textRect)
    pygame.display.flip()

def notTooBadSorting(listCities):
    ''' Just for begin with a first route "not too bad". Generate a route looking "each nearest" city WITHOUT complexe check ! ''' 
    newCities = []
    newCities.append(listCities[0])
    [newCities.append(newCities[i-1].nearest(listCities,newCities)) for i in range(len(listCities)) if i <> 0]
    return newCities

#@speedMeasure
def ga_solve(file=None, gui=True, maxtime=None, listCities=None):
    ''' Resolution of the city traveller problem ''' 

    if file != None:
        f = open(file,"r")
        listCities = [City(int(l.split(" ")[1]),int(strip(l.split(" ")[2])),l.split(" ")[0]) for l in f]
    
    resolution = Resolution(listCities, gui)
    resolution.start()
    resolution.join(maxtime)
        
    # Retrieve the best route from the queue
    bestRoute = result.get()
    return (bestRoute.len(), [c.name for c in bestRoute.cityList[:]])

if __name__ == '__main__':
    main()
