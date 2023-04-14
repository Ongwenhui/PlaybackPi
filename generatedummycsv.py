import pandas as pd

maskerlist = ['bird_00083.wav', 'ambient', 'bird_00033.wav', 'water_00033.wav', 'bird_00040', 'AMSS', 'AMSS2', 'AMSS4']
gainlist = [0.13, None, None, None, '0.5', None, None, None]
SMRlist = [None, None, -3, -3, None, None, None, None]

df = pd.DataFrame()
df['filename'] = maskerlist
df['gain'] = gainlist
df['SMR'] = SMRlist

print(df)
df.to_csv('testorder.csv')