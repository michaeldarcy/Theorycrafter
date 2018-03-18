import pandas as pd
import tensorflow as tf
import math, secrets
import json, ast
import numpy
import parseKillmails as parse
import os

from keras.models import Sequential, Model, model_from_json
from keras.layers import Embedding
from keras.layers import Dense, Input
from keras.layers import LSTM, concatenate
from keras import metrics

def generate_batches(killmail_folder, ship_ID_properties):
     
    for subdir, dirs, files in os.walk(killmail_folder):
        for file in files:
            #print os.path.join(subdir, file)
            filepath = subdir + os.sep + file

            if filepath.endswith(".json"):
                print (filepath)
                killmails = parse.parse_Killmails(filepath, ship_ID_properties)
                training_set = parse.input_evaluation_set (killmails, ship_ID_properties)
                yield ({'ship_input': training_set[0], 'modules_input' : training_set[1]}, {'aux_output': training_set[2], 'main_output': training_set[2]})
            else:
                continue

def save_model (model):
    # serialize model to JSON
    model_json = model.to_json()
    with open("model.json", "w") as json_file:
        json_file.write(model_json)
    # serialize weights to HDF5
    model.save_weights("model.h5")
    print("Saved model to disk")
 
# later...
def load_model():
# load json and create model
    json_file = open('model.json', 'r')
    loaded_model_json = json_file.read()
    json_file.close()
    loaded_model = model_from_json(loaded_model_json)
    # load weights into new model
    loaded_model.load_weights("model.h5")
    print("Loaded model from disk")
    return loaded_model


ship_ID_properties = parse.get_ship_ID_Properties ()

ship_input = Input(shape=(3,), dtype='int32', name='ship_input')
ship_embedding = Embedding(output_dim=50, input_dim=40000, input_length=3)(ship_input)
lstm_ships = LSTM(16)(ship_embedding)
auxiliary_output = Dense(len(ship_ID_properties["EquipmentIDs"]), activation='softmax', name='aux_output')(lstm_ships)

modules_input = Input(shape=(ship_ID_properties["TotalSlotsMax"],), name='modules_input')
module_embedding= Embedding(len(ship_ID_properties["EquipmentIDs"]), 100, input_length=ship_ID_properties["TotalSlotsMax"])(modules_input)
lstm_mods = LSTM(32)(module_embedding)
combined_inputs = concatenate([lstm_ships, lstm_mods])
                      
x = Dense(64, activation='relu')(combined_inputs)
x = Dense(64, activation='relu')(x)

# And finally we add the main logistic regression layer
main_output = Dense(len(ship_ID_properties["EquipmentIDs"]), activation='relu', name='main_output')(x)
model = Model(inputs=[modules_input, ship_input], outputs=[main_output, auxiliary_output])                      
print(model.summary())

gen = generate_batches(r"E:\project\killmails\batches", ship_ID_properties )

model.compile(loss='sparse_categorical_crossentropy', optimizer='adam', metrics=['accuracy', metrics.sparse_top_k_categorical_accuracy], loss_weights=[1., 0.2])
history = model.fit_generator(gen, steps_per_epoch=2, epochs=5000,verbose=2)
