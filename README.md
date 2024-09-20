# Production Planning

This codebase is a simple example of a production planning problem. The program
can be run as an API with a web interface, where the example csv files
`daily_charge_schedule`, `product_groups_monthly`, and `steel_grade_production`
can be uploaded and stored in an SQLite database.

Please first run
```bash
pip install -r requirements.txt
```

To run the API, execute the following command:

```bash
python3 app.py
```
And navigate to `http://127.0.0.1:5000/` in your browser.

Once the monthly and steel grade production csv files are uploaded, there is
also functionality to predict the production for the next month.

This prediciton is based on an exponential time weighted averaging model, which
avoids too many assumptions and allows for prediction intervals to be
calculated. The prediction for grade $j$ at time $i$ can be expressed as

$$
\hat{y}^j_{t+1} = \frac{\sum_{i=0}^{2} \exp(-i) \cdot y_{t-i}}{\sum_{i=0}^{2}
\exp(-i)},
$$

where $\hat{y}^j_{t+1}$ is then rescaled to the total production of the next
month to get the final prediction

$$
\hat{y'}^j_{t+1} = \hat{y}^j_{t+1}\cdot \frac{\mathrm{Total}}{\sum_{j=0}^{n} \hat{y}^j_{t+1}},
$$

where Total is provided by the user.

A simpler demonstration of the prediction model can be found by running

```bash
python3 predict_sept.py
```
