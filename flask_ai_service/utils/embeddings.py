import math

def embed(text):
    v=[0.0]*24
    for i,ch in enumerate(text.lower()):
        v[i%24]+=((ord(ch)%29)/29.0)
    return v

def cosine(a,b):
    d=sum(x*y for x,y in zip(a,b))
    na=math.sqrt(sum(x*x for x in a))
    nb=math.sqrt(sum(y*y for y in b))
    return d/((na*nb) or 1)
