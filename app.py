import importlib
import inspect
import io
import json
import os
from contextlib import redirect_stdout
from datetime import datetime
import numpy as np
import seaborn as sns
import pandas as pd
from flask import Flask, render_template, request, send_file
from matplotlib import pyplot as plt
from scipy import stats

app = Flask(__name__, template_folder='templates', static_url_path='/static')

df = pd.read_csv('data/HRDataset_v14.csv')
plots = []
code_to_display = {}


def count_employment_time(row):
    date_of_hire = datetime.strptime(row['DateofHire'], '%m/%d/%Y')
    date_of_termination = datetime.strptime(row['DateofTermination'], '%m/%d/%Y') if isinstance(
        row['DateofTermination'], str) else datetime.strptime('04/01/2021', '%m/%d/%Y')

    return (date_of_termination - date_of_hire).days


@app.before_first_request
def draw_graphs():
    global df, plots, code_to_display
    df['DOB_Datetime'] = df['DOB'].apply(lambda x: datetime.strptime(x, '%m/%d/%y'))
    df['DOB_Datetime'] = df['DOB_Datetime'].apply(lambda x: x.replace(year=x.year - 100) if x.year > 2000 else x)
    df['Age'] = datetime.strptime('04/01/2021', '%m/%d/%Y') - df['DOB_Datetime']
    df['Age'] = df['Age'].apply(lambda x: x.days / 365.25)

    df['EmploymentTime'] = df.apply(lambda row: count_employment_time(row), axis=1)
    df['AbsenceRate'] = df['Absences'] / df['EmploymentTime']

    z = np.abs(stats.zscore(df['Salary']))
    df_zscored = df[z < 3]
    ax = sns.displot(df_zscored, x='PerfScoreID', y='Salary')

    abscence_z = np.abs(stats.zscore(df['AbsenceRate']))
    df_absence_zscored = df_zscored[abscence_z < 2]

    df_zscored['MaritalBinary'] = df['MaritalDesc'] == 'Single'

    ax = sns.displot(df, x='PerfScoreID', y='Salary')
    ax.savefig('static/images/perfscroreid.png', dpi=300, bbox_inches='tight', pad_inches=0)

    ax = sns.displot(df_zscored, x='PerfScoreID', y='Salary')
    ax.savefig('static/images/perfscroreid2.png', dpi=300, bbox_inches='tight', pad_inches=0)

    sns.set_palette('tab10')
    ax = sns.lmplot(df_zscored, x='EngagementSurvey', y='Salary', line_kws={'color': 'red'})
    ax.savefig('static/images/eng_surv3.png', dpi=300, bbox_inches='tight', pad_inches=0)

    ax = sns.relplot(df_zscored, x='AbsenceRate', y='Salary')
    ax.savefig('static/images/abs_rate4.png', dpi=300, bbox_inches='tight', pad_inches=0)

    sns.set_theme(style="ticks")
    ax = sns.jointplot(df_absence_zscored, x='AbsenceRate', y='Salary', kind="hex")
    ax.savefig('static/images/abs_rate5.png', dpi=300, bbox_inches='tight', pad_inches=0)

    ax = sns.displot(df_zscored, x='EmpSatisfaction', y='Salary', hue='MaritalDesc')
    ax.savefig('static/images/married_satisf6.png', dpi=300, bbox_inches='tight', pad_inches=0)

    fig, axes = plt.subplots(1, 2, sharey=True, figsize=(15, 7))
    axes = axes.flatten()
    sns.histplot(df_zscored[df_zscored['MaritalBinary']], x='EmpSatisfaction', y='Salary', ax=axes[0])
    sns.histplot(df_zscored[df_zscored['MaritalBinary'] == False], x='EmpSatisfaction', y='Salary', hue='MaritalDesc',
                 ax=axes[1])
    sns.move_legend(axes[1], "upper left")
    fig.savefig('static/images/marital_binary7.png', dpi=300, bbox_inches='tight', pad_inches=0)

    with open('data/plots.json') as f:
        plots = json.load(f)

    with open('data/code_to_display.json') as f:
        code_to_display = json.load(f)


@app.route('/')
def index():
    cols_for_descriptive_stats = [{'col_name': 'Salary',
                                   'description': "Firstly, the descriptive statistics of Salary column can be useful as it is one of the most interesting columns of this dataset that will be referenced the most in my project."},
                                  {'col_name': 'EmpSatisfaction',
                                   'description': 'Secondly, the data about the satisfaction of employees. (from 0 to 5)'},
                                  {'col_name': 'Age',
                                   'description': 'The information about the age of employees in years can also be interesting and useful for the project. Due to this dataset was created in April 2021, the age of workers will be computed for this date.'}]
    descriptive_stats = []

    for item in cols_for_descriptive_stats:
        item['mean'] = round(df[item['col_name']].mean(), 2)
        item['std'] = round(df[item['col_name']].std(), 2)
        item['median'] = round(df[item['col_name']].median(), 2)
        item['min'] = round(df[item['col_name']].min(), 2)
        item['max'] = round(df[item['col_name']].max(), 2)
        descriptive_stats.append(item)

    data_trans = {}
    abs_rate = {'col_name': 'AbsenceRate'}
    abs_rate['mean'] = round(df[abs_rate['col_name']].mean(), 5)
    abs_rate['std'] = round(df[abs_rate['col_name']].std(), 5)
    abs_rate['median'] = round(df[abs_rate['col_name']].median(), 5)
    abs_rate['min'] = round(df[abs_rate['col_name']].min(), 2)
    abs_rate['max'] = round(df[abs_rate['col_name']].max(), 2)

    data_trans['abs_rate'] = abs_rate
    return render_template("index.html", descriptive_stats=descriptive_stats, data_trans=data_trans, plots=plots,
                           code_to_display=code_to_display)


@app.route('/plots')
def plots():
    return render_template('plots.html', plots_list=plots)


@app.route('/download_dataset')
def download_dataset():
    return send_file('data/HRDataset_v14.csv')
