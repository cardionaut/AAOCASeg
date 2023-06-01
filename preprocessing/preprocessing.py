import pydicom as dcm
import numpy as np


class PreProcessing:
    def __init__(self, images, frame_rate, speed) -> None:
        # self.dir_path = config.dir_path
        self.images = images
        self.frame_rate = frame_rate
        self.speed = speed

    def __call__(self):
        # images, frame_rate, speed = self.DICOM_reader()
        tags_dia = self.IVUS_gating_diastole()
        tags_sys, distance_frames = self.IVUS_gating_systole(tags_dia)
        dia, sys = self.stack_generator(tags_dia, tags_sys)

        return tags_dia, tags_sys, distance_frames


    def DICOM_reader(self):
        """Reads DICOM file and returns numpy array and relevant metadata"""
        ds = dcm.dcmread(self.dir_path)
        images = np.array(ds.pixel_array)
        frame_rate = int(ds.CineRate)
        speed = float(ds.IVUSPullbackRate)
        # StartFrame = int(ds.IVUSPullbackStartFrameNumber)
        # StopFrame = int(ds.IVUSPullbackStopFrameNumber)
        return images, frame_rate, speed


    def IVUS_gating_diastole(self):
        """Performs gating of IVUS images"""

        if len(self.images.shape) == 4:
            self.images = self.images[:, :, :, 0]

        num_images = self.images.shape[0]
        pullback = (
            self.speed * (num_images - 1) / self.frame_rate
        )  # first image is recorded instantly so no time delay

        s0 = np.zeros((num_images - 1, 1))
        s1 = np.zeros((num_images - 1, 1))

        for i in range(num_images - 1):
            C = self.normxcorr(self.images[i, :, :], self.images[i + 1, :, :])
            s0[i] = 1 - np.max(C)
            gradx, grady = np.gradient(self.images[i, :, :])
            gradmag = abs(np.sqrt(gradx**2 + grady**2))
            s1[i] = -np.sum(gradmag)

        # normalize data
        s0_plus = s0 - np.min(s0)
        s1_plus = s1 - np.min(s1)

        s0_norm = s0_plus / np.sum(s0_plus)
        s1_norm = s1_plus / np.sum(s1_plus)

        alpha = 0.25
        s = alpha * s0_norm + (1 - alpha) * s1_norm

        # determine Fs (sampling frequency)
        t = np.linspace(0, pullback / self.speed, num_images)
        Fs = num_images / np.max(t)
        NFFT = int(2 ** np.ceil(np.log2(np.abs(len(s)))))
        ss = np.fft.fft(s, NFFT, 0) / len(s)
        freq = Fs / 2 * np.linspace(0, 1, NFFT // 2 + 1)

        # in order to return correct amplitude fft must be divided by length of sample
        freq[freq < 0.75] = 0
        freq[freq > 1.66] = 0

        ss1 = ss[0 : NFFT // 2 + 1]
        ss1[freq == 0] = 0

        # determine maximum frequency component of ss
        fm = np.argmax(np.abs(ss1))
        fm = freq[fm]

        # find cutoff frequency
        sigma = 0.4
        fc = (1 + sigma) * fm

        # construct low pass kernal (fmax is half of the transducer frame rate)
        fmax = Fs / 2
        tau = 25 / 46
        v = 21 / 46
        f = ((fc / fmax) * np.sinc((fc * np.arange(1, num_images + 1)) / fmax)) * (
            tau - v * np.cos(2 * np.pi * (np.arange(1, num_images + 1) / num_images))
        )

        # determine low frequency signal
        s_low = np.convolve(s[:, 0], f)
        s_low = s_low[0 : len(s)]  # take first half only

        # find first minimum in heartbeat
        hr_frames = int(np.round(Fs / fm))  # heart rate in frames
        idx = np.argmin(s_low[0:hr_frames])
        tags_dia = []
        tags_dia.append(idx)
        k = 0

        while idx < (num_images - hr_frames):
            k = k + 1
            # based on known heart rate seach within 2 frames for local minimum
            # increase fc to look at higher frequencies
            idx2 = idx + np.arange(hr_frames - 2, hr_frames + 3)
            # find local minimum
            idx2 = idx2[idx2 < num_images - 1]
            min_idx = np.argmin(s_low[idx2])
            idx = idx2[min_idx]
            tags_dia.append(idx)

        fc = fc + fm
        j = 1
        s_low = np.expand_dims(s_low, 1)

        while fc < fmax:
            # recalculate f with new fc value
            f = ((fc / fmax) * np.sinc((fc * np.arange(1, num_images + 1)) / fmax)) * (
                tau - v * np.cos(2 * np.pi * (np.arange(1, num_images + 1) / num_images))
            )
            # add extra columns to s_low to create surface as in paper
            s_temp = np.expand_dims(np.convolve(s[:, 0], f), 1)
            s_low = np.concatenate((s_low, s_temp[0 : len(s)]), 1)

            # adjust each previous minimum p(i) to the nearest minimum
            for i in range(len(tags_dia)):
                # find index of new lowest p in +/-1 neighbour search
                search_index = np.arange(tags_dia[i] - 1, tags_dia[i] + 2)
                search_index = search_index[search_index >= 0]
                search_index = search_index[search_index < len(s)]  # <=?
                search_index = np.in1d(np.arange(0, len(s)), search_index)
                # determine index of min value in the specified neighbour range
                min_value = np.argmin(s_low[search_index, j])
                # switch from logical to indexed values
                search_index = np.argwhere(search_index)
                tags_dia[i] = search_index[min_value][0]
            # iteratively adjust to the new minimum
            # increase fc to look at higher frequencies
            fc = fc + fm
            j = j + 1

        # normalize each column of s_low
        max_values = np.max(s_low, 0)
        s_low_norm = s_low / np.tile(max_values, [len(s), 1])

        # group images between p(i) and p(i+1)
        # output frames corresponding to each cardiac phase
        HB = []
        for i in range(len(tags_dia) - 1):
            HB.append(list(np.arange(tags_dia[i], tags_dia[i + 1])))

        # identify P cardiac phases (where P is the amount of frames in shortest heartbeat
        P = [len(entry) for entry in HB]
        P = min(P)

        # each column in U corresponds to a cardiac phase (systole, diastole)
        U = np.zeros((len(HB), P))
        for i in range(len(HB)):
            U[i, :] = HB[i][0:P]

        # determine heartbeat period
        t_HB = t[tags_dia[1:]] - t[tags_dia[:-1]]

        return tags_dia


    def normxcorr(self, image1, image2):
        C = np.zeros_like(image1)
        image1_mean = np.mean(image1)
        image2_mean = np.mean(image2)
        image1_std = np.std(image1)
        image2_std = np.std(image2)
        C = np.sum((image1 - image1_mean) * (image2 - image2_mean)) / (
            image1_std * image2_std
        )
        C = C / (image1.shape[0] * image1.shape[1])
        return C


    def IVUS_gating_systole(self, tags_dia):
        """based on the frames p from IVUS gating, find the systolic frames with the formula 425 - 1.5 * HR"""
        distance_frames = []
        tags_sys = []
        for i in range(len(tags_dia) - 1):
            frame_diff = tags_dia[i + 1] - tags_dia[i]
            time_diff = frame_diff / self.frame_rate
            HR = 60 / time_diff
            s_to_systole = float((425 - 1.5 * HR) / 1000)
            frames = int(s_to_systole * self.frame_rate)
            tags_sys.append(tags_dia[i] + frames)
            distance = time_diff * self.speed
            distance_frames.append(distance)
        return tags_sys, distance_frames


    def stack_generator(self, tags_dia, tags_sys):
        """generate a stack for systolic and diastolic images based on list position"""
        diastole = []
        systole = []
        for i in range(len(self.images)):
            if i in tags_dia:
                diastole.append(self.images[i])
            if i in tags_sys:
                systole.append(self.images[i])
        # for i in range(len(diastole)):  # transpose and rotate
        #     diastole[i] = np.flipud(diastole[i])
        # for i in range(len(systole)):  # transpose and rotate
        #     systole[i] = np.flipud(systole[i])
        diastole = np.array(diastole)
        systole = np.array(systole)
        return diastole, systole
