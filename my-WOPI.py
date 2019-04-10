import argparse
import json
import matplotlib.pyplot as plt
import matplotlib
from math import pi
import numpy as np

def checkConfig(config):
    if type(config['axes']) is not list:
        raise Exception("'axes' should be a list. 'axes' was: {}".format(type(config['axes'])))
    if type(config['values']) is not list:
        raise Exception("'values' should be a list. 'values' was: {}".format(type(config['values'])))
    if len(config['values']) != len(config['axes']):
        raise Exception("Length of 'axes' and 'values' should be the same. Length of 'axes' was {}, "
                        "length of 'values' was {}".format(len(config['values']), len(config['axes'])))

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-c", "--config", type=str,
                        help="config file")
    parser.add_argument("-s", "--save", type=str,
                        help="save plot as an image")
    args = parser.parse_args()

    with open(args.config) as json_file:
        config = json.load(json_file)
    checkConfig(config)

    number_of_axes = len(config['axes'])
    angle = 2*pi / number_of_axes
    angles = [angle*x for x in range(number_of_axes)]
    # angles2 = [angle*x for x in range(number_of_axes+1)]
    values = config['values']
    # values2 = true_values + true_values[:1]
    labels = config['axes']

    polygon_coords = np.array(list(zip(angles,values)))

    ax = plt.subplot(111, polar=True)
    plt.xticks(angles, labels)
    plt.title(config['title'])
    polygon = matplotlib.patches.Polygon(polygon_coords, alpha=0.1)
    ax.add_patch(polygon)
    # ax.plot(angles2, values2)
    # ax.fill(angles2, values2, 'b', alpha=0.1)
    ax.set_rmax(5)

    if args.save is None:
        plt.show()
    else:
        plt.savefig(args.save, format='png')






main()

#if __name__ == "__main_":
#    main()