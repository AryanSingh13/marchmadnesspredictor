# Import packages

import numpy as np
import pandas as pd
import tensorflow as tf
from sklearn.preprocessing import StandardScaler
import pickle
from datetime import datetime as dt

start = dt.now()
folder = "datasets\\march madness\\"

results = pd.read_csv(folder + "RegularSeasonDetailedResults.csv") # Lists every match in each regular season with detailed information

# Convert season and team id integers to string in Season: Team_ID format

def identify(season, team):
    return str(season) + ": " + str(team)

# Gathers all seasons and teams in results and filter to leave only the unique

seasons_teams = []
for row in results.iterrows():
    row = row[1]
    seasons_teams.append(identify(row["Season"], row["Wteam"]))
    seasons_teams.append(identify(row["Season"], row["Lteam"]))
seasons_teams = np.unique(seasons_teams)

# Organizes the data from results into season_teams and calculates total wins, losses, and games

wteam_cols = ['Wscore', 'Wfgm', 'Wfga', 'Wfgm3', 'Wfga3', 'Wftm', 'Wfta', 'Wor', 'Wdr', 'Wast', 'Wto', 'Wstl', 'Wblk', 'Wpf']
lteam_cols = ['Lscore', 'Lfgm', 'Lfga', 'Lfgm3', 'Lfga3', 'Lftm', 'Lfta', 'Lor', 'Ldr', 'Last', 'Lto', 'Lstl', 'Lblk', 'Lpf']
other_cols = ['Wins', 'Losses', 'Games']
all_cols = wteam_cols + lteam_cols + other_cols

teams = pd.DataFrame(data = np.zeros((len(seasons_teams), len(wteam_cols) + len(lteam_cols) + len(other_cols))), index = seasons_teams, columns = all_cols)

for index in results.index:
    
    w = results.at[index, "Wteam"]
    l = results.at[index, "Lteam"]
    s = results.at[index, "Season"]
    
    w_id = identify(s, w)
    l_id = identify(s, l)
    
    teams.at[w_id, "Wins"] += 1
    teams.at[w_id, "Games"] += 1
    teams.at[l_id, "Losses"] += 1
    teams.at[l_id, "Games"] += 1
    
    for col in wteam_cols:
        teams.at[w_id, col] += results.at[index, col]
    for col in lteam_cols:
        teams.at[l_id, col] += results.at[index, col]

# Averages every value per game, except for Games        
        
for row in teams.index:
    g = teams.at[row, "Games"]
    w = teams.at[row, "Wins"]
    l = teams.at[row, "Losses"]
    if w != 0:
        for col in wteam_cols:
            teams.at[row, col] /= w
    if l != 0:
        for col in lteam_cols:
            teams.at[row, col] /= l
    for col in other_cols:
        if col != "Games":
            teams.at[row, col] /= g


end = dt.now()

print(str(end - start))
print(teams.head())
print(teams.isnull().values.any()) # Check if calculations failed, output should be False

teams.to_csv(path_or_buf = folder + "SeasonTeams.csv") # Saves season_teams data

# Combines results and seasons_teams data to show list two teams competing for each match and the score

# Generate columns needed for match data
team1_cols = []
team2_cols = []
for col in all_cols:
    team1_cols.append(col + "1")
    team2_cols.append(col + "2")
match_cols = team1_cols + team2_cols + ["Home", "Away", "Neutral", "Winner"]

start = dt.now()
results = pd.read_csv(folder + "RegularSeasonDetailedResults.csv") # Lists every match in each regular season with detailed information
def identify(season, team):
    return str(season) + ": " + str(team)
teams = pd.read_csv(folder + "SeasonTeams.csv", index_col = 0)
# Recreate each match in results with average team data
matches = pd.DataFrame(index = results.index, columns = match_cols)
for index in matches.index:
    
    # Get winner and loser and season
    w = results.at[index, "Wteam"]
    l = results.at[index, "Lteam"]
    s = results.at[index, "Season"]
    
    # Determine team order
    id1 = min(w, l)
    id2 = max(w, l)
    if id1 == w:
        o1 = 'W'
        o2 = 'L'
    else:
        o1 = 'L'
        o2 = 'W'
    id1 = identify(s, id1)
    id2 = identify(s, id2)
    
    ids = [id1, id2]
    
    # Place necessary statistics for each team
    for i, j in enumerate(ids):
        for col in all_cols:
            matches.at[index, col + str(i + 1)] = teams.at[j, col]
        
    matches.at[index, "Winner"] = 0 if o1 == 'W' else 1
    
    # Create one-hot array to categorize the location
    loc = results.at[index, "Wloc"]
    locs = [0, 0, 0]
    if loc == 'H':
        locs[0] = 1
    elif loc == 'A':
        locs[1] = 1
    else:
        locs[2] = 1
        
    # Fixes the loc to be in relation to team1    
    if o1 == 'L' and locs[2] != 1:
        locs[0] = (locs[0] + 1) % 2
        locs[1] = (locs[1] + 1) % 2
        
    matches.at[index, "Home"] = locs[0]
    matches.at[index, "Away"] = locs[1]
    matches.at[index, "Neutral"] = locs[2]

