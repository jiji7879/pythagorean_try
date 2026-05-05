import math
def find_triplet(arr):
    n = len(arr)
    # Iterate through all possible triplets
    
    for i in range(n - 2):
        for j in range(i + 1, n - 1):
            low_sum = arr[i]+arr[j]
            for k in range(j + 1, n):
                
                # Check if sum of two elements 
                # equals the third element
                
                if low_sum == arr[k]:
                    print(i, j, k)
                    return True
                elif low_sum < arr[k]:
                    break
    return False

arr = []
#p=3*5*7*11*13*17*19
p=3*5*7*11*13
for x in range(1, p):
    c = x*x * (p*p-x*x)
    if c < 0:
        print("Hey!")
        print(x, c, p)
    arr.append(math.sqrt(c))
find_triplet(arr)
