import matplotlib.pyplot as plt
import csv

X = []
Y = []

with open(r'channel_radii.dat', 'r') as datafile:
    plotting = csv.reader(datafile, delimiter=' ', skipinitialspace=True)
    next(plotting)

    for ROWS in plotting:
        # print("#: ", ROWS[0])
        X.append(float(ROWS[0]))
        Y.append(float(ROWS[1]))


# plt.scatter(X, Y)
plt.plot(X, Y)
# plt.title('Radii calculation')
plt.xlabel('Reaction coordinates (Å)')
plt.ylabel('Radii (Å)')
plt.autoscale()
plt.show()