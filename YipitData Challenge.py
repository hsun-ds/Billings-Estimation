#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Jun 13 12:28:04 2020

@author: Heqing Sun
"""

import os
import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt

# Get current working directory
os.getcwd()

# Read Excel data
df = pd.read_excel (r'./data/raw/Q4_2013_Groupon_North_America_Data_XLSX (1).xlsx', sheet_name='Q4 2013 Raw Data')
df_backup = df.copy()
## 138534 obs, 7 vars
df.head()

# =============================================================================
# EDA
# =============================================================================
# Define some functions
# For all varibales
def dataframe_description(df, col):
    print('Column Name:', col)
    print('Number of Rows:', len(df.index))
    print('Number of Missing Values:', df[col].isnull().sum())
    print('Percent Missing:', df[col].isnull().sum()/len(df.index)*100, '%')
    print('Number of Unique Values:', len(df[col].unique()))
    print('\n')

# For continuous variables    
def descriptive_stats_continuous(df, col):
    print('Column Name:', col)
    print('Mean:', np.mean(df[col]))
    print('Median:', np.nanmedian(df[col]))
    print('Standard Deviation:', np.std(df[col]))
    print('Minimum:', np.min(df[col]))
    print('Maximum:', np.max(df[col]))
    print('\n')

# Plotting distribution plots for continuous variables
def plot_distribution(df, col):
    sns.set(style='darkgrid')
    ax = sns.distplot(df[col].dropna())
    plt.xticks(rotation=90)
    plt.title('Distribution Plot for ' + col)
    plt.show()
    
# Plotting countplots for categorical vairables 
def plot_counts(df, col):
    sns.set(style='darkgrid')
    ax = sns.countplot(x=col, data=df)
    plt.xticks(rotation=90)
    plt.title('Count Plot')
    plt.show()

df.columns.values
## ['Deal ID', 'Units Sold', 'Billings', 'Start Date', 'Deal URL', 'Segment', 'Inventory Type']
continuous_vars = ['Units Sold', 'Billings']
categorical_vars = ['Start Date', 'Segment', 'Inventory Type']

for col in list(df.columns.values):
    dataframe_description(df, col)
## Each row is a unique Deal ID, no duplicates
## No mising value in all columns

for col in list(continuous_vars):
    descriptive_stats_continuous(df, col)
## Units Sold varibale: minimum is -9100.0, which is weird
## Billings variabls: minimu is -218062.90099999993, which is weird

for col in list(continuous_vars):
    plot_distribution(df, col)

for col in list(categorical_vars):
    plot_counts(df, col)

# Check if Units Sold is same symbol with Billings
df_check = df.copy()
df_check['Units Sold x Billings'] = df_check['Units Sold'] * df_check['Billings']
df_check[df_check['Units Sold x Billings'] < 0]
## All rows Units Sold and Billings variables have the same sign

# Create indicator variable for 'First - Party' inventory
# df = df_backup.copy()
df['Inventory Type'].unique()
df['Inventory_FP'] = np.where(df['Inventory Type']=='First - Party', 1, 0)
df['Inventory_TP'] = np.where(df['Inventory Type']=='Third - Party', 1, 0)
df.drop(['Deal ID', 'Deal URL', 'Inventory Type'], axis = 1, inplace = True) 
df.columns

# Split the dataset by segments
local = df[(df.Segment=='Local')]
goods = df[(df.Segment=='Goods')]
travel = df[(df.Segment=='Travel')]

# Aggregation
local['Start Date'] = local['Start Date'].astype(str)
local['Start Date'] = pd.to_datetime(local['Start Date'])
local_agg = local.groupby(['Start Date'], as_index=True).agg({'Units Sold':'sum','Billings':'sum','Inventory_FP':'sum','Inventory_TP':'sum'})


goods['Start Date'] = goods['Start Date'].astype(str)
goods['Start Date'] = pd.to_datetime(goods['Start Date'])
goods_agg = goods.groupby(['Start Date'], as_index=True).agg({'Units Sold':'sum','Billings':'sum','Inventory_FP':'sum','Inventory_TP':'sum'})

travel['Start Date'] = travel['Start Date'].astype(str)
travel['Start Date'] = pd.to_datetime(travel['Start Date'])
travel_agg = travel.groupby(['Start Date'], as_index=True).agg({'Units Sold':'sum','Billings':'sum','Inventory_FP':'sum','Inventory_TP':'sum'})


# Sort local aggregated dataframe
local_agg_sorted = local_agg.sort_index()

# Split local dataframe to two - before 2013 and Year 2013
local_2013 = local_agg_sorted.loc['2013-01-01':'2013-12-31'] ## 354 obs (missing 11 days)
local_before_2013 = local_agg_sorted.loc[:'2012-12-31'] ## 150 obs

# Add 11 rows represent missing 11 days
local_2013_full = local_2013.asfreq(freq='1D')

# Join two dataframes vertically
local_agg_full_sorted = local_before_2013.append(local_2013_full) ## 515 obs

# Write dataframe to csv and pickle file
local_agg_full_sorted.to_csv('./data/clean/local_agg_full_sorted.csv')
local_agg_full_sorted.to_pickle('./data/clean/local_agg_full_sorted.pkl')

local_agg_full_sorted = pd.read_pickle(r'./data/clean/local_agg_full_sorted.pkl')

# =============================================================================
# Imputation
# =============================================================================

# Plot with missing data
local_agg_full_sorted.plot()

# Method 1 - Simple Imputer -- not so good b/c all missing days are imputed as same
from sklearn.impute import SimpleImputer
local_si = SimpleImputer().fit_transform(local_agg_full_sorted)
## 418

# Method 2 - Direct Interpolation
local_ip = local_agg_full_sorted.interpolate()
local_ip.plot()
## 442

# Method 3 - pchip Interpolation
local_pc = local_agg_full_sorted.interpolate(method='pchip') ## cumulative distribution 
local_pc.plot()
## 439

# Method 4 - akima Interpolation - USE THIS ONE FOR NOW
local_ak = local_agg_full_sorted.interpolate(method='akima') ##  smooth plotting
local_ak.plot()
## 436

# Method 5 - MICE OKAY
local_mice = pd.read_csv(r'./data/clean/local_mice.csv')
local_mice.set_index('Start.Date', inplace=True)
local_mice.plot()
## 417

# Method 6 - kNN -- not so good b/c all missing days are imputed as same
from sklearn.impute import KNNImputer
local_knn = KNNImputer(n_neighbors=5).fit_transform(local_agg_full_sorted)
local_knn = pd.DataFrame(local_knn)
local_knn.index = list(local_agg_full_sorted.index) 
local_knn.plot()
## 418

# =============================================================================
# Get sum of each segment
# =============================================================================
local_ak.sum(axis = 0, skipna = True)/1000000
# Units Sold       14.432131
# Billings        436.451398

goods_agg.sum(axis = 0, skipna = True)/1000000
# Units Sold       10.419746
# Billings        282.245671

travel_agg.sum(axis = 0, skipna = True)/1000000
# Units Sold       0.378910
# Billings        70.552062


# =============================================================================
# LSTM
# =============================================================================
from keras.models import Sequential
from keras.layers import Dense
from keras.layers import LSTM
from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics import mean_squared_error




# =============================================================================
# Try Some TIme Series
# =============================================================================
local_ts = local[['Start Date','Billings']]
local_ts['Billings'].value_counts()
local_ts['Billings'].isnull().sum()
local_ts['Start Date'] = local_ts['Start Date'].astype(str)

goods_ts = goods[['Start Date','Billings']]
goods_ts['Billings'].value_counts()
goods_ts['Billings'].isnull().sum()
goods_ts['Start Date'] = goods_ts['Start Date'].astype(str)

travel_ts = travel[['Start Date','Billings']]
travel_ts['Billings'].value_counts()
travel_ts['Billings'].isnull().sum()
travel_ts['Start Date'] = travel_ts['Start Date'].astype(str)

# Aggreagation to day level using sum
local_ts_agg = local_ts.groupby(['Start Date'], as_index=True)['Billings'].sum()
goods_ts_agg = goods_ts.groupby(['Start Date'], as_index=True)['Billings'].sum()
travel_ts_agg = travel_ts.groupby(['Start Date'], as_index=True)['Billings'].sum()

# Some plots
from matplotlib import pyplot
local_ts_agg.plot()
pyplot.show()

goods_ts_agg.plot()
pyplot.show()

travel_ts_agg.plot()
pyplot.show()



