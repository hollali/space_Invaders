import pygame
import random
import math
from pygame import mixer

#* Initialize the pygame
pygame.init()

#* Create the screen
screen = pygame.display.set_mode((800,600))

#*background
background = pygame.image.load('./images/space_image.jpg')

#*Background sound 
mixer.music.load('./sounds/background.wav')
mixer.music.play(-1)

#* Tittle and Icon
pygame.display.set_caption("Space Invaders")
icon = pygame.image.load('./images/space.png')
pygame.display.set_icon(icon)

#* Player
playerImg = pygame.image.load('./images/arcade-game(1).png')
playerX = 380
playerY = 480
playerX_change = 0 

#*Enemy
enemyImg = []
enemyX = []
enemyY = []
enemyX_change = []
enemyY_change = []
num_of_enemies = 4

for i in range(num_of_enemies):
    enemyImg.append(pygame.image.load('./images/alien.png'))  
    enemyX .append(random.randint(0, 755)) 
    enemyY .append(random.randint(50, 150))
    enemyX_change .append(-1) 
    enemyY_change .append(40)

#*Bullet
bulletImg = pygame.image.load('./images/bullet.png')
bulletX = 0 
bulletY = 480
bulletX_change = 0
bulletY_change = 10
bullet_state = "ready"


#*Score
#
score_value = 0 
font = pygame.font.Font('freesansbold.ttf',32)

textX = 10
textY = 10

#* Game over
over_font = pygame.font.Font('freesansbold.ttf',64)

#!FUNCTIONS
#* Score Function
def show_score(x,y):
    score = font.render("Score : " + str(score_value), True ,(255,255,255))
    screen.blit(score, (x, y))

#*Game over Function
def game_over_text():
    over_text = over_font.render("GAME OVER", True,(255,255,255))
    screen.blit(over_text, (200, 250))

#*Player Functions
def player (x,y):
    screen.blit(playerImg, (x,y))

#* Enemies Functions
def enemy (x , y, i):
    screen.blit(enemyImg[i], (x,y))

#*Bullet Functions
def  fire_bullet(x,y):
    global bullet_state
    bullet_state = "fire"
    screen.blit(bulletImg,(x + 16, y + 10))

#* Collision Functions
def isCollision(enemyX,enemyY,bulletX,bulletY):
    distance = math.sqrt(math.pow(enemyX-bulletX,2)+(math.pow(enemyY-bulletY,2)))
    if distance < 27:
        return True
    else:
        return False

#*Game Loop
running = True
while running:

    #* RGB 
    screen.fill((0,0,0))

    #*Background image
    screen.blit(background,(0, 0))

    for event in pygame.event.get (): 
        if event.type == pygame.QUIT:
            running = False

        #*if  keystroke  check whether is is right or left     
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_LEFT:
                playerX_change = -1.5
            if event.key == pygame.K_RIGHT:
                playerX_change = 1.5
        if event.type == pygame.KEYUP:
            if event.key == pygame.K_LEFT or event.key == pygame.K_RIGHT:
                playerX_change = 0
            if event.key == pygame.K_SPACE:
                if bullet_state == "ready":
                    bullet_Sound = mixer.Sound('./sounds/laser.wav')
                    bullet_Sound.play()
                    bulletX = playerX 
                    fire_bullet(playerX,bulletY)


    # 5 = 5 + 0.1 -> 5 = 5 - 0.1
    # 5 = 5 + 0.1

    #* Checking for boundaries
    playerX += playerX_change

    if playerX <= 0:
        playerX = 0
    elif playerX >= 766: 
        playerX = 766

    #* Enemy movement
    for i in range (num_of_enemies):

        # Game Over
        if enemyY[i] > 440:
            for j in range (num_of_enemies):
                enemyY[j] = 2000
            game_over_text()
            break    
        enemyX[i] += enemyX_change[i]
        if enemyX[i] <= 0:
            enemyX_change[i]= 0.6
            enemyY[i] += enemyY_change[i]
        elif enemyX[i] >= 766:
            enemyX [i]= -0.6
            enemyY[i] += enemyY_change[i] 
        
            #* Collision
        collision = isCollision (enemyY[i], enemyY[i] ,bulletX ,bulletY )#     
        if collision :
            explosion_Sound = mixer.Sound('./sounds/explosion.wav')
            explosion_Sound.play()
            bulletY = 480
            bullet_state = "ready"
            score_value += 1
            enemyX[i] = random.randint(0, 755)
            enemyY[i] = random.randint(50, 150)        
        
        enemy(enemyX[i], enemyY[i], i)
    #*Bullet Movement
    if bulletY <= 0:
        bulletY = 480
        bullet_state = "ready"

    if bullet_state == "fire":
        fire_bullet(bulletX,bulletY)
        bulletY -= bulletY_change

    

    player(playerX,playerY)
    show_score(textX, textY)
    pygame.display.update() 