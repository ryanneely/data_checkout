##filtering.py
##various filter functions

##by Ryan Neely
##8_17_18

import numpy as np
from scipy.signal import butter, lfilter
from scipy import signal
from scipy.ndimage.filters import gaussian_filter

def bandpass_filter(data,lowcut=300,highcut=5000,fs=24414.0625,order=5):
	"""
	this function uses a Butterworth bandpass filter to extract 
	the spikeband data, or data filtered between two set frequency values.

	Args:

		-data: 1-D numpy array of raw ehphys data
		-lowcut: the low frequency corner (Hz)
		-highcut: the high freq corner
		-fs: the sample rate of the data
		-order: the order of the butterworth filter to uses
		-plot: if True, make a plot

	returns: 
		-a 1-D numpy array of filtered data
	"""
	##check the data dimensions
	data = np.squeeze(data)
	if len(data.shape) > 1:
		raise ValueError("Needs 1-D array!")
	##define filter functions
	def butter_bandpass(lowcut, highcut, fs, order=5):
		nyq = 0.5 * fs
		low = lowcut / nyq
		high = highcut / nyq
		b, a = butter(order, [low, high], btype='band')
		return b, a

	def butter_bandpass_filter(data, lowcut, highcut, fs, order=5):
		b, a = butter_bandpass(lowcut, highcut, fs, order=order)
		y = lfilter(b, a, data)
		return y

	filtered = butter_bandpass_filter(data, lowcut, highcut, fs, order)

	return filtered

def gauss_convolve(array, sigma, fs):
	"""
	takes in an array with dimenstions samples x trials.
	Returns an array of the same size where each trial is convolved with
	a gaussian kernel with sigma = sigma.

	Args:
		-array: data array to smooth
		-sigma: width of the gaussian kernel in MS!!
	"""
	##remove singleton dimesions and make sure values are floats
	array = array.squeeze().astype(float)
	##allocate memory for result
	result = np.zeros(array.shape)
	##determine the width of the kernel in samples
	sigma = sigma*(fs/1000.0)
	##if the array is 2-D, handle each trial separately
	try:
		for trial in range(array.shape[1]):
			result[:,trial] = gaussian_filter(array[:, trial], sigma = sigma, order = 0, mode = "reflect")
	##if it's 1-D:
	except IndexError:
		if array.shape[0] == array.size:
			result = gaussian_filter(array, sigma = sigma, order = 0, mode = "reflect")
		else:
			print("Check your array dimenszions!")

	return result

def bin_data(timestamps,data,bin_size,Fs):
	"""
	a function that bins data.

	Args:
		- timestamps: the timestamps array
		-data: the data to bin
		-bin_size = the bin size, in ms
		-Fs: the sampling frequency (Hz)

	Returns:
		-timestamps: the scaled timestamps array
		-result: binned data
	"""
	##first start by getting some info about the data
	N_ms = (data.shape[0]/Fs)*1000
	##convert the bin size to samples
	bin_size = int((bin_size/1000)*Fs)
	##determine the number of bins that will fit in the data
	numBins = int((data.size)/bin_size)
	##now convert the timestamps array
	timestamps2 = np.linspace(timestamps[0],timestamps[-1],numBins)
	##allocate memory
	result = np.zeros(numBins)
	##bin the data!
	for i in range(numBins):
		result[i] = np.trapz(data[i*bin_size:(i+1)*bin_size])/bin_size
	return timestamps2,result
