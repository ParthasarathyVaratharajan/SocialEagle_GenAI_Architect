import matplotlib.pyplot as plt
import seaborn as sns
from numpy import random


#sns.displot([0, 1, 2, 3, 4, 5])
#plt.show()

#sns.displot([0, 1, 2, 3, 4, 5], kind="kde")
#plt.show()


#sns.displot(random.normal(size=1000), kind="kde")
#plt.show()


x = random.normal(loc=1, scale=2, size=(2, 3))
print(x)

x = random.binomial(n=10, p=0.5, size=10)
print(x)

#sns.displot(random.binomial(n=10, p=0.5, size=1000))
#plt.show()

data = {
  "normal": random.normal(loc=50, scale=5, size=1000),
  "binomial": random.binomial(n=100, p=0.5, size=1000),
  "poisson": random.poisson(lam=50, size=1000)
}

sns.displot(data, kind="kde")
plt.show()

#sns.displot(random.poisson(lam=2, size=1000))
#plt.show()