import numpy as np
from   scipy.stats import norm
import matplotlib.pyplot as plt

fontSize = 12     # font size
dpi      = 150    # printing resolution

def plotXY(x, y, z, name):
    nSamples = np.shape(x)[0]
    rangeplot = range(0, nSamples)

    fig, [ax1, ax2, ax3] = plt.subplots(nrows=3, ncols=1, sharex=True)
    ax1.plot(rangeplot, x[rangeplot], lw=1, alpha=0.9, color='r', label=r'Advance $a$')
    ax2.plot(rangeplot, y[rangeplot], lw=1, alpha=0.9, color='b', label=r'Cumulated waiting time')
    ax3.plot(rangeplot, z[rangeplot], lw=1, alpha=0.9, color='g', label=r'Total packets lost')
    ax1.set_ylabel(r'Advance',      fontsize=fontSize)
    ax2.set_ylabel(r'Waiting Time',      fontsize=fontSize)
    ax3.set_ylabel(r'Packets Lost', fontsize=fontSize)
    ax3.set_xlabel(r'Packets', fontsize=fontSize)
    ax1.legend()
    ax2.legend()
    ax3.legend()
    ax3.set_xlim(left=0, right=nSamples)
    plt.savefig('figures/' + name +'.png', bbox_inches='tight', dpi=dpi)
    plt.close()

def plotXYTime(t, x, y, z, name, f='png'):
    nSamples = np.shape(x)[0]
    rangeplot = range(0, nSamples)

    fig, [ax1, ax2, ax3] = plt.subplots(nrows=3, ncols=1, sharex=True)
    ax1.plot(t[rangeplot], x[rangeplot], lw=1, alpha=0.9, color='r', label=r'Advance $a$')
    ax2.plot(t[rangeplot], y[rangeplot], lw=1, alpha=0.9, color='b', label=r'Cumulated waiting time')
    ax3.plot(t[rangeplot], z[rangeplot], lw=1, alpha=0.9, color='g', label=r'Total packets lost')
    ax1.set_ylabel(r'Advance',      fontsize=fontSize)
    ax2.set_ylabel(r'Waiting Time',      fontsize=fontSize)
    ax3.set_ylabel(r'Packets Lost', fontsize=fontSize)
    ax3.set_xlabel(r'Time', fontsize=fontSize)
    ax1.legend()
    ax2.legend()
    ax3.legend()
    ax3.set_xlim(left=0, right=t[nSamples-1])
    plt.savefig('figures/' + name +'.'+f, format=f)
    plt.show()


def plotTime(x,y,name):
    nSamples = np.shape(x)[0]
    rangeplot = range(0, nSamples)

    fig, ax1 = plt.subplots()
    ax1.plot(x[rangeplot], y[rangeplot], lw=1, alpha=0.9, color='r', label=r'Advance $a$')
    #ax2.plot(x[rangeplot], y[rangeplot], lw=1, alpha=0.9, color='b', label=r'Cumulated waiting time')
    ax1.set_ylabel(r'Advance',      fontsize=fontSize)
    #ax2.set_ylabel(r'Waiting Time',      fontsize=fontSize)
    ax1.set_xlabel(r'Time', fontsize=fontSize)
    ax1.legend()
    #ax2.legend()
    ax1.set_xlim(left=0, right=x[nSamples-1])
    plt.savefig('figures/' + name +'.png', bbox_inches='tight', dpi=dpi)
    plt.close()