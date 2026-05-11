from fractions import Fraction
import math, itertools, collections, time
def pyth_sines(max_h):
    vals=set()
    triples=[]
    for m in range(2,int(math.sqrt(max_h))+2):
        for n in range(1,m):
            if ((m-n)&1)==1 and math.gcd(m,n)==1:
                a=m*m-n*n
                b=2*m*n
                c=m*m+n*n
                if c<=max_h:
                    for leg in (a,b):
                        vals.add(Fraction(leg,c))
                        triples.append((Fraction(leg,c),(leg,c),(a,b,c),m,n))
    return vals,triples

if __name__=="__main__":
    vals,triples=pyth_sines(20000)

    vals_list=sorted(vals)
    vals_set=set(vals_list)
    solutions=[]
    for i,x in enumerate(vals_list):
        for y in vals_list[i:]:
            z=x+y
            if z>=1: break
            if z in vals_set:
                solutions.append((x,y,z))
                if len(solutions)>=50:
                    break
        if len(solutions)>=50: break

    for s in solutions:
        print(s)
