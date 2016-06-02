from obspy.core.trace import BaseTrace, Stats
from matplotlib import mlab
from numpy import fft
import numpy as np
import matplotlib.pyplot as plt
from scipy import fftpack
from obspy.core.trace import Trace

class TimeSeriesFrequencyDomainTrace(BaseTrace):

    def ifft(self):
        from obspy.core.trace import TimeSeriesTrace
        t_tr = TimeSeriesTrace()
        t_tr.data = fft.irfft(self.data)
        t_tr.stats = Stats()
        #remaining stats information
        t_tr.stats.network = self.stats.network
        t_tr.stats.station = self.stats.station
        t_tr.stats.location = self.stats.location
        t_tr.stats.starttime = self.stats.starttime

        t_tr.stats.calib = self.stats.calib
        t_tr.stats.back_azimuth = self.stats.back_azimuth
        t_tr.stats.inclination = self.stats.inclination

        #modifiable stats information
        #t_tr.stats.endtime = self.stats.endtime
        t_tr.stats.sampling_rate = self.stats.sampling_rate
        t_tr.stats.npts = self.stats.npts

        return t_tr

    def plot(self):
        N = self.stats.npts
        T = self.stats.delta
        #x = np.linspace(0.0, N*T, N)
        yf = self.data
        xf = np.linspace(0.0, 1.0/(2.0*T), N/2)
        fig, ax = plt.subplots()
        ax.plot(xf, 2.0/N * np.abs(yf[:N/2]))
        plt.xlabel('Freq (Hz)')
        plt.ylabel('|Y(freq)|')
        plt.show()

    def differentiation(self, order_of_differention = 1):
        self.data = fftpack.diff(self.data, order = order_of_differention)
        return self

    def integration(self, order_of_integration=1):
        order_of_integration = (-1)*order_of_integration
        self.data = fftpack.diff(self.data, order = order_of_integration)
        return self

    @property
    def phase(self):
        return np.angle(self.data)

    @property
    def amplitude(self):
        return np.absolute(self.data)
    
    def cross_correlation(self, tr2):

        if self.stats.starttime != tr2.stats.starttime:
            msg = "Traces do not have the same starttime"
            raise Exception(msg)
       
        elif "FALSE" == np.array_equal(self.frequencies(), tr2.frequencies()):
            msg = "Traces do not have the same frequencies"
            raise Exception(msg)

        else: 
            data1 = self.data
            data2 = tr2.data 
            data2_conj = np.conj(data2)
            data_multiplied = np.multiply(data1, data2_conj)
            corr = fftpack.ifft(data_multiplied)
       
            plt.plot(corr)        
            plt.xlabel('offset between two waves')
            plt.ylabel('correlation')
            plt.show()

            return (corr)        

    def frequencies(self):
        n = self.data.size
        timestep = self.stats.delta
        freq = fft.rfftfreq(n, d=timestep)       
        return freq

    def cross_spectrum(self, tr2):
        data1 = self.data
        data2 = tr2.data
        data2_conj = np.conj(data2)
        cross_spectrum = data2_conj*data1
        return (cross_spectrum)

    def coherence(self, tr2):
        data1 = self.data
        data2 = tr2.data
        data2_conj = np.conj(data2)
        cross_spectrum = data2_conj*data1
        coherence = (cross_spectrum)**2/(np.abs(data1)*np.abs(data2))
        return (coherence)

