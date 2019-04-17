import json

# class Config
#     def __init__(self, )

def save_json(j_dict, file):
    with open(file, 'w') as outfile:
        json.dump(j_dict,outfile)


def write_heli_data(angles, blades, blade_length=8, fat=True):
    blade_offsets = [int(angles*x/blades) for x in range(blades)]
    base = [1 for x in range(angles)]
    blade_names = ['blade_{}'.format(x) for x in range(blades)]
    axes = ['' for x in range(angles)]

    heli_dict = {'title': 'helicopter', 'colormap': 'jet', 'axes': axes, 'animated': True, 'frame_length': 40}

    groups = dict()
    for t in range(angles):
        for b in range(blades):
            pos = (t+blade_offsets[b]) % angles
            data = base.copy()
            data[pos] = blade_length
            if fat:
                data[(pos+1) % angles] = blade_length
            content = {'name':blade_names[b],
                       'data':data,
                       'frame':t}
            g_name = 'group_{}_{}'.format(b,t)
            groups[g_name] = content
    heli_dict['groups'] = groups
    return heli_dict

# h_dict = write_heli_data(20,4)
# file = 'helicopter_3.json'
#
# save_json(h_dict, file)

def write_cm_fail(angles, blade_length=8, fat=True):
    base = [1 for x in range(angles)]
    axes = ['' for x in range(angles)]
    color_dict = {'title': 'colormap example', 'colormap': 'Accent', 'axes': axes}

    groups = dict()
    for t in range(angles):
        data = base.copy()
        data[t] = blade_length
        if fat:
            data[(t+1) % angles] = blade_length
        content = {'data': data,}
        g_name = 'color_{}'.format(t)
        groups[g_name] = content
    color_dict['groups'] = groups
    return color_dict

c_dict_1 = write_cm_fail(9)
c_dict_2 = write_cm_fail(8)
file_1 = 'failed_cm.json'
file_2 = 'succeed_cm.json'

save_json(c_dict_1, file_1)
save_json(c_dict_2, file_2)