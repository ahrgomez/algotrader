import numpy as np
import warnings
warnings.filterwarnings(action="ignore", module="scipy", message="^internal gelsd")
import sys

class SupportsAndResistences():

    RANGE_LENGTH = 10
    RANGE_VALUE = 0.010
    ELEMENTS_COUNT = 670

    def Calculate(self, data):
        lowData = [row.mid.l for row in data]
        highData = [row.mid.h for row in data]
        
        lowRanges = self.getRanges(lowData)
        highRanges = self.getRanges(highData)

        values = []
        values.extend(self.getRangesMinValues(lowRanges))
        values.extend(self.getRangesMaxValues(highRanges))

        supportAndResistences = []

        while(len(values) > 0):
            maxOfValues = np.amax(values)
            points, values = self.calculateResistencePointsArrayAndStrength(values, maxOfValues)
            supportAndResistences.append(maxOfValues)

        return np.sort(supportAndResistences)

    def getRanges(self, data):
        chunks = [data[x:x+self.RANGE_LENGTH] for x in range(0, len(data), self.RANGE_LENGTH)]
        return chunks

    def getRangesMaxValues(self, ranges):
        maxValues = []
        for x in range(0, len(ranges), 1):
            maxValueRange = ranges[x]
            max = np.amax(maxValueRange)
            maxValues.append(max);
        return maxValues

    def calculateResistencePointsArrayAndStrength(self, maxValues, maxOfMaxValues):
        resistencePointsArray = [maxOfMaxValues]
        maxValues.remove(maxOfMaxValues);
        inRangeValue = maxOfMaxValues * self.RANGE_VALUE
        minRangeValue = maxOfMaxValues - inRangeValue
        maxRangeValue = maxOfMaxValues + inRangeValue

        for x in range(0, len(maxValues), 1):
            val = maxValues[x]

            if val > minRangeValue and val < maxRangeValue:
                resistencePointsArray.append(val)

        for x in range(0, len(resistencePointsArray), 1):
            val = resistencePointsArray[x]

            if val in maxValues:
                maxValues.remove(val)

        return resistencePointsArray, maxValues

    def getRangesMinValues(self, ranges):
        minValues = []
        for x in range(0, len(ranges), 1):
            minValueRange = ranges[x]
            min = np.amin(minValueRange)
            minValues.append(min);
        return minValues

    def calculateSupportPointsArrayAndStrength(self, minValues, minOfMinValues):
        supportPointsArray = [minOfMinValues]
        minValues.remove(minOfMinValues);
        inRangeValue = minOfMinValues * self.RANGE_VALUE
        minRangeValue = minOfMinValues - inRangeValue
        maxRangeValue = minOfMinValues + inRangeValue

        for x in range(0, len(minValues), 1):
            val = minValues[x]

            if val > minRangeValue and val < maxRangeValue:
                supportPointsArray.append(val)

        for x in range(0, len(supportPointsArray), 1):
            val = supportPointsArray[x]

            if val in minValues:
                minValues.remove(val)

        return supportPointsArray, minValues