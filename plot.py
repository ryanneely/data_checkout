##plot.py

##functions to plot processed data

##by Ryan Neely 1/3/19

import numpy as np
import matplotlib.pyplot as plt
import filtering as filt
from itertools import cycle

def plot_stim_window(data,norm=False,smooth=False):
    """
    Makes some quick plots of stim-locked variables from a single
    dataset.
    Args:
        -data: data dictionary of the kind returned by get_stim_window
            containing the data to plot
        -norm: if True, normalizes the values to the mean of the pre-stim window
    """
    pad = data['pad']/1000.0/60.0 ##let's plot things in mins for ease of viewing
    start = data['start']/1000.0/60.0
    stop = data['stop']/1000.0/60.0
    exclude = ['time','start','stop','pad'] ##varibles present in the dictionary that we don't want to plot
    var = [x for x in list(data) if not x in exclude] ##all the rest of the variables to plot
    for v in var:
        y = data[v]
        tbase = np.linspace(-pad,stop+pad,y.size)
        if smooth:
            fs = y.size/(60*(2*pad+stop)) ##derive the sample rate 
            y = filt.gauss_convolve(y,5000,fs)
        if norm:
            ##find out the index of the start time
            idx = np.where(tbase>0)[0][0]
            baseline = y[0:idx]
            y = y/np.mean(baseline)
        fig,ax = plt.subplots(1)
        ax.plot(tbase,y,linewidth=2)
        stim_bar = np.ones(10)*(np.min(y)-np.std(y))
        stim_x = np.linspace(0,stop,10)
        ax.plot(stim_x,stim_bar,linewidth=5,color='r',label='stim on')
        ax.set_xlabel('Time from stim onset, mins',fontsize=14)
        if norm:
            ax.set_ylabel("Value, normalized to pre-stim baseline",fontsize=14)
        else:
            ax.set_ylabel('Value',fontsize=14)
        ax.set_title(v,fontsize=14)
        for tick in ax.yaxis.get_major_ticks():
            tick.label.set_fontsize(14)
        for tick in ax.xaxis.get_major_ticks():
            tick.label.set_fontsize(14)
        ax.legend()
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)

def plot_stim_window2(data,smooth=False):
    """
    Makes a single plot of stim-locked variables from a single
    dataset, normalizing values to baseline so they can be plotted together.
    Args:
        -data: data dictionary of the kind returned by get_stim_window
            containing the data to plot
        -smooth: if True, gaussian convolves the data to smooth it out. 
    """
    pad = data['pad']/1000.0/60.0 ##let's plot things in mins for ease of viewing
    start = data['start']/1000.0/60.0
    stop = data['stop']/1000.0/60.0
    exclude = ['time','start','stop','pad'] ##varibles present in the dictionary that we don't want to plot
    var = [x for x in list(data) if not x in exclude] ##all the rest of the variables to plot
    fig,axes = plt.subplots(nrows=len(var),ncols=1,sharex=True)
    ##cycle plot colors
    prop_cycle = plt.rcParams['axes.prop_cycle']
    colors = cycle(prop_cycle.by_key()['color'])
    for i,v in enumerate(var):
        y = data[v]
        tbase = np.linspace(-pad,stop+pad,y.size)
        if smooth:
            fs = y.size/(60*(2*pad+stop)) ##derive the sample rate 
            y = filt.gauss_convolve(y,5000,fs)
        axes[i].plot(tbase,y,linewidth=2,label=v,color=next(colors))
        ##some values for the onset/offset ticks
        start_idx = np.where(tbase>0)[0][0]
        stop_idx = np.where(tbase>stop)[0][0]
        ymin = (y[start_idx]-y.std(),y[stop_idx]-y.std())
        ymax = (y[start_idx]+y.std(),y[stop_idx]+y.std())
        axes[i].vlines([start,stop],ymin,ymax)
        axes[i].set_ylabel("Value",fontsize=14)
        axes[i].spines["top"].set_visible(False)
        axes[i].spines["right"].set_visible(False)
        for tick in axes[i].yaxis.get_major_ticks():
            tick.label.set_fontsize(14)
        if i<len(var)-1:
            axes[i].legend()
            # axes[i].set_xticks([])
    stim_bar = np.ones(10)*(y.min()-y.std())
    stim_x = np.linspace(0,stop,10)
    axes[i].plot(stim_x,stim_bar,linewidth=5,color='r',label='stim on')    
    axes[i].set_xlabel('Time from stim onset, mins',fontsize=14)
    fig.suptitle("Physiological changes with stimulation",fontsize=14)
    for tick in axes[i].xaxis.get_major_ticks():
        tick.label.set_fontsize(14)
    axes[i].legend()


