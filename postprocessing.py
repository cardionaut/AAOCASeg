import numpy as np
import pandas as pd

frame_rate = 30 #fps
pullback_speed = 0.5 #mm/s
aortic_frame_sys = 1757
aortic_frame_dia = 1857

file_path = r'D:\Documents\2_Coding\Python\AAOCASeg\2_IVUSimages\CelikSevket\20220104\085619\Run1\PDGZHJ6B_report.txt'
df = pd.read_csv(file_path, sep='\t', encoding='latin-1')
new_columns = ['frame', 'position', 'lumen', 'plaque', 'vessel', 'plaque_burden','phenotype']
df = df.rename(columns=dict(zip(df.columns, new_columns)))
diastole = df[df.index % 2 != 0]
systole = df[df.index % 2 == 0]
diff_frame_systole = systole['frame'].diff().fillna(0)
diff_frame_diastole = diastole['frame'].diff().fillna(0)
diff_list = [diff_frame_diastole, diff_frame_systole]
mean_diff = diff_list[0].mean()
ms = mean_diff/frame_rate

def calculate_zposition(diastole, pullback_speed, frame_rate):
    z_position = np.zeros(len(diastole))
    z_position[1] = (abs(diastole['frame'].iloc[2] - diastole['frame'].iloc[1]) / frame_rate) * pullback_speed + z_position[0]
    for i in range(2, len(diastole)):
        if (i + 1) >= len(diastole):
            z_position[i] = 0  # Set the last value to 0 if index goes out of bounds
        else:
            z_position[i] = (abs(diastole['frame'].iloc[i + 1] - diastole['frame'].iloc[i]) / frame_rate) * pullback_speed + z_position[i - 1]
    diastole['z_position'] = z_position
    return diastole

diastole_flip = diastole.sort_values(by='frame', ascending=False)
systole_flip = systole.sort_values(by='frame', ascending=False)
dia = calculate_zposition(systole_flip, pullback_speed, frame_rate)
sys = calculate_zposition(diastole_flip, pullback_speed, frame_rate)
dia = dia[['frame','z_position']]
sys = sys[['frame','z_position']]
sub_df = pd.concat([dia, sys], ignore_index=True)
df = df.merge(sub_df, on='frame', how='left')

df['HR'] = np.nan   
df.loc[0, 'HR'] = 60 / ms

df.to_csv(r'D:\Documents\2_Coding\Python\AAOCASeg\full_report_rest.csv', index=False)







