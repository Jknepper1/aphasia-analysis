import pandas as pd
import matplotlib.pyplot as plt

sheet = pd.read_csv("batchVHuman.csv")

# print(sheet.dtypes)

relevant_columns = sheet[["File", "Words_Min"]]
# Iterates over each column and uses file name to identify batch rows and 
# Extracts its associated columns. List order will match sheet order 

x_cords = []
y_cords = []
rowNum = len(relevant_columns)
for i in range(rowNum):
    if ("B-" in relevant_columns["File"][i]):
        x_cords.append(relevant_columns["Words_Min"][i])
    else:
        y_cords.append(relevant_columns["Words_Min"][i])

# print(x_cords)
# print(y_cords)
# cords = list(zip(x_cords, y_cords))

# Utilize matplotlib's pyplot to scatter plot the two lists 
plt.scatter(x_cords, y_cords)
plt.xlabel("Batch")
plt.ylabel("Human")
plt.title("Words_Min")
plt.show()