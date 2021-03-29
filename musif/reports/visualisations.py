########################################################################
# VISUALISATIONS SCRIPT
########################################################################
# This script is composed of several functions called from the write
# module. Each function generates a different visualisation
########################################################################

import matplotlib.pyplot as plt
import warnings
import numpy as np
from music21 import pitch, interval
import matplotlib
matplotlib.use('Agg')
warnings.filterwarnings("ignore")


def box_plot(name, data, second_title=None):
    try:
        columns_box = [['LowestIndex', 'HighestIndex'],
                       ['AmbitusLargestSemitones']]
        columns_names = [['Lowest Notes', 'Highest Notes'], ['Ambitus']]
        subplot_titles = ['Notes', 'Ambitus']
        fig, ax = plt.subplots(ncols=2)
        if second_title is not None:
            plt.suptitle('Ambitus')
            plt.title(second_title)
        else:
            plt.title('Ambitus')
        i = 0
        try:
            for j, info in enumerate(columns_box):
                info_data = [data[x].tolist() for x in info]
                ax[i].boxplot(info_data, labels=info)
                ax[i].set_xticklabels(columns_names[i])
                # change the axis from midi index to note name
                plt.draw()
                labels = [x.get_text() for x in ax[i].get_yticklabels()]
                if i == 0:
                    labels_names = [pitch.Pitch(
                        int(x)).unicodeNameWithOctave for x in labels]
                    ax[i].set_ylabel('Note')
                else:
                    labels_names = [interval.Interval(
                        float(x)).directedName for x in labels]
                    ax[i].set_ylabel('Interval')
                ax[i].set_yticklabels(labels_names)

                i += 1
        except Exception as e:
            print(e)

        fig.tight_layout()
        fig.subplots_adjust(top=0.88)
        plt.savefig(name)
        plt.close(fig)
    except:
        pass


def ivalues_bar_plot(name, data, column_names, second_title=None):
    size = len(column_names)
    list_sum = data[column_names].sum(axis=0, skipna=True)
    fig = plt.figure(figsize=(size if len(column_names) >
                              6 else 10, size if len(column_names) > 6 else 10))
    plt.bar(x=range(0, size, 1), height=list(
        list_sum / len(data[column_names])), color='w', edgecolor='k')
    plt.xticks(ticks=range(0, size, 1), labels=column_names)
    plt.tick_params(labelsize='large')
    if second_title is not None:
        plt.suptitle('Intervallic variation measurements')
        plt.title(second_title)
    else:
        plt.title('Intervallic variation measurements')
    plt.ylabel('Number of Semitones')
    plt.tight_layout()
    plt.savefig(name)
    plt.close(fig)


def bar_plot(name, data, column_names, x_label, title, second_title=None):
    size = len(column_names)

    list_sum = data[column_names].sum(axis=0, skipna=True)
    results = list((list_sum / sum(list_sum)) * 100)
    valid_results = []
    more_than_2 = []
    for j, i in enumerate(results):
        if i > 2:
            more_than_2.append(column_names[j])
            valid_results.append(i)
    size = len(more_than_2)
    fig, ax = plt.subplots(
        figsize=(size if size > 6 else 6, size if size > 6 else 6))
    plt.bar(x=range(0, size, 1), height=valid_results, color='w', edgecolor='k')
    plt.draw()
    labels = [x.get_text() for x in ax.get_yticklabels()]
    ax.set_yticklabels([l + '%' for l in labels])
    plt.xticks(ticks=range(0, size, 1), labels=more_than_2)
    plt.xlabel(x_label)
    plt.ylabel('Percentage')
    plt.suptitle(
        title + ('\n' + second_title if second_title is not None else ''))
    plt.savefig(name)
    plt.close(fig)


