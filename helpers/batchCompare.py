import pandas as pd
import numpy as np
import scipy.stats
import matplotlib.pyplot as plt

batch = pd.read_csv("Batch.csv")
human = pd.read_csv("Human.csv")

column_names = ["Total_Utts", "MLU_Utts", "MLU_Words", "MLU_Morphemes",
                "FREQ_types", "FREQ_tokens", "FREQ_TTR", "Words_Min",
                "Verbs_Utt", "%_Word_Errors", "Utt_Errors", "%_Nouns",
                "%_Plurals", "%_Verbs", "%_Aux", "%_3S", "%_PAST",
                "%_PASTP", "%_PRESP", "%_prep", "%_adj", "%_adv", "%_conj",
                "%_det", "%_pro", "noun_verb", "open_closed", "#open-class",
                "#closed-class", "retracing", "repetition"]

# Clean whitespace from the File column
batch["File"] = batch["File"].str.strip()
human["File"] = human["File"].str.strip()

# Dropping duplicates based on the File column, keeping only the first occurrence
# Assumes which is kept doesn't matter
# Due to the low amount of duplicates over such a large sample size this may not be an issue
dup_files = batch["File"][batch["File"].duplicated()]
print("Duplicate Files in Batch Dataset:", len(dup_files))


batch_1 = batch.drop_duplicates(subset=["File"], keep="first")
human_1 = human.drop_duplicates(subset=["File"], keep="first")

# Common_files is a set of file names that are common between the two datasets
# Removes duplicates and only holds files that are in both datasets
common_files = set(batch_1["File"]) & set(human_1["File"])

print("Maximum X and Y amount:", len(common_files))

batch_common = batch_1[batch_1["File"].isin(common_files)]
human_common = human_1[human_1["File"].isin(common_files)]

# Explicit sorting to ensure that both dataframes are in the same order before use. 
# ChatGPT recommended .reset_index but idk exactly why yet
batch_common = (
    batch_common
    .sort_values("File")
    .reset_index(drop=True)
)

human_common = (
    human_common
    .sort_values("File")
    .reset_index(drop=True)
)

# Checks to make sure that file names do match up
print("Do Files line up?", (batch_common["File"].values == human_common["File"].values).all())

# Following loop assumes that the rows for each sheet match up with each other
# This honestly may not be true but is reasonable to assume with my use of sets and sorting
pearson = {}
spearman = {}
for column in column_names:
    print("\nAnalyzing Column:", column)
    plt.figure()
    x = batch_common[column].to_numpy()
    y = human_common[column].to_numpy()

    # Remove NaN values from both x and y, a NaN value in one removes that index for both
    mask = np.isfinite(x) & np.isfinite(y)
    x_cords = x[mask]
    y_cords = y[mask]

    print("X Cord Num:", len(x_cords))
    print("Y Cord Num:", len(y_cords))

    # Produce a Pearson correlation coefficient
    
    corr_matrix = np.corrcoef(x_cords, y_cords)
    r = corr_matrix[0, 1]
    pearson[column] = r

    # Produce Spearman correlation (prevents outliers from making as much change)
    rho = scipy.stats.spearmanr(x_cords, y_cords)
    spearman[column] = rho.correlation


    # Determine the min and max values for setting plot limits 
    min_val = min(min(x_cords), min(y_cords))
    max_val = max(max(x_cords), max(y_cords))

    # Scatter plot
    plt.scatter(x_cords, y_cords)
    plt.xlabel("Batch")
    plt.ylabel("Human")
    plt.title(column)

    plt.plot(
        [min_val, max_val],
        [min_val, max_val],
        linestyle="--",
        linewidth=1,
        color="red"
    )

    plt.xlim(min_val, max_val)
    plt.ylim(min_val, max_val)
    plt.savefig(f'graphs/{column}.png')

# Print all correlations in one list to share with team
print("\nCorrelations:")
for x in pearson:
    print(f'{x}: r = {format(pearson[x], ".4f")}, rho = {format(spearman[x], ".4f")}')
    
plt.show()
