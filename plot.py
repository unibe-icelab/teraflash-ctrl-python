import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib import style
import numpy as np
import random
import serial

# initialize serial port
COM = '/dev/cu.usbmodem3253354F31391'
BAUD = 115200
# Create figure for plotting
fig = plt.figure()
ax = fig.add_subplot(1, 1, 1)
xs = []  # store time here (n)
t1s = []  # store temp here
t2s = []  # store temp here
t3s = []  # store temp here
t4s = []  # store temp here
t5s = []  # store temp here

ser = serial.Serial(COM, BAUD, timeout=0.1)
print('Waiting for device')
print(ser.name)


# This function is called periodically from FuncAnimation
def animate(i, xs, t1s, t2s, t3s, t4s, t5s):
    # Aquire and parse data from serial port
    val = ser.readline().decode('utf-8', errors='replace').replace("\n", "").replace("\x00", "")
    print(i, " ", val)
    try:
        t1, t2, t3, t4, t5 = val.split(",")
        t1 = float(t1)
        t2 = float(t2)
        t3 = float(t3)
        t4 = float(t4)
        t5 = float(t5)
        # Add x and y to lists
        xs.append(i)
        t1s.append(t1)
        t2s.append(t2)
        t3s.append(t3)
        t4s.append(t4)
        t5s.append(t5)

        # Draw x and y lists
        ax.clear()
        ax.plot(xs, t1s, label="T1")
        ax.plot(xs, t2s, label="T2")
        ax.plot(xs, t3s, label="T3")
        ax.plot(xs, t4s, label="T4")
        ax.plot(xs, t5s, label="T5")

        # Format plot
        plt.title('This is how I roll...')
        plt.ylabel('measurement')
        plt.legend()
        plt.axis([max(1, i - 50), None, None, None])
    except ValueError as e:
        print(e)
        print("re-initialising port")
        ser.close()
        ser.open()


# Set up plot to call animate() function periodically
ani = animation.FuncAnimation(fig, animate, fargs=(xs, t1s, t2s, t3s, t4s, t5s), interval=10)
plt.show()
