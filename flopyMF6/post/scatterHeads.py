import pickle
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

def scatterHeads(sim, nam, obs_headsfp, outpngfp):
    with open(obs_headsfp, "rb") as f: obs_head = pickle.load(f)
    gwf = sim.get_model(nam)

    # # individual plots by layer
    # for k, obs in enumerate(obs_head):
    #     obs = obs.flatten()
    #     head = gwf.output.head().get_data()[k].flatten()
    #     # resid = np.sqrt(np.mean((head[obs_head>0] - obs_head[obs_head>0])**2)) # RMSE
    #     df = pd.DataFrame({
    #         'simulated': head[(obs>0) & (head<9999)],
    #         'observed': obs[(obs>0) & (head<9999)],
    #     })
    #     df = df[df['simulated'] > 0]
    #     print(df)

    #     fig, ax_main = plt.subplots(figsize=(8, 6))
    #     pm = 10
    #     mn, mx = np.min(df), np.max(df)    
    #     df.plot.scatter(x='observed',y='simulated',s=1,c='#00006C0D',ax=ax_main)
    #     ax_main.plot( [mn, mx], [mn, mx], color='red', linestyle='--' )
    #     ax_main.plot( [mn+pm, mx], [mn, mx-pm], color='red', linestyle='dotted' )
    #     ax_main.plot( [mn, mx-pm], [mn+pm, mx], color='red', linestyle='dotted' )
    #     ax_main.grid(True, linestyle=':', alpha=0.5)
    #     # ax_main.set_title('Main Plot with Histogram Inset')

    #     # Create inset axes: [left, bottom, width, height] in figure fraction (0-1)
    #     left, bottom, width, height = 0.63, 0.16, 0.3, 0.3
    #     ax_inset = fig.add_axes([left, bottom, width, height])

    #     # Plot histogram in inset
    #     ax_inset.hist(df['simulated']-df['observed'], bins=30, color='skyblue', edgecolor='black', alpha=0.7)
    #     ax_inset.set_title('Histogram', fontsize=9)
    #     ax_inset.tick_params(axis='both', which='major', labelsize=8)

    #     if not outpngfp is None: plt.savefig('{}-{}.png'.format(outpngfp[:-4], k), bbox_inches='tight')
        
    #     plt.show()



    head = gwf.output.head().get_data()
    # resid = np.sqrt(np.mean((head[obs_head>0] - obs_head[obs_head>0])**2)) # RMSE
    df = pd.DataFrame({
        'simulated': head[(obs_head>0) & (head<9999)],
        'observed': obs_head[(obs_head>0) & (head<9999)],
    })
    df = df[df['simulated'] > 0]
    # print(df)

    fig, ax_main = plt.subplots(figsize=(8, 6))
    pm = 10
    mn, mx = np.min(df), np.max(df)    
    df.plot.scatter(x='observed',y='simulated',s=1,c='#00006C0D',ax=ax_main)
    ax_main.plot( [mn, mx], [mn, mx], color='red', linestyle='--' )
    ax_main.plot( [mn+pm, mx], [mn, mx-pm], color='red', linestyle='dotted' )
    ax_main.plot( [mn, mx-pm], [mn+pm, mx], color='red', linestyle='dotted' )
    ax_main.grid(True, linestyle=':', alpha=0.5)
    # ax_main.set_title('Main Plot with Histogram Inset')

    # Create inset axes: [left, bottom, width, height] in figure fraction (0-1)
    left, bottom, width, height = 0.63, 0.16, 0.3, 0.3
    ax_inset = fig.add_axes([left, bottom, width, height])

    # Plot histogram in inset
    ax_inset.hist(df['simulated']-df['observed'], bins=30, color='skyblue', edgecolor='black', alpha=0.7)
    ax_inset.set_title('Histogram', fontsize=9)
    ax_inset.tick_params(axis='both', which='major', labelsize=8)

    if not outpngfp is None: plt.savefig(outpngfp, bbox_inches='tight')
    
    plt.show()    