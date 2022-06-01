from box import Box

parameters1 = Box(
    {
        "ip": {
            "attribute1": {
                "default": 64,
                "elements": [32, 64, 128, 256, 512],
                "excluded": [64, 128],
            },
            "attribute2": {"default": 127, "range": [0, 255], "excluded": [35, 36, 37]},
            "attribute3": {"default": 1.4, "range": [0, 2, 0.2]},
            "attribute4": {"default": 18, "range": [10, 20], "randomize": False},
            "attribute5": {"range": [20, 30], "replace": False},
        }
    },
    box_dots=True,
)

parameters2 = Box(default_box=True, box_intact_types=[list, tuple])
parameters2.ip.attribute1.default = 64
parameters2.ip.attribute1.elements = [32, 64, 128, 256, 512]
parameters2.ip.attribute1.excluded = [64, 128]
parameters2.ip.attribute2.default = 127
parameters2.ip.attribute2.range = [0, 255]
parameters2.ip.attribute2.excluded = [35, 36, 37]
parameters2.ip.attribute3.default = 1.4
parameters2.ip.attribute3.range = [0, 2, 0.2]
parameters2.ip.attribute4.default = 18
parameters2.ip.attribute4.range = [10, 20]
parameters2.ip.attribute4.randomize = False
parameters2.ip.attribute5.range = [20, 30]
parameters2.ip.attribute5.replace = False

del Box
