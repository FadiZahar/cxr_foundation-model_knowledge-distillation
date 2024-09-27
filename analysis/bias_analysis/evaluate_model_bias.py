import os
import argparse
import numpy as np
import pandas as pd
import seaborn as sns
from tqdm import tqdm
from sklearn.manifold import TSNE
from sklearn.decomposition import PCA
from scipy.stats import ks_2samp
from statsmodels.stats.multitest import multipletests

import matplotlib.pyplot as plt
from matplotlib import font_manager
import matplotlib.gridspec as gridspec
import matplotlib.image as mpimg

# Check if Latin Modern Roman (~LaTeX) is available, and set it; otherwise, use the default font
if 'Latin Modern Roman' in [f.name for f in font_manager.fontManager.ttflist]:
    plt.style.use('default')
    plt.rcParams['font.family'] = 'Latin Modern Roman'

np.random.seed(42)



# Import global shared variables
from config.config_shared import OUT_DPI, RACES, SEXES
# Import the configuration loader
from config.loader_config import load_config, get_dataset_name

# Define other global variables
OUT_FORMAT = 'png'
RASTERIZED_SCATTER = True
N_SAMPLES = 1000

ALPHA = 0.6
MARKER = 'o'
MARKERSIZE = 40
FONT_SCALE = 1.3
COLOR_PALETTE1 = ['deepskyblue', 'darkorange', 'forestgreen', 'darkorchid', 'red']
COLOR_PALETTE2 = 'plasma_r'
KIND = 'scatter'

AGE_BINS = {
    '0-20': (0, 20),
    '21-30': (21, 30),
    '31-40': (31, 40),
    '41-50': (41, 50),
    '51-60': (51, 60),
    '61-70': (61, 70),
    '71-80': (71, 80),
    '81+': (81, float('inf'))
}

np.random.seed(42)



def get_num_features(data):
    embed_cols = [col for col in data.columns if col.startswith('embed_')]
    if not embed_cols:
        raise ValueError('No "embed_" columns found in the DataFrame.')
    max_embed_num = max(int(col.split('_')[1]) for col in embed_cols)
    return max_embed_num
    

def read_csv_file(file_path):
    try:
        data = pd.read_csv(file_path)
        if data.empty:
            raise ValueError(f"The file '{file_path}' is empty.")
        return data
    except FileNotFoundError:
        raise FileNotFoundError(f"The file '{file_path}' was not found.")
    except pd.errors.EmptyDataError:
        raise ValueError(f"The file '{file_path}' is empty.")
    except pd.errors.ParserError:
        raise ValueError(f"The file '{file_path}' could not be parsed.")
    except Exception as e:
        raise Exception(f"An unexpected error occurred while reading the file '{file_path}': {str(e)}")
    

