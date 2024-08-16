import random 
def genotp():
    otp=''
    Caps=[chr(i) for i in range(ord('A'),ord('Z')+1)] #list comprehension
    sma=[chr(i) for i in range(ord('a'),ord('z')+1)]
    for i in range(0,2):
        otp=otp+random.choice(Caps)  #to get 1 large character in alphabetic
        otp=otp+str(random.randint(0,9)) # to get 1 char in alphabetic
        otp=otp+random.choice(sma) # to get 1 small char in alphabetic
    return otp
