import urllib.request
import random

url = 'https://raw.githubusercontent.com/dwyl/english-words/master/words_alpha.txt'

response = urllib.request.urlopen(url)

lines = response.readlines()
lines = [l.decode().strip() for l in lines]
lines =[l for l in lines if len(l) in [4, 5, 6, 7, 8]]

ok = 'qwertasdfgzxcvb'

def checker(word):
  return word == ''.join([c for c in word if c in ok])

bingo = [word for word in lines if checker(word)]

winners = random.sample(bingo, 2)

for i in range(100):
  print('.'.join([word.title() for word in random.sample(bingo, 2)]))
