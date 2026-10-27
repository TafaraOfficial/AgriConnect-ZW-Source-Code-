import pandas as pd
from sklearn.linear_model import LinearRegression

data = {
    "month":[1,2,3,4,5,6],
    "price":[10,12,13,15,17,18]
}

df = pd.DataFrame(data)

X = df[["month"]]
y = df["price"]

model = LinearRegression()
model.fit(X,y)

prediction = model.predict(pd.DataFrame({"month": [7]}))

print(
    f"Predicted July Price: {prediction[0]}"
)