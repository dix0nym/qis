from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
import numpy as np

from .dbhelper import DBhelper
from .util import get_filename


class Plotter:
    def __init__(self, db, records):
        # data = {modul, count, participants, average}
        self.db = db
        self.groups = ["1 - 1,3", "1,7 - 2,3",
                       "2,7 - 3,3", "3,7 - 4", "4,7 - 5"]
        self.data = self.build_plot_data(records)

    def build_plot_data(self, records):
        data = []
        for record in records:
            # get infos from table data
            exam_details = self.db.get_exam_details(record['nr'])
            if not exam_details:
                continue
            entry = {'nr': record['nr'], 'modul': record['module'], 'count': exam_details['count'],
                     'participants': exam_details['participants'], 'average': exam_details['average']}
            data.append(entry)
        return data

    def create(self):
        names = []
        for modul_data in self.data:
            modul = modul_data['modul']
            nr = modul_data['nr']
            fig = self.create_plot(modul, modul_data['count'],
                                   modul_data['participants'], modul_data['average'])
            name = self.save_plot(nr, modul, fig)
            plt.close(fig)
            names.append(name)
        return names

    def create_plot(self, modul, count, participants, average):
        fig, ax = plt.subplots()
        y_pos = np.arange(len(self.groups))
        values = [v/participants * 100 for v in count]
        rects = ax.bar(y_pos, values, align='center', alpha=0.5)
        # set axis titles
        ax.set_ylabel('Prozent')
        ax.set_xlabel('Noten')
        ax.set_title(f"Notenspiegel {modul}")
        ax.yaxis.set_major_formatter(mtick.PercentFormatter())
        plt.xticks(y_pos, self.groups)
        # add numbers to every bar
        for i, rect in enumerate(rects):
            base_y = rect.get_height()
            label_pos_y = base_y - 3 if base_y else 2
            label_pos_x = rect.get_x() + rect.get_width()/2
            label = f"{int(base_y)}% ({count[i]})"
            ax.text(label_pos_x, label_pos_y, label,
                    ha='center', va='bottom', clip_on=True)
        # calculate best spot for text box
        min_idx = values.index(min(values))
        max_heigth = max([r.get_height() for r in rects])
        lb_box_min_pos_x = rects[min_idx].get_x() + \
            rects[min_idx].get_width()/2
        lb_box_max_pos_y = max_heigth - 5
        # add text box with average/participants
        lb_box_text = f"Ø {average}\n# {participants}"
        ax.text(lb_box_min_pos_x, lb_box_max_pos_y, lb_box_text,
                ha='center', va='bottom', bbox=dict(facecolor='red', alpha=0.5))
        return fig

    def save_plot(self, nr, title, fig):
        name = get_filename(f"{nr}-{title}")
        path = Path("plots/", f"{name}.png")
        if not path.parent.exists():
            path.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(path, format="png", bbox_inches="tight",
                    bbox_extra_artists=[])
        return path
