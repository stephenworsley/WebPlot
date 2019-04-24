import argparse
import json
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import matplotlib
from math import pi
import numpy as np
import datetime


def parseCommands():
    """
    Parses commands from the command line.

    Returns:
    * argparse.ArgumentParser object
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("-c", "--config", type=str,
                        help="config file")
    parser.add_argument("-s", "--save", type=str,
                        help="save plot as an image")
    args = parser.parse_args()
    return args


def setConfig(config_file):
    """
    Reads config file location from args, extracts json file to dict.

    Args:

    * args ()

    Returns:
        dict
    """
    with open(config_file) as json_file:
        config = json.load(json_file)
    cleanConfig(config)
    return config


def checkType(dict_, key, type_):
    if type(dict_[key]) is not type_:
        raise Exception("{0} does not have type {1}. {0} had type {2}".format(key, type_, type(dict_[key])))


def cleanConfig(config):
    """
    Cleans the configuration data and raises exceptions where appropriate.

    Args:

    * config (dict)
    """
    if 'title' not in config:
        config['title'] = ''
    checkType(config, 'title', str)
    if 'axes' not in config:
        raise Exception("'axes' does not exist in config file.")
    checkType(config, 'axes', list)
    if len(config['axes']) == 0:
        raise Exception("'axes' should contain at least one axis.")
    if 'groups' not in config:
        raise Exception("'groups' does not exist in config file.")
    checkType(config, 'groups', dict)
    if 'animated' not in config:
        config['animated'] = False
    checkType(config, 'animated', bool)
    if 'colormap' not in config:
        config['colormap'] = 'tab20'
    if 'frame_length' not in config:
        config['frame_length'] = 400
    checkType(config, 'frame_length', int)

    date_dict = dict()
    frames_missing = False
    has_frames = False
    name_set = set()
    data_set = set()
    for group, content in config['groups'].items():
        if type(content) is not dict:
            raise Exception("{0} should be a dict. {0} had type: {1}".format(type(content), group))
        if 'name' not in content:
            content['name'] = group
        name_set.add(content['name'])
        if 'data' not in content:
            raise Exception("'data' does not exist in group '{}'.".format(group))
        if type(content['data']) is not list:
            raise Exception("'data' in group '{}' is not a list")
        if len(content['data']) != len(config['axes']):
            raise Exception("the size of data in group '{}' conflicts with the number of axes"
                            .format(group))
        for x in content['data']:
            if not isinstance(x, (int, float)):
                raise Exception("data in group'{}' is not numerical".format(group))
            data_set.add(x)
        if config['animated']:
            if not ('date' in content or 'frame' in content):
                raise Exception("insufficient data in group '{}' to assign a frame"
                                .format(group))
            if 'date' in content:
                date_dict.setdefault(content['date'], []).append(group)
            if 'frame' in content:
                if type(content['frame']) is not int:
                    raise Exception("'frame' in group {} does not have type int".format(group))
                has_frames = True
            else:
                frames_missing = True
        else:
            content['frame'] = 0
    if 'max' not in config:
        config['max'] = int(max(data_set) + 1)
    if 'min' not in config:
        config['min'] = int(min(data_set) - 1)
        if config['min'] > 0:
            config['min'] = 0

    if config['animated']:
        if has_frames and frames_missing:
            raise Exception("'frame' data is incomplete")
        # if frames_missing is True and an exception has not been raised then all groups must have dates.
        # 'frame' data is then assumed to be in chronological order and the config file is updated accordingly.
        if not has_frames:
            i = 0
            for date in sorted(date_dict, key=lambda date: datetime.datetime.strptime(date, "%d/%m/%Y")):
                group_list = date_dict[date]

                for group in group_list:
                    config['groups'][group]['frame'] = i
                i += 1

    # if no color is specified for a group then one will be assigned. If there is a group with the same name which
    # already has a color, this one will be assigned, otherwise one will be chosen using the specified colormap.
    # Colors must be the same for all groups with the same name. Colors must be distinct on each frame.
    cm = matplotlib.cm.get_cmap(config['colormap'])
    palette = [matplotlib.colors.to_rgb(cm(x / len(name_set))) for x in range(len(name_set))]
    color_set = set()
    color_frame_dict = dict()
    name_color_dict = dict()
    name_frame_set = set()
    for group, content in config['groups'].items():

        if 'color' not in content:
            content['color'] = 'default'
        elif content['color'] != 'default':
            if not matplotlib.colors.is_color_like(content['color']):
                raise Exception("group '{}' does not have a valid color.".format(group))
            # Colors are normalized to rgb so they can be compared.
            normalized_color = matplotlib.colors.to_rgb(content['color'])
            color_set.add(normalized_color)
            if (normalized_color, content['frame']) in color_frame_dict:
                raise Exception("group '{}' has shares a conflicting color with group '{}'"
                                .format(group, color_frame_dict[(normalized_color, content['frame'])]))
            else:
                color_frame_dict[(normalized_color, content['frame'])] = group
            if content['name'] in name_color_dict:
                if content['color'] != name_color_dict[content['name']]:
                    raise Exception("the group name '{}' is assigned two different colors"
                                    .format(content['name']))
            else:
                name_color_dict[content['name']] = content['color']
        if (content['name'], content['frame']) in name_frame_set:
            raise Exception("two groups share the name '{}' and the frame '{}'"
                            .format(content['name'], content['frame']))
        else:
            name_frame_set.add((content['name'], content['frame']))
    for group, content in config['groups'].items():
        if content['color'] == 'default':
            if content['name'] in name_color_dict:
                content['color'] = name_color_dict[content['name']]
            else:
                color_assigned = False
                for col in palette:
                    if col not in color_set:
                        content['color'] = col
                        name_color_dict[content['name']] = col
                        color_set.add(col)
                        color_assigned = True
                        break
                if not color_assigned:
                    raise Exception("insufficient colors in colormap '{}'".format(config['colormap']))


def orderFrames(config):
    """
    Extracts a list of lists of groups, ordered by their frames.

    If a frame in between the start and end has no group with that frame, an empty list will be placed in that position.

    Args:
        config (dict)
    Returns:
        list
    """
    frame_dict = dict()
    for group, content in config['groups'].items():
        frame_dict.setdefault(content['frame'], []).append(group)
    ordered_frame_list = sorted(frame_dict)
    min_ = ordered_frame_list[0]
    max_ = ordered_frame_list[-1]
    total_frame_list = [frame_dict[frame+min_] if frame+min_ in frame_dict else []
                        for frame in range(max_-min_+1)]
    return total_frame_list


def main():
    """Reads a config file specified in the command line and creates a radar plot from the data."""
    args = parseCommands()
    config = setConfig(args.config)
    frame_list = orderFrames(config)

    number_of_axes = len(config['axes'])
    angle = 2*pi / number_of_axes
    angles = [angle*x for x in range(number_of_axes)]
    labels = config['axes']
    fig = plt.figure()
    ax = plt.subplot(111, polar=True, animated=False)

    def update_fig(i):
        ax.clear()
        plt.xticks(angles, labels)
        plt.title(config['title'])
        ax.set_rmax(config['max'])
        ax.set_rmin(config['min'])

        group_list = frame_list[i]
        for group in group_list:
            patch_color = config['groups'][group]['color']
            values = config['groups'][group]['data']
            polygon_coords = np.array(list(zip(angles, values)))

            polygon = matplotlib.patches.Polygon(polygon_coords, color=patch_color, alpha=0.4,
                                                 label=config['groups'][group]['name'])
            ax.add_patch(polygon)
        ax.legend(loc='lower right')
        plt.draw()

    update_fig(0)

    if config['animated']:
        ani = animation.FuncAnimation(fig, update_fig, len(frame_list), interval=config['frame_length'], repeat=True)

    if args.save is None:
        plt.show()
    else:
        if not config['animated']:
            plt.savefig(args.save, format='png')
        else:
            ani.save(args.save)


if __name__ == "__main__":
    main()
