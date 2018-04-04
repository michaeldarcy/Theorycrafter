import pandas as pd
import tensorflow as tf
import math, secrets
import json, ast
import numpy
import parseKillmails as parse
import os
from operator import add
from keras.models import Sequential, Model, model_from_json
from keras.layers import Embedding
from keras.layers import Dense, Input
from keras.layers import LSTM, concatenate
from keras import metrics, utils
from keras import backend as K

def generate_batches(killmail_folder, ship_ID_properties):
     
    for subdir, dirs, files in os.walk(killmail_folder):
        for file in files:
            #print os.path.join(subdir, file)
            filepath = subdir + os.sep + file

            if filepath.endswith(".json"):
                print (filepath)
                killmails = parse.parse_Killmails(filepath, ship_ID_properties)
                if (len(killmails["AllSlots"]) == 0):
                       """print(killmails["AllSlots"])"""
                       continue
                training_set = parse.input_evaluation_set (killmails, ship_ID_properties)
                training_set[2] = ModulesToOneHootMultilabel(training_set[2], ship_ID_properties)
                yield ({'ship_input': training_set[0], 'modules_input' : training_set[1]}, {'aux_output': training_set[2], 'main_output': training_set[2]})
            else:
                continue

def ModulesToOneHotMultilabel (module_set , ship_ID_properties):
    multilabel_list = []
    for col in module_set:
        new_label_set = []
        multilabel = numpy.zeros(len(ship_ID_properties["EquipmentIDs"]))
        for item in col:
            new_label_set.append(ship_ID_properties["EquipmentIDs"].index(item))
        new_label_set = utils.to_categorical(new_label_set, len(ship_ID_properties["EquipmentIDs"]))
        print(new_label_set)
        #merge one-hots to make a multi-label
        for onehot in new_label_set:
            multilabel = [multilabel[index] or onehot[index] for index in range(len(multilabel))]

            #multiple copies of the same module shouldn't change acceptable answers
            for index in range(len(multilabel)):
                if multilabel[index] > 1:
                    print (multilabel)
                    multilabel[index] = 1
                    
        multilabel_list.append(multilabel)                                
    return multilabel_list

def promiscuous_categorical_crossentropy(y_true, y_pred):
    y_true_component = tf.zeros([len(ship_ID_properties["EquipmentIDs"])])
    min_component_loss = float('Inf')
    y_true = tf.unstack(y_true)
    for index in range(len(y_true)):
        if y_true[index]:
            y_true_component[index] = 1
            component_loss =  K.categorical_crossentropy(y_true_component, y_pred)                 
            if component_loss < min_component_loss:
                min_component_loss = component_loss
                             
            y_true_component[index] = 0                 
    return min_component_loss
        
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

def main():
    global ship_ID_properties
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

    model.compile(loss=promiscuous_categorical_crossentropy , optimizer='adam', metrics=['accuracy', metrics.sparse_categorical_accuracy], loss_weights=[1., 0.2]);
    history = model.fit_generator(gen, steps_per_epoch=2, epochs=5000,verbose=2)
