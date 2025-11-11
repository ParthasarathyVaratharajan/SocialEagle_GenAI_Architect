from numpy import random
import numpy as np

#Random Numbers
x = random.randint(100)
print(x)
x = random.rand()
print(x)    
x = random.randint(100, size=(5))
print(x)
x = random.randint(100, size=(3, 5))    
print(x)
x = random.rand(3, 5)      
print(x)
x = random.choice([3, 5, 7, 9])
print(x)
x = random.choice([3, 5, 7, 9], size=(3, 5))
print(x)

#Random Data Distribution
x = random.normal(loc=1.0, scale=0.5, size=(2, 3))
print(x)
x = random.binomial(n=10, p=0.5, size=10)
print(x)
x = random.poisson(lam=3.0, size=10)
print(x)
x = random.uniform(low=0.0, high=1.0, size=(2, 3))
print(x)

x = random.choice([3, 5, 7, 9], p=[0.1, 0.3, 0.6, 0.0], size=(100))
print(x)

#Random Permutations
arr = np.array([1, 2, 3, 4, 5])
random.shuffle(arr)
print(arr)

arr = np.array([1, 2, 3, 4, 5])
print(random.permutation(arr))