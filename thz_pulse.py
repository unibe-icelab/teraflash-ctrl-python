import numpy as np
import matplotlib.pyplot as plt


def pulse(x, noise=1):
    offset = 1
    if noise != 0: noise = np.random.normal(0, 0.02, 1)
    offset = offset + noise
    pulse = np.sin(x + offset) ** 99 * np.sin(x + offset + 1.5) * 8
    pulse[x > 2] = 0
    pulse[x < -2] = 0
    if noise != 0: noise = np.random.normal(0, 0.02, len(pulse))
    return pulse + noise


if __name__ == "__main__":
    x = np.linspace(-8, 2, 10000)
    fig = plt.gcf()
    fig.set_size_inches(10,2)
    plt.plot(x, pulse(x, 0), lw=4, color="black")
    plt.axis("off")
    plt.savefig("pulse.pdf")
    plt.show()