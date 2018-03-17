import pandas as pd
import tensorflow as tf
import math, secrets
import json, ast
import numpy
import parseKillmails as parse

from keras.models import Sequential
from keras.layers import Embedding
from keras.layers import Dense
from keras.layers import LSTM




ship_ID_properties = parse.get_ship_ID_Properties ()    
killmails = parse.parse_Killmails (r"E:\project\killmails\batches\d0034\k020.json", ship_ID_properties)
training_set = parse.input_evaluation_set(killmails, ship_ID_properties)

ship_input = Input(shape=(3,), dtype='int32', name='ship_input')
ship_embedding = Embedding(output_dim=200, input_dim=2000000, input_length=100)(ship_input)
lstm_ships = LSTM(32)(ship_embedding)
auxiliary_output = Dense(1, activation='sigmoid', name='aux_output')(lstm_ships)

modules_input = Input(shape=(len(ship_ID_properties["EquipmentIDs"]),), name='mod_input')
module_embedding= Embedding(len(ship_ID_properties["EquipmentIDs"]), 100, input_length=ship_ID_properties["TotalSlotsMax"])
combined_inputs = kears.layers.concatenate([lstm_ships, module_embedding])
                      
x = Dense(64, activation='relu')(combined_inputs)
x = Dense(64, activation='relu')(x)
x = Dense(64, activation='relu')(x)

# And finally we add the main logistic regression layer
main_output = Dense(1, activation='softmax', name='main_output')(x)
                      
print(model.summary())

model.compile(loss='sparse_categorical_crossentropy', optimizer='adam', metrics=['accuracy'], loss_weights=[1., 0.2])
model.fit({'ship_input': training_set[0], 'mod_input' : training_set[1],
           'aux_output': training_set[2], 'main_output': training_set[2]}, epochs=500, verbose=2)
