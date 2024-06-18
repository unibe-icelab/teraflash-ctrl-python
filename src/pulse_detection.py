import numpy as np
from scipy.signal import hilbert
from typing import Optional


def detect_pulse(time: np.array, signal: np.array) -> Optional[int]:
    # Compute the analytic signal using Hilbert transform
    analytic_signal = hilbert(signal)
    envelope = np.abs(analytic_signal)

    # Detect the main pulse in the envelope
    max_index = np.argmax(envelope)
    main_pulse_time = time[max_index]

    # Define a threshold to find the start and end of the pulse
    threshold = envelope[max_index] * 0.5
    pulse_indices = np.where(envelope > threshold)[0]
    _pulse_start_time = time[pulse_indices[0]]
    _pulse_end_time = time[pulse_indices[-1]]

    # always start 15 ps before pulse begins
    main_pulse_time -= 15.0

    # only return the pulse if it is above the noise level
    if envelope[max_index] > 7.0:
        return int(main_pulse_time)
    else:
        return None