def apply_pca(embeds, df, pca_dir_path, n_components=0.99):
    pca = PCA(n_components=n_components, whiten=False)
    embeds_pca = pca.fit_transform(embeds)

    # Extracting and storing PCA results
    df['PCA Mode 1'] = embeds_pca[:, 0]
    df['PCA Mode 2'] = embeds_pca[:, 1]
    df['PCA Mode 3'] = embeds_pca[:, 2]
    df['PCA Mode 4'] = embeds_pca[:, 3]

    # Calculate retained variance
    exp_var = pca.explained_variance_ratio_
    cumul_exp_var = np.cumsum(exp_var)

    # Plotting the explained variance
    plt.figure()
    plt.plot(range(1, len(exp_var) + 1), cumul_exp_var, color='mediumblue')
    plt.xlabel('Mode', fontsize=12)
    plt.ylabel('Retained Variance', fontsize=12)
    plt.title('PCA Cumulative Explained Variance')
    
    # Dynamic tick marks: Calculate the interval to achieve 10 ticks including 1
    tick_interval = max(1, len(cumul_exp_var) // 10)
    tick_interval = int(round(tick_interval / 10) * 10)  # Adjusted to the nearest multiple of 10
    tick_interval = max(10, tick_interval)  # Ensure it's at least 10 or the calculated value
    ticks = [1] + list(range(tick_interval, len(cumul_exp_var) + 1, tick_interval))
    if ticks[-1] != len(cumul_exp_var):  # Ensure the last tick marks the last mode
        ticks.append(len(cumul_exp_var))
    plt.xticks(ticks)
    
    # Save plot
    plot_path = os.path.join(pca_dir_path, 'pca_cumulative_explained_variance.png')
    plt.savefig(plot_path, dpi=OUT_DPI)
    plt.close()

    # Save explained variance data to CSV
    exp_var_df = pd.DataFrame({
        'PCA Mode': range(1, len(exp_var) + 1),
        'Explained Variance': exp_var,
        'Cumulative Explained Variance': cumul_exp_var
    })
    csv_path = os.path.join(pca_dir_path, 'pca_explained_variance.csv')
    exp_var_df.to_csv(csv_path, index=False)

    print(f"PCA output shape: {embeds_pca.shape}")
    print(f"Plot saved to: {plot_path}")
    print(f"Explained variance CSV saved to: {csv_path}")
    return embeds_pca, exp_var


def apply_tsne(embeds_pca, df, tsne_dir_path, n_components=2):
    # Apply t-SNE to the PCA-reduced embeddings
    tsne = TSNE(n_components=n_components, init='random', learning_rate='auto')
    embeds_tsne = tsne.fit_transform(embeds_pca)

    # Extracting and storing t-SNE results
    df['t-SNE Dimension 1'] = embeds_tsne[:, 0]
    df['t-SNE Dimension 2'] = embeds_tsne[:, 1]

    # Save the results to a CSV for further analysis
    tsne_df = pd.DataFrame({
        't-SNE Dimension 1': embeds_tsne[:, 0],
        't-SNE Dimension 2': embeds_tsne[:, 1]
    })
    csv_path = os.path.join(tsne_dir_path, 'tsne_results.csv')
    tsne_df.to_csv(csv_path, index=False)
    
    print(f"t-SNE data saved to: {csv_path}")
    return embeds_tsne


def bin_age(age):
    for label, (low, high) in AGE_BINS.items():
        if low <= age <= high:
            return label
    return 'Unknown' 


def sample_by_race(df, n_samples, output_dir, races):
    sampled_dfs = {}
    for race in tqdm(races, desc="Sampling by race"):
        sampled_df = df[df['race'] == race].sample(n=n_samples)
        sampled_df['binned_age'] = sampled_df['age'].apply(bin_age)
        sampled_dfs[race] = sampled_df
    
    # Concatenate the sampled dataframes
    sample_test = pd.concat(sampled_dfs.values())
    # Replace 'Other' with 'Others' in the 'disease' column
    sample_test['disease'] = sample_test['disease'].replace('Other', 'Others')
    
    # Save the concatenated DataFrame to a CSV
    csv_filename = 'inspection_sample.csv'
    output_filepath = os.path.join(output_dir, csv_filename)
    sample_test.to_csv(output_filepath)
    
    print(f"Sampled data saved to: {output_filepath}")
    return sample_test


def plot_feature_modes(df, method, mode_indices, xdat, ydat, labels_dict, plots_joint_dir_path, plots_marginal_dir_path, 
                   out_format, out_dpi, color_palette1, color_palette2, font_scale, alpha, marker, markersize, kind, rasterized):
    sns.set_theme(style="white", palette=color_palette1, font_scale=font_scale, font='Latin Modern Roman')
    xlim = None
    ylim = None
    
    # Loop through each label in labels_dict to create plots for each category
    for i, (label, settings) in enumerate(labels_dict.items()):
        current_palette = color_palette2 if label == 'Age' else color_palette1
        # Jointplot for each label
        if i == 0:
            fig = sns.jointplot(x=xdat, y=ydat, hue=label, kind=kind, alpha=alpha, marker=marker, s=markersize,
                                palette=current_palette, hue_order=settings['hue_order'], data=df, 
                                joint_kws={'rasterized': rasterized}, marginal_kws={'common_norm': False})
            xlim = fig.ax_joint.get_xlim()
            ylim = fig.ax_joint.get_ylim()
        else:
            # Apply previously determined xlim and ylim
            fig = sns.jointplot(x=xdat, y=ydat, hue=label, kind=kind, alpha=alpha, marker=marker, s=markersize,
                                palette=current_palette, hue_order=settings['hue_order'], data=df, 
                                joint_kws={'rasterized': rasterized}, marginal_kws={'common_norm': False}, 
                                xlim=xlim, ylim=ylim)
        fig.ax_joint.legend(loc='upper right')
        joint_filename = f'{method}-{label}-joint.{out_format}'
        joint_filepath = os.path.join(plots_joint_dir_path, joint_filename)
        plt.savefig(joint_filepath, bbox_inches='tight', dpi=out_dpi)
        plt.close()
        
        # Marginal KDE plots for x and y
        for axdat, index, axlim in zip([xdat, ydat], mode_indices, [xlim, ylim]):
            fig, ax = plt.subplots(figsize=(10, 3))
            p = sns.kdeplot(x=axdat, hue=label, fill=True, hue_order=settings['hue_order'], data=df, ax=ax, 
                            palette=current_palette, common_norm=False)
            p.get_legend().set_title(None)
            p.spines[['right', 'top']].set_visible(False)
            p.set_xlim(axlim)
            method_name = method.split('-')[0]
            marginal_filename = f'{method_name}-{index}-{label}-marginal.{out_format}'
            marginal_filepath = os.path.join(plots_marginal_dir_path, marginal_filename)
            plt.savefig(marginal_filepath, bbox_inches='tight', dpi=out_dpi)
            plt.close()

        print(f"Plots for {label} saved to: (Joint) {joint_filepath} and (Margina) {marginal_filepath}")


def aggregate_jointplots_into_grid(output_dir, models, labels, grid_shape=(2, 2), figsize=(16, 8), font_size=12, 
                                  title_font_delta=4, wspace=-0.15, hspace=0.05, dataset_name='CheXpert'):
    """Aggregates the joint plots into a grid and displays them."""
    for i, model in enumerate(models):
        fig = plt.figure(figsize=figsize)
        gs = gridspec.GridSpec(nrows=grid_shape[0], 
                               ncols=grid_shape[1], 
                               width_ratios=[1] * grid_shape[1], 
                               height_ratios=[1] * grid_shape[0])

        axes = [fig.add_subplot(gs[row, col]) for row in range(grid_shape[0]) for col in range(grid_shape[1])]

        model_shortname = model['shortname'].replace(' ', '_')
        model_aucroc_dir_path = os.path.join(output_dir, model_shortname)

        # Add title
        title = f"{model['shortname']}\nROC Curve | {dataset_name}"
        fig.suptitle(title, fontsize=font_size+title_font_delta)

        for j, label in enumerate(labels):
            # Calculate the row and column of the subplot in the grid based on the index `j`
            ax_subplot = axes[j]

            # Construct the filename for the grid-ready plot
            roccurve_filename_grid = f'{model_shortname}__roc_curve_gridready__({dataset_name}--{label.replace(" ", "_")}).png'
            roccurve_filepath = os.path.join(model_aucroc_dir_path, roccurve_filename_grid)

            # Load the image and display it in the subplot
            img = mpimg.imread(roccurve_filepath)
            ax_subplot.imshow(img)
            ax_subplot.axis('off')
        
        grid_plot_filename = f'{model_shortname}__roc_curves_grid_combined__({dataset_name}--{label.replace(" ", "_")}).png'
        plt.tight_layout()
        plt.subplots_adjust(wspace=wspace, hspace=hspace)
        plt.savefig(os.path.join(output_dir, grid_plot_filename), dpi=OUT_DPI)
        plt.close()


def perform_statistical_tests(df, bias_stats_dir_path, races, sexes, diseases, exp_var):
    # Define function to perform Two-sample Kolmogorov–Smirnov tests between each pair of subgroups
    def stats_tests(marginal, samples):
        groups = {race: samples[samples['race'] == race] for race in races}
        groups.update({sex: samples[samples['sex'] == sex] for sex in sexes})
        groups.update({disease: samples[samples['disease'] == disease] for disease in diseases})
        # Define comparisons
        comparisons = [
            (diseases[0], diseases[1]), 
            (races[0], races[1]),  
            (races[0], races[2]),
            (races[1], races[2]),
            (sexes[0], sexes[1])
        ]
        # Perform Two-sample Kolmogorov–Smirnov tests
        results = []
        for group1, group2 in comparisons:
            result = ks_2samp(groups[group1][marginal], groups[group2][marginal])
            results.append(result.pvalue)
        return results

    # Get p-values for each PCA mode
    pvals = np.array([stats_tests(f'PCA Mode {i+1}', df) for i in tqdm(range(4), desc="Performing statistical tests")])
    
    # Adjust p-values using the FDR method (Benjamini-Yekutieli Procedure)
    res = multipletests(pvals.flatten(), alpha=0.05, method='fdr_by', is_sorted=False, returnsorted=False)
    reshaped_rejected = np.array(res[0]).reshape((4,5))
    reshaped_adjusted_pvals = np.array(res[1]).reshape((4,5))

    # Create a DataFrame for the results
    modes = [f'PCA Mode {i+1}' for i in range(4)]
    columns = ['Mode', 'Explained Variance', f'{diseases[0]} vs {diseases[1]}', f'{races[0]} vs {races[1]}', 
               f'{races[0]} vs {races[2]}', f'{races[1]} vs {races[2]}', f'{sexes[0]} vs {sexes[1]}']
    
    save_statistical_data(bias_stats_dir_path=bias_stats_dir_path, modes=modes, columns=columns, exp_var=exp_var[:4], 
                          adjusted_pvals=reshaped_adjusted_pvals, rejected=reshaped_rejected)
    

def save_statistical_data(bias_stats_dir_path, modes, columns, exp_var, adjusted_pvals, rejected):
    # Prepare data for adjusted p-values
    adjusted_pvalues_data = { 'Mode': modes, 'Explained Variance': exp_var }
    for i, label in enumerate(columns[2:]):
        adjusted_pvalues_data[label] = adjusted_pvals[:, i]
    adjusted_pvalues_df = pd.DataFrame(adjusted_pvalues_data, columns=columns)
    pvalues_csv_path = os.path.join(bias_stats_dir_path, 'statistical_tests_adjusted_pvalues.csv')
    adjusted_pvalues_df.to_csv(pvalues_csv_path, index=False)

    # Prepare data for rejection results
    rejection_data = { 'Mode': modes, 'Explained Variance': exp_var }
    for i, label in enumerate(columns[2:]):
        rejection_data[label] = rejected[:, i]
    rejection_df = pd.DataFrame(rejection_data, columns=columns)
    rejection_csv_path = os.path.join(bias_stats_dir_path, 'statistical_tests_rejections.csv')
    rejection_df.to_csv(rejection_csv_path, index=False)

    print(f"Adjusted p-values saved to: {pvalues_csv_path}")
    print(f"Rejection results saved to: {rejection_csv_path}")



def parse_args():
    parser = argparse.ArgumentParser(description="Model bias inspection.")
    parser.add_argument('--outputs_dir', type=str, required=True, help='Path to outputs directory')
    parser.add_argument('--config', default='chexpert', choices=['chexpert', 'mimic'], help='Config dataset module to use')
    parser.add_argument('--labels', nargs='+', default=['Pleural Effusion', 'Others', 'No Finding'], 
                        help='List of labels to process')
    parser.add_argument('--local_execution', type=bool, default=True, help='Boolean to check whether the code is run locally or remotely')
    return parser.parse_args()


if __name__ == "__main__":

    args = parse_args()
    # Load the configuration dynamically based on the command line argument
    config = load_config(args.config)
    # Accessing the configuration to import dataset-specific variables
    dataset_name = get_dataset_name(args.config)

    if args.local_execution:
        # Construct local file path dynamically based on the dataset name
        local_base_path = '/Users/macuser/Desktop/Imperial/70078_MSc_AI_Individual_Project/code/Test_Resample_Records'
        local_dataset_path = os.path.join(local_base_path, dataset_name)
        local_filename = os.path.basename(config.TEST_RECORDS_CSV)  # Extracts filename from the config path
        TEST_RECORDS_CSV = os.path.join(local_dataset_path, local_filename)
    else:
        TEST_RECORDS_CSV = config.TEST_RECORDS_CSV

    # Path to outputs and data characteristics files
    embeddings_csv_filepath = os.path.join(args.outputs_dir, 'embeddings_test.csv')
    model_embeddings = read_csv_file(embeddings_csv_filepath)
    df = pd.read_csv(TEST_RECORDS_CSV)

    # Get embeddings size
    num_features = get_num_features(model_embeddings)

    # Get embeddings columns
    embed_cols_names = [f'embed_{i}' for i in range(1, num_features+1)]
    embeds = model_embeddings[embed_cols_names].to_numpy()
    n, m = embeds.shape
    print(f"Embeddings shape: {embeds.shape}")


    # Directories to save bias analysis outputs
    bias_dir_path = os.path.join(args.outputs_dir, 'bias_analysis')
    bias_stats_dir_path = os.path.join(bias_dir_path, 'bias_stats/')
    tsne_dir_path = os.path.join(bias_dir_path, 'tsne/')
    tsne_plots_joint_dir_path = os.path.join(tsne_dir_path, 'tsne_plots_joint/')
    tsne_plots_marginal_dir_path = os.path.join(tsne_dir_path, 'tsne_plots_marginal/')
    pca_dir_path = os.path.join(bias_dir_path, 'pca/')
    pca_plots_joint_dir_path = os.path.join(pca_dir_path, 'pca_plots_joint/')
    pca_plots_marginal_dir_path = os.path.join(pca_dir_path, 'pca_plots_marginal/')
    combined_plots_dir_path = os.path.join(bias_dir_path, 'combined_plots/')
    combined_joint_plots_dir_path = os.path.join(combined_plots_dir_path, 'combined_joint_plots/')
    combined_marginal_plots_dir_path = os.path.join(combined_plots_dir_path, 'combined_marginal_plots/')
    os.makedirs(bias_dir_path, exist_ok=True)
    os.makedirs(bias_stats_dir_path, exist_ok=True)
    os.makedirs(tsne_dir_path, exist_ok=True)
    os.makedirs(tsne_plots_joint_dir_path, exist_ok=True)
    os.makedirs(tsne_plots_marginal_dir_path, exist_ok=True)
    os.makedirs(pca_dir_path, exist_ok=True)
    os.makedirs(pca_plots_joint_dir_path, exist_ok=True)
    os.makedirs(pca_plots_marginal_dir_path, exist_ok=True)
    os.makedirs(combined_plots_dir_path, exist_ok=True)
    os.makedirs(combined_joint_plots_dir_path, exist_ok=True)
    os.makedirs(combined_marginal_plots_dir_path, exist_ok=True)


    # Get PCA embeddings
    embeds_pca, exp_var = apply_pca(embeds=embeds, df=df, pca_dir_path=pca_dir_path)
    # Get TSNE embeddings from the PCA-reduced embeddings
    embeds_tsne = apply_tsne(embeds_pca=embeds_pca, df=df, tsne_dir_path=tsne_dir_path)

    # Create the sample to be used for analysis
    sample_test = sample_by_race(df=df, n_samples=N_SAMPLES, output_dir=bias_dir_path, races=RACES)
    sample_test = sample_test.sample(frac=1) # shuffle data for proper visualisation due to overlappping following z order of data points
    # Replicate entries for having capital letters in plots
    sample_test['Disease'] = sample_test['disease']
    sample_test['Sex'] = sample_test['sex']
    sample_test['Age'] = sample_test['binned_age']
    sample_test['Race'] = sample_test['race']



    # ================================================
    # ==== BIAS ANALYSIS - GENERATE PLOTS & STATS ====
    # ================================================

    # Define labels to guide the plotting
    labels_dict = {
        'Disease': {'hue_order': args.labels},
        'Sex': {'hue_order': [sex for sex in SEXES]},
        'Race': {'hue_order': [race for race in RACES]},
        'Age': {'hue_order': list(AGE_BINS.keys())}
    }

    ## Individual Plots
    # PCA Modes 1-2
    method = 'PCA-1+2' 
    mode_indices = [1, 2]
    xdat = 'PCA Mode 1'
    ydat = 'PCA Mode 2'
    plot_feature_modes(df=sample_test, method=method, mode_indices=mode_indices, xdat=xdat, ydat=ydat, labels_dict=labels_dict, 
                   plots_joint_dir_path=pca_plots_joint_dir_path, plots_marginal_dir_path=pca_plots_marginal_dir_path, 
                   out_format=OUT_FORMAT, out_dpi=OUT_DPI, color_palette1=COLOR_PALETTE1, color_palette2=COLOR_PALETTE2, 
                   font_scale=FONT_SCALE, alpha=ALPHA, marker=MARKER, markersize=MARKERSIZE, kind=KIND, rasterized=RASTERIZED_SCATTER)

    # PCA Modes 3-4
    method = 'PCA-3+4'
    mode_indices = [3, 4]
    xdat = 'PCA Mode 3'
    ydat = 'PCA Mode 4'
    plot_feature_modes(df=sample_test, method=method, mode_indices=mode_indices, xdat=xdat, ydat=ydat, labels_dict=labels_dict, 
                   plots_joint_dir_path=pca_plots_joint_dir_path, plots_marginal_dir_path=pca_plots_marginal_dir_path, 
                   out_format=OUT_FORMAT, out_dpi=OUT_DPI, color_palette1=COLOR_PALETTE1, color_palette2=COLOR_PALETTE2, 
                   font_scale=FONT_SCALE, alpha=ALPHA, marker=MARKER, markersize=MARKERSIZE, kind=KIND, rasterized=RASTERIZED_SCATTER)
    
    # t-SNE
    method = 'tSNE'
    mode_indices = [1, 2]
    xdat = 't-SNE Dimension 1'
    ydat = 't-SNE Dimension 2'
    plot_feature_modes(df=sample_test, method=method, mode_indices=mode_indices, xdat=xdat, ydat=ydat, labels_dict=labels_dict, 
                   plots_joint_dir_path=tsne_plots_joint_dir_path, plots_marginal_dir_path=tsne_plots_marginal_dir_path, 
                   out_format=OUT_FORMAT, out_dpi=OUT_DPI, color_palette1=COLOR_PALETTE1, color_palette2=COLOR_PALETTE2, 
                   font_scale=FONT_SCALE, alpha=ALPHA, marker=MARKER, markersize=MARKERSIZE, kind=KIND, rasterized=RASTERIZED_SCATTER)


    ## Combined Plots
    # Combine joint PCA and t-SNE plots together
    

    # Combine marginal PCA and t-SNE plots together
    
        
    ## Stats
    # Perform Two-sample Kolmogorov–Smirnov tests between each pair of subgroups
    # the function is currently defined to only perform stat. testing on 2 diseases
    diseases = ['Pleural Effusion', 'No Finding']
    perform_statistical_tests(df=sample_test, bias_stats_dir_path=bias_stats_dir_path, 
                              races=RACES, sexes=SEXES, diseases=diseases, exp_var=exp_var)




