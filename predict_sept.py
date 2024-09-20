import numpy as np
from scipy import stats
from io import BytesIO
import base64
import matplotlib
matplotlib.use('SVG')
import matplotlib.pyplot as plt
plt.rcParams['font.family'] = 'DejaVu Sans'
plt.rcParams['text.usetex'] = False

def predict(qual, tot):
    '''Predict sept grades based on the previous 3 months, exponentially weighted
    then averaged, and rescaled to the total of sept'''
    d_with_sum = np.vstack((qual, np.sum(qual, 0)))
    d_with_predict = np.hstack((d_with_sum, np.array([np.nan]*qual.shape[0]+[tot]).reshape(-1,1)))
    weight = np.exp([-2,-1,0])
    weighted_sum = np.sum(d_with_sum*weight, 1)
    rescaled_sum = weighted_sum/sum(weight)
    d_with_predict[:-1,-1] = rescaled_sum[:-1]*tot/rescaled_sum[-1]
    return d_with_predict

def calc_interval(qual, tot):
    'Calculate 95% prediction interval'
    prediction = predict(qual, tot)
    predicted_values = prediction[:-1, -1]
    
    data_with_prediction = np.column_stack((qual, predicted_values))
    
    n = data_with_prediction.shape[1]
    weights = np.exp(range(-3, 1))
    weights = weights / np.sum(weights)
    
    weighted_mean = np.sum(data_with_prediction * weights, axis=1)
    weighted_var = np.sum(weights * (data_with_prediction.T - weighted_mean).T**2, axis=1)
    
    # Add minimum variance to handle zero-variance cases (more practical than using 0)
    weighted_var = np.maximum(weighted_var, min(weighted_var[weighted_var > 0]))
    
    # Calculate standard error of prediction
    se_pred = np.sqrt(weighted_var * (1 + 1/n))
    
    t_value = stats.t.ppf(1 - 0.05/2, df=n-1)
    
    margin_of_error = t_value * se_pred
    
    # Cant be below 0
    lower_bound = np.maximum(0, predicted_values - margin_of_error)
    upper_bound = predicted_values + margin_of_error
    # Upper limit for any value (with 95% interval) is total - sum of lower
    # bounds of other values
    upper_bound[upper_bound > tot] = tot - np.sum(lower_bound[upper_bound < tot])
    # Bring lower bound of the largest error interval up to the minimum it must be in
    # order to still produce the total value if all others are at their max
    lower_bound[np.argmax(margin_of_error)] = max(tot - np.sum(
                                     upper_bound[margin_of_error < max(margin_of_error)]),
                                                  lower_bound[np.argmax(margin_of_error)])
    
    return np.column_stack((predicted_values, lower_bound, upper_bound))

def plot_prediction(qual, tot, show=False):
    try:
        plt.figure(figsize=(7,5))
        prediction = predict(qual, tot)
        for i in range(prediction.shape[0]-1):
            plt.plot(prediction[i], '-o', label=f'Type {i+1}')
        plt.plot(prediction[-1], '-o', linewidth=2, label='Prediction', color='black')
        
        intervals = calc_interval(qual, tot)
        for i in range(qual.shape[0]):
            plt.errorbar(3+(i-qual.shape[0]/2+0.5)/80, intervals[i, 0], 
                         yerr=[[intervals[i, 0] - intervals[i, 1]], 
                               [intervals[i, 2] - intervals[i, 0]]],
                         fmt=f'C{i}.', capsize=5)
        
        plt.title('Grade Prediction for September with 95% Intervals')
        plt.xlabel('Month')
        plt.ylabel('Value')
        plt.xticks(range(4), ['June', 'July', 'August', 'September'])
        plt.legend()
        plt.grid(True)
        # plt.tight_layout()
        if show:
            return
        
        img = BytesIO()
        plt.savefig(img, format='png', dpi=120)
        img.seek(0)
        plot_url = base64.b64encode(img.getvalue()).decode()
        plt.close()  # Close the plot to free up memory
        return plot_url
    except Exception as e:
        plt.close()  # Ensure the plot is closed even if an error occurs
        raise e  # Re-raise the exception to be caught in the route handler

if __name__ == '__main__':
    
    matplotlib.use('TkAgg')
    # Data if not loaded from database
    rebar = np.array([[ 8724,  9230,  8989],
                      [10880, 11030, 10822],
                      [ 4111,  1557,  4756]])
    rebar_sept_tot = 23200

    MBQ = np.array([[   0,  202,  199],
                    [ 512,    0,    0],
                    [ 935,    0,    0],
                    [   0, 3204, 3112],
                    [   0, 3199, 2879],
                    [ 333,    0,    0],
                    [   0,    0,    0]])
    MBQ_sept_tot = 5400

    SBQ = np.array([[ 99,   0,   0],
                    [102,   0,   0],
                    [  0,   0,   0],
                    [612, 601, 603]])
    SBQ_sept_tot = 1000

    CHQ = np.array([[2078, 1032,    0],
                    [ 308,    0, 2541]])
    CHQ_sept_tot = 2200

    for qual,sept_tot in zip([rebar, MBQ, SBQ, CHQ],
                     [rebar_sept_tot, MBQ_sept_tot, SBQ_sept_tot, CHQ_sept_tot]):
        plot_prediction(qual, sept_tot, show=True)
    plt.show()
