import numpy as np
from numpy.fft import rfft
import wave
import subprocess
import json

NEED_FREQS = [2**t for t in range(5, 15)]
BOUNDARY_FREQS_RANGE = 15
SAMPLES_COUNT = 10


def learn(file, state):
    full_bd = bd_read()

    imprint = get_imprint(file)

    i = find_most_similar(full_bd[state], imprint)
    if i[0] < 0.4:
        full_bd[state].append(imprint)
    else:
        bd = full_bd[state][i[1]]
        for s in range(SAMPLES_COUNT):
            for f in range(len(bd[s])):
                bd[s][f] += bd[s][f] + imprint[s][f]/10
            bd[s] = normalize(bd[s])
            full_bd[state][i[1]] = bd
    bd_write(full_bd)


def check(file):
    imprint = get_imprint(file)

    bd = bd_read()

    good = find_most_similar(bd['good'], imprint)[0]
    bad = find_most_similar(bd['bad'], imprint)[0]

    print(good, bad)
    good /= (good + bad)/100
    return good


def find_most_similar(bd, imprint):
    if len(bd) == 0:
        return [0, 0]
    s = []
    for i in range(len(bd)):
        s.append([how_similar(bd[i], imprint), i])
    s.sort(key=lambda x: x[0])
    return s[0]


def how_similar(a, b):
    s = []
    for i in range(SAMPLES_COUNT):
        s.append(vec_angle(a[i], b[i]))
    return np.average(s)


def get_imprint(filename):
    subprocess.call(['ffmpeg\\bin\\ffmpeg', '-y', '-i', filename, filename + '.wav'])
    print("open " + filename)

    FD = 44100

    wr = wave.open(filename + '.wav', 'r')

    time_interval = round( (wr.getnframes() - FD)/SAMPLES_COUNT )
    samples = []
    for i in range(SAMPLES_COUNT):
        wr.setpos(time_interval*i)
        da = np.fromstring(wr.readframes(FD), dtype=np.int16)
        spectrum = rfft(da[::2])
        freqs = get_freqs(spectrum)
        samples.append(freqs)

    wr.close()

    return samples


def get_freqs(spectrum):
    vec = []
    for freq in NEED_FREQS:
        s = round(abs(spectrum[freq]))
        for i in range(-BOUNDARY_FREQS_RANGE, BOUNDARY_FREQS_RANGE):
            if i == 0: continue
            s += round(abs(spectrum[freq+i] / i**2))
        vec.append(s)

    vec = normalize(vec)
    return vec


def vec_angle(v1, v2):
    if len(v1) != len(v2):
        print('govno')
        return 0
    sum = 0
    for i in range(len(v1)):
        sum += v1[i] * v2[i]
    return sum


def normalize(vec):
    s = 0
    for e in vec:
        s += e ** 2
    if s == 0:
        return vec
    s = s ** 0.5
    vec = [e / s for e in vec]
    return vec


def bd_read():
    f = open('bd.bd', 'r')
    bd = json.loads(f.read())
    f.close()
    return bd


def bd_write(bd):
    f = open('bd.bd', 'w')
    f.write(json.dumps(bd))
    f.close()


print(check('test.mp3'))