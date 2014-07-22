from os import path
from glob import glob

import random
import threading
import time

import pygame
import pygame.mixer

class Arcanum(object):

    def __init__(self, dataPath):

        self.dataPath = dataPath

        self.size = (1440, 900)
        self.screen = None

    def GetFile(self, relativePath):

        return path.join(self.dataPath, relativePath)

    def Run(self):

        self.Prepare()

        self.HandleLoading()

        self.HandleMenu()

    def Prepare(self):

        pygame.init()

        self.screen = pygame.display.set_mode(self.size)

    def HandleMenu(self):

        menuMusicPath = self.GetFile("modules/Arcanum/sound/music/Arcanum.mp3")
        pygame.mixer.music.load(menuMusicPath)
        pygame.mixer.music.play(-1)

        menuImagePath = self.GetFile("data/art/interface/MainMenuBack.png")
        menuImage = pygame.image.load(menuImagePath)
        self.RenderBackground(menuImage)

        while 1:
            for event in pygame.event.get():

                if event.type == pygame.QUIT:
                    return

                if event.type == pygame.KEYUP:

                    if event.key == pygame.K_ESCAPE:
                        return

    def HandleLoading(self):

        # Start playing video while loading stuff
        video =  self.PlayVideo("data/movies/SierraLogo.mpg")

        loadingThread = threading.Thread(target = self.Load)
        loadingThread.start()

        splash = self.GetSplashScreen("data/art/splash")

        sierraLogoFinished = False
        troikaLogoFinished = False
        loadingFinished = False

        while True:

            if not sierraLogoFinished and not video.get_busy():
                sierraLogoFinished = True
                video = self.PlayVideo("data/movies/TroikaLogo.mpg")

            if sierraLogoFinished and not troikaLogoFinished and not video.get_busy():
                troikaLogoFinished = True
                self.RenderBackground(splash)

            if sierraLogoFinished and troikaLogoFinished and not loadingFinished and not loadingThread.is_alive():
                loadingFinished = True
                video = self.PlayVideo("modules/Arcanum/movies/50000.mpg")

            if loadingFinished and not video.get_busy():
                break

            for event in pygame.event.get():

                if event.type == pygame.MOUSEBUTTONUP or event.type == pygame.KEYUP:
                    if video.get_busy():
                        video.stop()
                        pygame.mixer.music.stop()

    def GetSplashScreen(self, splashesSubFolder):

        splashesFolder = self.GetFile(splashesSubFolder)
        splashPaths = glob(path.join(splashesFolder, "*.bmp"))

        splashPath = random.choice(splashPaths)

        return pygame.image.load(splashPath)

    def RenderBackground(self, background):

        position = self.CalculateCenterPosition(background.get_size())

        self.screen.fill((0,0,0))
        self.screen.blit(background, position)
        pygame.display.flip()

    def Load(self):

        time.sleep(10)

    def CalculateCenterPosition(self, objectSize):

        def CalculateCenterPositionOnAxis(containerValue, objectValue):
            return (containerValue / 2) - (objectValue / 2) if objectValue < containerValue else 0

        objectXPosition = CalculateCenterPositionOnAxis(self.size[0], objectSize[0])
        objectYPosition = CalculateCenterPositionOnAxis(self.size[1], objectSize[1])

        return objectXPosition, objectYPosition

    def PlayVideo(self, relativeVideoPath):

        videoPath = self.GetFile(relativeVideoPath)

        video = pygame.movie.Movie(videoPath)
        position = self.CalculateCenterPosition(video.get_size())
        video.set_display(self.screen, position)
        video.set_volume(0)

        pygame.mixer.music.load(videoPath)

        self.screen.fill((0,0,0))

        video.play()
        pygame.mixer.music.play()

        return video