def double_bar_plot(name, data, second_title=None):
    plots = [['LeapsAll', 'StepwiseMotionAll'], ['PerfectAll',
                                                 'MajorAll', 'MinorAll', 'AugmentedAll', 'DiminishedAll']]
    fig, ax = plt.subplots(nrows=1, ncols=2)
    for i, plot in enumerate(plots):
        list_sum = data[plot].sum(axis=0, skipna=True)
        results = list((list_sum / sum(list_sum)) * 100)
        ax[i].bar(x=range(len(plot)), height=results, color='w', edgecolor='k')
        ax[i].set_xticks(range(len(plot)))
        plt.draw()
        labels = [x.get_text() for x in ax[i].get_yticklabels()]
        ax[i].set_yticklabels([l + '%' for l in labels])
        ax[i].set_ylabel('Percentage')
        ax[i].set_xticklabels([p.replace('All', '')
                               for p in plot], rotation=45, ha='right')

    plt.suptitle('Presence of Interval Types' +
                 ('\n' + second_title if second_title is not None else ''))
    plt.tight_layout()
    plt.subplots_adjust(top=0.9)
    plt.savefig(name)
    plt.close(fig)


def pie_plot(name, data, second_title=None):
    main_division = ['Ascending', 'Descending']
    plots = ['StepwiseMotion', 'Leaps', 'Perfect',
             'Major', 'Minor', 'Augmented', 'Diminished']
    fig, ax = plt.subplots(nrows=3, ncols=3)
    i = 0
    resta = 0
    for j, info in enumerate(plots):
        if j in [2, 5]:
            i += 1
            resta = j
        ax[i][j - resta].set_title(info)
        sum_augmented = np.nansum(data[info + main_division[0]])
        sum_descending = np.nansum(data[info + main_division[1]])
        ax[i][j - resta].pie([sum_augmented, sum_descending],
                             autopct='%1.0f%%')
        ax[i][j - resta].axis('equal')

    fig.delaxes(ax[0, 2])
    fig.delaxes(ax[2, 2])
    fig.legend(main_division, loc='lower right')
    plt.suptitle('Presence of ascending and descending intervals within each type\n' +
                 ('\n'+second_title if second_title is not None else ''))
    plt.tight_layout()
    plt.subplots_adjust(top=0.85)
    plt.savefig(name)
    plt.close(fig)


def customized_plot(name, data, column_names, subtitile, second_title=None):
    size = len(column_names)
    list_sum = data[column_names].sum(axis=0, skipna=True)
    sum_all = sum(list_sum)
    possitions = {'bb1': (4.5, 2), 'b1': (4.9, 5), '1': (6.6, 5), '#1': (1.3, 0.85),
                  'bb2': (8.1, 5.5), 'b2': (8.2, 5.2), '2': (2.5, 1.5), '#2': (7.5, 2.8),
                  'bb3': (3.6, 2.3), 'b3': (6.7, 3.25), '3': (8.6, 3.4), '#3': (0.3, 2.5),
                  'bb4': (7.7, 3.3), 'b4': (-0.2, 2.7), '4': (1.2, 3.4), '#4': (5.2, 0.7),
                  'bb5': (1.4, 3.7), 'b5': (2, 4), '5': (6.8, 1.5), '#5': (1.85, 4.5),
                  'bb6': (2.5, 3.7), 'b6': (2.7, 3.25), '6': (2.8, 4.95), '#6': (4, 3),
                  'bb7': (3.8, 5.2), 'b7': (4.5, 1.8), '7': (4.8, 3.55), '#7': (5.85, 3.7)}

    colors = {'bb1':  'powderblue', 'b1':  'paleturquoise', '1': 'skyblue', '#1':  'darkgoldenrod',
              'bb2': 'lightblue', 'b2':  'lightskyblue', '2': 'darkkhaki', '#2': 'darkorchid',
              'bb3': 'goldenrod', 'b3': 'palevioletred', '3': 'plum', '#3': 'green',
              'bb4': 'thistle', 'b4': 'yellowgreen', '4': 'lightgreen', '#4': 'darkred',
              'bb5': 'lightseagreen', 'b5': 'mediumseagreen', '5': 'firebrick', '#5': 'forestgreen',
              'bb6': 'lightgreen', 'b6': 'olivedrab', '6': 'seagreen', '#6': 'rebeccapurple',
              'bb7': 'mediumseagreen', 'b7': 'mediumvioletred', '7': 'slateblue', '#7': 'purple'}

    fig, ax = plt.subplots(figsize=(8.5, 6))
    ax.set(xlim=(0, 10), ylim=(0, 6.5))
    ax.set_axis_off()
    for i, cname in enumerate(column_names):
        if cname in possitions:
            loc = possitions[cname]
            size = ((list_sum[i] / sum_all) * 100)
            size_bigger = size * 7
            ax.plot(loc[0], loc[1], marker='o',
                    markersize=size_bigger, color=colors[cname])
            #ax.annotate(cname, loc, ha="center", va ='center')
            ax.text(loc[0], loc[1], cname, fontsize=20,
                    verticalalignment='center', horizontalalignment='center')
    plt.suptitle('Scale degrees in part ' + subtitile +
                 ('\n'+second_title if second_title is not None else ''))
    fig.tight_layout()
    fig.savefig(name)
    plt.close(fig)


