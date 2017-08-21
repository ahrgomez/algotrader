def priceInRange(price, num1, num2):
    minValue = num1
    maxValue = num2

    if num1 < num2:
        minValue = num1
        maxValue = num2
    else:
        minValue = num2
        maxValue = num1

    return minValue <= price <= maxValue