import pyautogui
import time
import random
letters = "qwertyuiopasdfghjklzxcvbnm"
time.sleep(5)
while True:
    word = "".join([letters[random.randint(0,len(letters)-1)] for i in range(random.randint(3,10))])
    pyautogui.write(word)
    pyautogui.press(["enter"])