def bar_plot_extended(name, data, column_names, x_label, y_label, title, second_title=None):
    size = len(column_names)
    fig = plt.figure(figsize=(size if len(column_names) >
                              6 else 10, size if len(column_names) > 6 else 10))
    if hasattr(data, 'groups'):
        barWidth = 1/(len(data[column_names])*2)
        X = np.arange(size)
        counter = 0
        for i, group in data[column_names]:
            plt.bar(x=X, width=barWidth, height=list(group[column_names].mean(
                axis=0, skipna=True)), color=COLOR[counter], edgecolor='k', label=str(i))
            X = [x + barWidth for x in X]
            counter += 1
        plt.legend(loc="upper right")
        plt.xticks(ticks=[r + len(data[column_names])*barWidth /
                          2-barWidth/2 for r in range(size)], labels=column_names)
        plt.tick_params(labelsize='large')
        if second_title is not None:
            plt.suptitle('.')
        plt.ylabel(y_label)
        plt.suptitle(
            title + ('\n' + second_title if second_title is not None else ''))
    else:
        plt.bar(x=range(0, size, 1), height=list(data[column_names].mean(
            axis=0, skipna=True)), color=COLOR[np.random.randint(len(COLOR))], edgecolor='k')
        plt.xticks(ticks=range(0, size, 1), labels=column_names)
        plt.tick_params(labelsize='large')
        if second_title is not None:
            plt.suptitle('.')
        plt.ylabel(y_label)
        plt.suptitle(
            title + ('\n' + second_title if second_title is not None else ''))
    plt.tight_layout()
    plt.savefig(name)
    plt.close(fig)


def line_plot_extended(name, data, column_names, x_label, y_label, title, second_title=None):
    from matplotlib.lines import Line2D
    size = len(column_names)
    fig = plt.figure(figsize=(size if len(column_names) >
                              6 else 10, size if len(column_names) > 6 else 10))
    if hasattr(data, 'groups'):
        X = np.arange(size)
        counter = 0
        for i, group in data[column_names]:
            results = np.array(group[column_names].mean(
                axis=0, skipna=True)).astype(np.double)
            s1mask = np.isfinite(results)
            plt.plot(np.array(X)[s1mask], results[s1mask], color=COLOR[counter], linestyle=LINESTYLES[np.random.randint(
                len(LINESTYLES))], marker=MARKERS[np.random.randint(len(MARKERS))], label=str(i), markersize=15)
            counter += 1
        plt.legend(loc="upper right")
        plt.xticks(ticks=X, labels=column_names)
        plt.tick_params(labelsize='large')
        if second_title is not None:
            plt.suptitle('.')
        plt.ylabel(y_label)
        plt.suptitle(
            title + ('\n' + second_title if second_title is not None else ''))
    else:
        plt.plot(range(0, size, 1), list(data[column_names].mean(axis=0, skipna=True)), color=COLOR[np.random.randint(
            len(COLOR))], linestyle='--', marker='o', markersize=15)
        plt.xticks(ticks=range(0, size, 1), labels=column_names)
        plt.tick_params(labelsize='large')
        if second_title is not None:
            plt.suptitle('.')
        plt.ylabel(y_label)
        plt.suptitle(
            title + ('\n' + second_title if second_title is not None else ''))
    plt.tight_layout()
    plt.savefig(name)
    plt.close(fig)
