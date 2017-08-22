import numpy as np

def priceInRange(price, num1, num2):
    minValue = num1
    maxValue = num2

    if num1 < num2:
        minValue = num1
        maxValue = num2
    else:
        minValue = num2
        maxValue = num1

    result = np.isclose(price, [minValue, maxValue,], atol=0.0005)

    return result[0] or result[1]