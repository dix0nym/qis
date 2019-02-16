import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
import numpy as np


def create_plot(modul, names, anzahl, count):
    fig, ax = plt.subplots()
    y_pos = np.arange(len(names))
    values = [v/count * 100 for v in anzahl]
    rects = ax.bar(y_pos, values, align='center', alpha=0.5)
    ax.set_ylabel('Prozent')
    ax.set_xlabel('Noten')
    ax.set_title('Notenspiegel {}'.format(modul))
    ax.yaxis.set_major_formatter(mtick.PercentFormatter())
    plt.xticks(y_pos, names)
    for i, rect in enumerate(rects):
        height = rect.get_height()
        h = height - 2 if height else 2
        ax.text(rect.get_x() + rect.get_width()/2, h, '%d%% (%d)' % (int(height), anzahl[i]), ha='center', va='bottom', clip_on=True)
    fname = "temp_{}.png".format(modul)
    fig.savefig(fname, format="png", bbox_inches="tight", bbox_extra_artists=[])
    return fname