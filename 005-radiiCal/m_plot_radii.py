import matplotlib.pyplot as plt
import csv
import argparse

p = argparse.ArgumentParser()

p.add_argument('--radii_f_path', '-r', type=str, default="channel_radii.dat", help="The path of radii file.")

args = p.parse_args()

X = []
Y = []

with open(args.radii_f_path, 'r') as datafile:
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