class FrequencyDomainTrace(TimeSeriesFrequencyDomainTrace):

    def ifft(self):
        from obspy.core.trace import Trace    
        tr = Trace()
        tr.data = fft.irfft(self.data)

        tr.stats = Stats()
        #remaining stats information
        tr.stats.network = self.stats.network
        tr.stats.station = self.stats.station
        tr.stats.location = self.stats.location
        tr.stats.starttime = self.stats.starttime

        tr.stats.calib = self.stats.calib
        tr.stats.back_azimuth = self.stats.back_azimuth
        tr.stats.inclination = self.stats.inclination

        #modifiable stats information
        #tr.stats.endtime = self.stats.endtime
        tr.stats.sampling_rate = self.stats.sampling_rate
        tr.stats.npts = self.stats.npts

        return tr


    def plot_psd_trace(self, plot_type='default', nperseg=4096, noverlap=None,
                       detrend=mlab.detrend_linear, window=mlab.window_hanning,
                       convert_to_periods=False, convert_to_db=False, logx=False,
                       plot_noise_models=False, ax=None, show_plot=True,
                       amplitude_label_units=None, calc_only=False):
    
        """
    
        Plot the power spectral density estimated using Welch's method.
        Welch's method works by averaging modified periodograms calculated from
        overlapping data segments (see also [McNamara2004]_). When used without
        windowing and with zero overlap, this is identical to Bartlett's method.
        Setting plot_type to 'ppsd' sets up the plot very similar to the plot
        generated by obspy.signal.spectral_estimation.PPSD. Note that in this mode
        there the visible area contains data if the waveform data was converted to
        ground acceleration.
    
        :type plot_type: String
        :param plot_type: XXX move to special method?
        :type nperseg: int
        :param nperseg: Number of data points to use for FFT. Care must be taken
                to choose a number suitable for FFT. See e.g.
                :func:`~obspy.signal.util.prevpow2`.
        :type noverlap: int
        :param noverlap: The number of overlapping points. If `None`, defaults to
                50% of nperseg.
        XXX Document other options (if they stay).
        """
    
        if plot_type == 'ppsd':
    
            # This is the same as in obspy.signal.spectral_estimation.PPSD.
            # Initiially split the trace into 13 segments, overlapping by 75%
            segment_length = self.stats.npts / 4.0
        
        
            # Reduce segment length to next lower power of 2 (potentially
            # increasing number of segments up to a maximum of 27)

            nperseg = prevpow2(segment_length)
            noverlap = int(0.75 * nperseg)
            # Since plot_type is merely a shortcut, force appropriate options,
            # ignoring manually set values
            detrend = mlab.detrend_linear
            window = fft_taper
            convert_to_periods = True
            convert_to_db = True
            logx = True
            plot_noise_models = True
    
        if noverlap is None:
            # Default to 50% as appropriate for window_hanning
            noverlap = int(0.5 * nperseg)
    
        # Perform the spectral estimation
        Pxx, f = mlab.psd(
            self.data,
            NFFT=nperseg,
            Fs=self.stats.sampling_rate,
            detrend=detrend,
            window=window,
            noverlap=noverlap
        )
    
        # Remove first term (zero frequency)
        Pxx = Pxx[1:]
        f = f[1:]
    
        if calc_only:
            return Pxx, f
    
        if convert_to_periods:
            # Go from frequency to period
            f = 1. / f
    
        if convert_to_db:
            # Replace zero values for safe logarithm (as in PPSD)
            dtiny = np.finfo(0.0).tiny
            idx = Pxx < dtiny
            Pxx[idx] = dtiny
            # Go to db
            Pxx = np.log10(Pxx)
            Pxx *= 10
    
        if ax is None:
            _fig, ax = plt.subplots(nrows=1)
        ax.plot(f, Pxx)
    
        if plot_noise_models:
            # Taken from PPSD.plot()
            model_periods, high_noise = obspy.signal.spectral_estimation.get_NHNM()
            ax.plot(model_periods, high_noise, '0.4', linewidth=2)
            model_periods, low_noise = obspy.signal.spectral_estimation.get_NLNM()
            ax.plot(model_periods, low_noise, '0.4', linewidth=2)
    
        if plot_type == 'ppsd':
            # Set the same limits as in PPSD with 1h segments
            ax.set_xlim(0.01, 179)
            ax.set_ylim(-200, -50)
            # Warn if there is nothing to display (likely data wasn't acceleration)
            if not np.any((Pxx > -200) & (Pxx < -50)):
                msg = 'No data to display (PSD data is between %.01f and ' + \
                      '%.01f dB). Maybe instrument response was not removed ' + \
                      'or data is not ground acceleration?'
                warnings.warn(msg % (Pxx.min(), Pxx.max()))
        else:
            # Scale to maximum of central 90% (so that scaling won't be dominated
            # by border effects)
            cut = int(0.05 * len(Pxx))
            y_max = np.max(Pxx[cut:-cut])
            # Add some padding at the top
            y_max *= 1.05
            ax.set_ylim(0, y_max)
    
        if logx:
            ax.semilogx()
    
        # Set plot labels
        if convert_to_periods:
            ax.set_xlabel('Period [s]')
        else:
            ax.set_xlabel('Frequency [Hz]')
        if convert_to_db:
            ax.set_ylabel('Amplitude [dB]')
        else:
            label = 'Amplitude'
            if amplitude_label_units:
                label += ' [' + amplitude_label_units + ']'
            ax.set_ylabel(label)
        ax.xaxis.set_major_formatter(FormatStrFormatter("%.2f"))
        title = "%s   PSD Estimation"
        ax.set_title(title % self.id)
    
        if show_plot:
            plt.show()