end = dt.now()
print(str(end - start))
matches.head()

matches.to_csv(path_or_buf = folder + "Matches.csv")
folder = "datasets\\march madness\\"
matches = pd.read_csv(folder + "Matches.csv", index_col = 0)

# Split match data into test and train sets to a 20:80 ratio
ratio = 0.2
rand_ints = np.random.permutation(len(matches))
test_size = int(ratio * len(matches))
test_indices = rand_ints[:test_size]
train_indices = rand_ints[test_size:]

matches_test = matches.iloc[test_indices]
matches_train = matches.iloc[train_indices]

# Pops the label columns and scales input features
def prepare_data(matches):
    scaler = StandardScaler()
    y = matches.pop("Winner")
    numerical_features = matches.iloc[:, :62]
    numerical_features = scaler.fit_transform(numerical_features)
    mean = scaler.mean_
    var = scaler.var_
    X = np.concatenate((numerical_features, matches.iloc[:, 62:65].values), axis = 1)
    return y.values.astype(np.uint8), X.astype(np.float32), mean, var
	
y_train, X_train, mean_train, var_train = prepare_data(matches_train)
y_test, X_test, mean_test, var_test = prepare_data(matches_test)

# Deep Neural Network

# Number of neurons per layer
n_inputs = 65
n_hidden1 = 50
n_hidden2 = 25
n_outputs = 2
    
tf.reset_default_graph()

# Create neuron layers
X = tf.placeholder(tf.float32, shape=(None, n_inputs), name="X")
y = tf.placeholder(tf.int32, shape=(None), name="y")

hidden1 = tf.layers.dense(X, n_hidden1, name="hidden1",
                          activation=tf.nn.relu)
hidden2 = tf.layers.dense(hidden1, n_hidden2, name="hidden2",
                          activation=tf.nn.relu)
logits = tf.layers.dense(hidden2, n_outputs, name="outputs")
y_proba = tf.nn.softmax(logits)

# Create loss metric
xentropy = tf.nn.sparse_softmax_cross_entropy_with_logits(labels=y, logits=logits)
loss = tf.reduce_mean(xentropy, name="loss")

learning_rate = 0.01

# Adjust neurons to account for loss metric
optimizer = tf.train.GradientDescentOptimizer(learning_rate)
training_op = optimizer.minimize(loss)

correct = tf.nn.in_top_k(logits, y, 1)
accuracy = tf.reduce_mean(tf.cast(correct, tf.float32))

init = tf.global_variables_initializer()
saver = tf.train.Saver()

# Input function
n_epochs = 20
batch_size = 50

def shuffle_batch(X, y, batch_size):
    rnd_idx = np.random.permutation(len(X))
    n_batches = len(X) // batch_size
    for batch_idx in np.array_split(rnd_idx, n_batches):
        X_batch, y_batch = X[batch_idx], y[batch_idx]
        yield X_batch, y_batch

# Run training
with tf.Session() as sess:
    sess.run(init)
    for epoch in range(n_epochs):
        for X_batch, y_batch in shuffle_batch(X_train, y_train, batch_size):
            sess.run(training_op, feed_dict={X: X_batch, y: y_batch})
            
        acc_batch = accuracy.eval(feed_dict={X: X_batch, y: y_batch})
        acc_test = accuracy.eval(feed_dict={X: X_test, y: y_test})
        print(epoch, "Batch accuracy:", acc_batch, "Test accuracy:", acc_test)
    
    
    # Converts model to tflite for mobile use
    converter = tf.lite.TFLiteConverter.from_session(sess, [X], [y_proba])
    tflite_model = converter.convert()
    open("converted_model.tflite", "wb").write(tflite_model)

    save_path = saver.save(sess, "./my_model_final.ckpt")
