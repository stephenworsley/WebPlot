import argparse
import json
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import matplotlib
from math import pi
import numpy as np
import datetime

def cleanConfig(config):
    if 'title' not in config:
        config['title'] = ''
    if 'axes' not in config:
        raise Exception("'axes' does not exist in config file.")
    else:
        if type(config['axes']) is not list:
            raise Exception("'axes' should be a list. 'axes' had type: {}".format(type(config['axes'])))
    if 'groups' not in config:
        raise Exception("'groups' does not exist in config file.")
    if type(config['groups']) is not dict:
        raise Exception("'groups' should be a dict. 'axes' had type: {}".format(type(config['groups'])))
    if 'animated' not in config:
        config['animated'] = False
    if type(config['animated']) is not bool:
        raise Exception("'animated' should be a bool value. 'animated' had type {}".format(type(config['animated'])))
    if 'colormap' not in config:
        config['colormap'] = 'tab20'
    if 'frame_length' not in config:
        config['frame_length'] = 400

    date_dict = dict()
    frames_missing = False
    has_frames = False
    name_list = []
    data_set = set()
    for group, content in config['groups'].items():
        if type(content) is not dict:
            raise Exception("{0} should be a dict. {0} had type: {1}".format(type(content),group))
        if 'name' not in content:
            content['name'] = group
        if content['name'] not in name_list:
            name_list.append(content['name'])
        if 'data' not in content:
            raise Exception("'data' does not exist in group '{}'.".format(group))
        if type(content['data']) is not list:
            raise Exception("'data' in group '{}' is not a list")
        if len(content['data']) != len(config['axes']):
            raise Exception("the size of data in group '{}' conflicts with the number of axes"
                            .format(group))
        for x in content['data']:
            if not isinstance(x,(int, float)):
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
                # if content['frame'] < 0
                #     raise Exception ("'frame' in group {} is negative".format(group))
                has_frames = True
            else:
                frames_missing = True
        else:
            content['frame'] = 0
    if 'max' not in config:
        config['max'] = max(data_set) + 1
    if 'min' not in config:
        config['min'] = min(data_set) - 1

    if config['animated']:
        if has_frames and frames_missing:
            raise Exception("frame data is incomplete")
        i = 0
        for date in sorted(date_dict, key=lambda date: datetime.datetime.strptime(date, "%d/%m/%Y")):
            group_list = date_dict[date]
            if not has_frames:
                for group in group_list:
                    config['groups'][group]['frame'] = i
                i += 1

    cm =  matplotlib.cm.get_cmap(config['colormap'])
    palette = [matplotlib.colors.to_rgb(cm(x/len(name_list))) for x in range(len(name_list))]
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
            normalized_color = matplotlib.colors.to_rgb(content['color'])
            color_set.add(normalized_color)
            if (normalized_color,content['frame']) in color_frame_dict:
                raise Exception("group '{}' has shares a conflicting color with group '{}'"
                                .format(group,color_frame_dict[(normalized_color,content['frame'])]))
            else:
                color_frame_dict[(normalized_color,content['frame'])] = group

            if content['name'] in name_color_dict:
                if content['color'] != name_color_dict[content['name']]:
                    raise Exception("the group name '{}' is assigned two different colors"
                                    .format(content['name']))
            else:
                name_color_dict[content['name']] = content['color']
        if (content['name'],content['frame']) in name_frame_set:
            raise Exception("two groups share the name '{}' and the frame '{}'"
                            .format(content['name'],content['frame']))
        else:
            name_frame_set.add((content['name'],content['frame']))

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
    frame_dict = dict()
    for group, content in config['groups'].items():
        frame_dict.setdefault(content['frame'],[]).append(group)
    ordered_frame_list = sorted(frame_dict)
    min = ordered_frame_list[0]
    max = ordered_frame_list[-1]
    total_frame_list = [frame_dict[frame+min] if frame+min in frame_dict else (frame,[])
                        for frame in range(max-min+1)]
    return total_frame_list


def parseCommands():
    parser = argparse.ArgumentParser()
    parser.add_argument("-c", "--config", type=str,
                        help="config file")
    parser.add_argument("-s", "--save", type=str,
                        help="save plot as an image")
    args = parser.parse_args()
    return args


def setConfig(args):
    with open(args.config) as json_file:
        config = json.load(json_file)
    cleanConfig(config)
    return config


def main():
    args = parseCommands()
    config = setConfig(args)
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
            polygon_coords = np.array(list(zip(angles,values)))

            polygon = matplotlib.patches.Polygon(polygon_coords, color=patch_color, alpha=0.4)
            ax.add_patch(polygon)
        plt.draw()

    update_fig(0)

    if config['animated']:
        ani = animation.FuncAnimation(fig, update_fig, len(frame_list), interval=config['frame_length'])


    if args.save is None:
        plt.show()
    else:
        if config['animated']:
            plt.savefig(args.save, format='png')
        else:
            ani.save(args.save)


main()
