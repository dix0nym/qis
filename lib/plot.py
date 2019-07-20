import os

import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
import numpy as np


def create_plot(modul, names, anzahl, participants, average):
    fig, ax = plt.subplots()
    y_pos = np.arange(len(names))
    values = [v/participants * 100 for v in anzahl]
    rects = ax.bar(y_pos, values, align='center', alpha=0.5)
    ax.set_ylabel('Prozent')
    ax.set_xlabel('Noten')
    ax.set_title('Notenspiegel {}'.format(modul))
    ax.yaxis.set_major_formatter(mtick.PercentFormatter())
    plt.xticks(y_pos, names)
    min_idx = values.index(min(values))
    max_heigth = max([r.get_height() for r in rects]) 
    for i, rect in enumerate(rects):
        height = rect.get_height()
        h = height - 3 if height else 2
        ax.text(rect.get_x() + rect.get_width()/2, h, '%d%% (%d)' % (int(height), anzahl[i]), ha='center', va='bottom', clip_on=True)
    ax.text(rects[min_idx].get_x() + rects[min_idx].get_width()/2, max_heigth - 5,"Ø {}\n# {}".format(average, participants), ha='center', va='bottom', bbox=dict(facecolor='red', alpha=0.5))
    if not os.path.isdir("plots"):
        os.makedirs("plots")
    fname = "plots/{}.png".format(modul)
    fig.savefig(fname, format="png",bbox_inches="tight", bbox_extra_artists=[])
    return fname
