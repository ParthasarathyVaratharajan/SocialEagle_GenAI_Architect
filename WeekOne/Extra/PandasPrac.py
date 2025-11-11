import pandas as pd
import matplotlib.pyplot as plt

data = {
  "calories": [420, 380, 390],
  "duration": [50, 40, 45]
}

#load data into a DataFrame object:
df = pd.DataFrame(data)

print(df) 

df = pd.read_csv('data.csv')
df.dropna(inplace = True)
print(df.to_string()) 


df.plot(kind = 'scatter', x = 'Duration', y = 'Calories')
plt.show()