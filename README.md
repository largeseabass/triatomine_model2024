# triatomine_model2024

This repository contains all the files used in the work. Please cite the paper *pending* if you use any of these scripts in your work.


A Brief Summary of the workflow:

### 1. Observation Data filtering

#### 1.1 Clean raw data
**/scripts/python/observation_clean_filter/cleaning_process.ipynb** 
Detailed process of re-formatting all the raw datasets, concatenating them, removing duplicate and checking reliability. 

**/scripts/python/observation_clean_filter/data_column.txt** 
Explain the data columns of the resulting dataset.

**/scripts/python/observation_clean_filter/cleaning.py** 
Functions in this script is called by *cleaning_process.ipynb*.

#### 1.2 Filter data

**/scripts/python/observation_clean_filter/test_spthin.R** Remove observation points which are closer than a specific distance.

#### 1.3 Plot observation data

**/scripts/python/post_process_R_results/plot_observation_data.ipynb**

### 2. Data Preparation

#### 2.1 reproject, align and mask - prepare all the raster (bioclimatic and landcover) inputs

**/scripts/R/raster_process/align_raw_rasters.R** (Reproject), align and mask all the input rasters. Please select the input raster with the smallest geographical range as the reference raster.

**/scripts/R/others/variable_raster_range.R** This tells you the range of the values of each raster.

#### 2.2 get the grid-based data for training MaxEnt
**/scripts/python/grid_input_generation/presence_points_buffer.py** Apart from the rasters processed in step 1, a shapefile for the grid need to be generated for this task via QGIS. For more details on how to get this work, please refer to this more detailed [instruction](https://github.com/largeseabass/KissingBugsRf.git) 

#### 2.3 train MaxEnt model with 8 different setups (see our paper for more details)

The results will be saved under the **/output** directory in their specific sub-directory.

**/scripts/R/maxent_model/grid_buffer_off_train.R**

**/scripts/R/maxent_model/grid_buffer_on_train.R**

**/scripts/R/maxent_model/grid_nobuffer_off_train.R**

**/scripts/R/maxent_model/grid_nobuffer_on_train.R**

**/scripts/R/maxent_model/pixel_buffer_off_train.R**

**/scripts/R/maxent_model/pixel_buffer_on_train.R**

**/scripts/R/maxent_model/pixel_nobuffer_off_train.R**

**/scripts/R/maxent_model/pixel_nobuffer_on_train.R**

#### 2.4 select the best model setup (see our paper for more details)

**/scripts/python/post_process_R_results/select_best_parameter.ipynb** This script compares the training and testing results of the 8 setups and decide which one works the best.

#### 2.5 make predictions with the trained model of the best setup

**/scripts/R/maxent_model/pixel_buffer_off_maxent_predict.R**

#### 2.6 train Random Forest with the same model setup and make predictions

**/scripts/R/random_forest_model/pixel_buffer_off_rf_train_predict.R**

#### 2.7 Post-process results for plotting

**/scripts/R/others/prepare_plotting_data.R** This calculate the percentage difference between raster pairs.

#### 2.8 Plot graphs we used in the paper

**/scripts/python/post_process_R_results/plot_metrics_importance.ipynb** Plot the evaluation metrics and also variable importance spyder plots.

**/scripts/python/post_process_R_results/plot_prediction_conparison.ipynb** Plot what's prepared in *prepare_plotting_data.R*.

