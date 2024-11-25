from moku.instruments import LockInAmp

import time              as _time
import numpy             as _n
import matplotlib.pyplot as plt
import spinmob           as _s 
import mcphysics         as _m
import sys

class Moku_Go():
    """
    This object lets you query the Liquid Instruments Moku Go.

    Parameters
    ----------
    IP=[fe80::7269:79ff:feb9:502e]
       IP address. Use Moku GUI to find this (Device Info).

    force_connect=False
        If True, claim ownership even if the device is already owned by another resource.

    default=True
        If True, pre-configure lockin for the Drum setup.

    """

    def __init__(self, IP = '[fe80::7269:79ff:feb9:502e]', force_connect=False, defaults = True):
        
        self.LIA = LockInAmp(IP, force_connect=force_connect)
        
        if(defaults): self.configre_lockin()

    def configre_lockin(self, freq = 320, amp = .100, lowpass_corner = 10, lowpass_slope = 12, gain = 40):
        """
        Configures the Moku Lock-in amplifier for use with the Drum setup.
        Intended configuration is as follows:
        
        IN:
            Channel 1: 
                AC coupled, should be connected to reflective sensor output.
            
            Channel 2:
                Unused.
                
        OUT:
            Channel 1:
                Lock-in output (max 5V).
                
            Channel 2:
                Reference sinewave signal out, should be sent to the amplifier input (phono R/L).
                
         Parameters
         ----------
         freq : float
            Lockin reference/output sinewave frequency. 
        
        amp: float
            Output sinewave amplitude [V]. 
        
        lowpass_corner: uint
            Corner frequency [Hz] for the lowpass filter of the lockin amplifier.
        
        lowpass_slope: uint
            Lowpass filter slope (dB) per octave. Allowed values are 6, 12, 18, and 24.
        
        gain: uint 
            Post lockin detection gain [dB]. 
        
        """

        # Set Channel 1 AC coupled, 1 Mohm impedance, and 400 mVpp range
        self.LIA.set_frontend(1, coupling='AC', impedance='1MOhm',attenuation='0dB')

        # Configure the demodulation signal
        self.LIA.set_demodulation('Internal', frequency= freq, phase = 0)
        
        # Output sinewave amplitude
        self.LIA.set_aux_output(freq, amp)

        # Set low pass filter corner frequency and slope
        if   lowpass_slope == 6 : self.LIA.set_filter(10,slope='Slope6dB')
        elif lowpass_slope == 12: self.LIA.set_filter(10,slope='Slope12dB')
        elif lowpass_slope == 18: self.LIA.set_filter(10,slope='Slope18dB')
        elif lowpass_slope == 24: self.LIA.set_filter(10,slope='Slope24dB')
            
        # Configure gain post Lockin (dB)
        self.LIA.set_gain(main=gain,aux=1)
        
        # Config channel 2 to monitor LIA Main output signal
        self.LIA.set_monitor(2, 'MainOutput')

        # Configure output signals
        self.LIA.set_outputs(main = 'R', aux = "Demod")
        
        # Set polar mode for Lock-In output
        self.LIA.set_polar_mode(range = '7.5mVpp')

    def set_amplitude(self, amplitude):
        """
        Set the output sinewave amplitude.

        Parameters
        ----------
        amplitude : float
            Output sinewave amplitude [V].
            
        """
        self.LIA.set_aux_output(0, amplitude)
        
    
    def set_frequency(self, freq, phase=0): 
        """
        Set the Lockin reference frequency.

        Parameters
        ----------
        freq : float
            Lockin reference/output sinewave frequency.
            
        """
        self.LIA.set_demodulation('Internal',frequency=freq)
        
    def get_output(self):
        """
        
        """
        data = self.LIA.get_data()
        return _n.average(data['ch2'])
        
    def scan(self, freqs, delay = 1, plot=True):
        """
        Measures the amplitude response of the drumhead at each frequency provided,
        at the current location of the sensor.

        Parameters
        ----------
        freqs : list/array
            Set of frequencies to be iterated over.
            
        delay: uint
            Time [s] to wait after frequency changes before making amplitude measurement.
        
        plot: bool
            If True, plot the results when scan is complete.

        Returns
        -------
        numpy.array
            Array of the amplitude response at each of the supplied frequencies.

        """

        
        # Create list to hold the measured amplitudes
        amplitudes = []
        
        # Number of frequencies
        n = len(freqs)
        
        # Iterate over each frequency
        for i,f in enumerate(freqs):
            
            #
            self.set_frequency(f)
            
            # Let the plate/drum settle
            _time.sleep(delay)
            
            # Append Lock-In output value to list
            try: val = self.get_output()
            except: val = 0
            
            if(val != None): amplitudes.append(val)
            else:            amplitudes.append(0)
            
            # Write to console
            sys.stdout.write('\r')
            sys.stdout.write("[%-25s] %d%%   Frequency = %.2f Hz, LIA: %f" % ('='*int(25*i/n), int(100*i/n), f, val))
            sys.stdout.flush()
                 
        # Plot the results    
        if(plot):
            plt.figure()
            plt.plot(freqs,amplitudes)
            plt.show()
          
        return _n.array(amplitudes)


    def spatial_scan(self, r, theta):
        """
        

        Parameters
        ----------
        r : TYPE
            DESCRIPTION.
        theta : TYPE
            DESCRIPTION.

        Returns
        -------
        None.

        """
        data = []
        for i in range(18):
            rad = []
            val = self.get_output()
            rad.append(val)
            
            for j in range(10):
                motor._radial_go(700)
                _time.sleep(3)
                val = self.get_output()
                rad.append(val)
                print("theta: %d, radius: %d, LIA: %f"%(i*10, (j+1)*700,val))
                
            data.append(_n.array(rad))
            motor._radial_go(-7250)
            motor._radial_go(250)
            motor._angular_go(40)
            _time.sleep(2)
            
        plt.figure()
        radius_matrix, theta_matrix = _n.meshgrid(r,theta)
        X = radius_matrix * _n.cos(theta_matrix)
        Y = radius_matrix * _n.sin(theta_matrix)
        Z = data
        
        # Create a contour plot with a diverging colormap
        plt.contourf(X, Y, Z, cmap='RdYlBu_r',levels = [.05*i for i in range(84)])
        plt.colorbar(label='Values')
        plt.scatter(X,Y,Z)
        plt.xlabel('X')
        plt.ylabel('Y')
        plt.show()

    def close(self):
        """
        Relinquish ownership of the Moku. 
        """
        self.LIA.relinquish_ownership()

if __name__ == '__main__':
    self = Moku_Go(force_connect= True)
    
    #motor = m.experiments.drum._unsafe_motors('COM4')
    
    